# SPEC — Technical Design & Implementation

This document translates the PRD into an implementable plan: services, data, algorithms, APIs, deployment, and testing.

---

## 1) Architecture

### Services
- **Ingestor** (Python): Reddit stream → queue (`comments.events`).
- **NLP/Parser** (Python): ticker extraction, stance, options intent → `mention_events`.
- **Price Harvester** (Python/Go): minute bars; Redis cache for hot symbols.
- **Trend Engine** (Python): 1‑min aggregations; Z/EARS/CUSUM; emits `alerts`.
- **API Gateway** (FastAPI): REST + SSE/WebSocket; auth; rate limiting.
- **Web App** (Next.js): dashboards; alert subscriptions.
- **Backtester** (Python): offline replays; cohort stats.
- **Orchestrator** (Airflow/Cron): baselines, compaction, backfills.

### Data Stores
- **Primary TSDB:** TimescaleDB (hypertables) or ClickHouse.
- **Cache:** Redis.
- **Queue:** Kafka/Redpanda or Redis Streams.
- **Object Store:** artifacts/backtests/exports.

### Data Flow
1. Ingestor pulls comments/posts → queue.  
2. NLP extracts (ticker, stance) → `mention_events`.  
3. Price Harvester stamps minute bars; Trend Engine aggregates per minute.  
4. Detectors run → `alerts`.  
5. API serves trending/alerts/impact; Web subscribes to SSE.  

---

## 2) Data Model (DDL Sketches)

> Use TimescaleDB hypertables for time‑series. Adjust types to your provider’s decimal/float policy.

```sql
-- 2.1 Ticker Master
CREATE TABLE ticker_master(
  symbol TEXT PRIMARY KEY,
  exchange TEXT NOT NULL,
  name TEXT,
  is_active BOOLEAN DEFAULT TRUE
);

-- 2.2 Raw Reddit Items
CREATE TABLE reddit_items(
  id TEXT PRIMARY KEY,               -- comment or post id
  kind TEXT CHECK (kind IN ('comment','post')),
  parent_id TEXT,
  link_id TEXT,
  author TEXT,
  body TEXT,
  created_utc TIMESTAMPTZ NOT NULL,
  score INT,
  permalink TEXT
);
SELECT create_hypertable('reddit_items', 'created_utc', if_not_exists=>TRUE);

-- 2.3 Mention Events (one row per (comment, ticker))
CREATE TABLE mention_events(
  id BIGSERIAL PRIMARY KEY,
  ts_utc TIMESTAMPTZ NOT NULL,
  subreddit TEXT NOT NULL,
  reddit_id TEXT NOT NULL REFERENCES reddit_items(id),
  author TEXT NOT NULL,
  ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
  confidence REAL NOT NULL,
  upvotes INT,
  sentiment_label SMALLINT,          -- -1 bear, 0 neu, +1 bull
  sentiment_score REAL,              -- [-1,1]
  sentiment_conf REAL,
  has_options_intent BOOLEAN,
  option_side SMALLINT,              -- -1 put, +1 call
  UNIQUE (reddit_id, ticker)
);
SELECT create_hypertable('mention_events', 'ts_utc', if_not_exists=>TRUE);

-- 2.4 Minute Bars
CREATE TABLE minute_bars(
  ts_utc TIMESTAMPTZ NOT NULL,
  ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
  open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume BIGINT,
  PRIMARY KEY (ticker, ts_utc)
);
SELECT create_hypertable('minute_bars', 'ts_utc', if_not_exists=>TRUE);

-- 2.5 Per-Ticker 1m Aggregations
CREATE TABLE mentions_1m(
  ts_utc TIMESTAMPTZ NOT NULL,
  ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
  mentions INT NOT NULL,
  unique_authors INT NOT NULL,
  threads_touched INT NOT NULL,
  avg_sentiment REAL,
  zscore REAL,
  ears_flag BOOLEAN,
  cusum_stat REAL,
  PRIMARY KEY (ticker, ts_utc)
);
SELECT create_hypertable('mentions_1m', 'ts_utc', if_not_exists=>TRUE);

-- 2.6 Alerts Tape
CREATE TABLE alerts(
  id BIGSERIAL PRIMARY KEY,
  ts_alert TIMESTAMPTZ NOT NULL,
  ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
  tier TEXT NOT NULL,                -- 'heads-up' | 'actionable'
  hype_score REAL NOT NULL,
  zscore REAL NOT NULL,
  unique_authors INT NOT NULL,
  threads_touched INT NOT NULL,
  avg_sentiment REAL,
  price_at_alert NUMERIC,
  meta JSONB                         -- {ears:bool, cusum:float, baseline:{mu,sd}, refs:[...]}
);
CREATE INDEX ON alerts (ts_alert DESC);
```

**Continuous Aggregates (examples)**

```sql
CREATE MATERIALIZED VIEW ca_mentions_10m
WITH (timescaledb.continuous) AS
SELECT ticker,
       time_bucket('10 minutes', ts_utc) AS ts_10m,
       COUNT(*) AS m10,
       COUNT(DISTINCT author) AS a10,
       AVG(sentiment_score) AS s10
FROM mention_events
GROUP BY ticker, ts_10m;

CREATE MATERIALIZED VIEW ca_returns_daily
WITH (timescaledb.continuous) AS
SELECT ticker,
       time_bucket('1 day', ts_utc) AS d,
       first(close, ts_utc) AS open_d,
       last(close, ts_utc) AS close_d
FROM minute_bars
GROUP BY ticker, d;
```

---

## 3) Algorithms

### 3.1 Ticker Extraction
- Universe: listed equities/ETFs; refresh daily.
- Rules:
  - `$TICKER` → accept.
  - ALL‑CAPS 1–5 chars in universe → candidate; if in **stoplist** (A, IT, ON, ALL, FOR, GO, ARE, BE, etc.), require finance‑term context within ±3 tokens (e.g., “calls”, “puts”, “PT”, “earnings”, “float”, “short”).
  - Company alias pass (“Palantir” → PLTR).
- One credit per (comment, ticker).

### 3.2 Sentiment / Stance
- Per detected ticker, extract span ±8–12 tokens.
- Run **FinBERT** → `s_fin ∈ [-1,1]` and optionally **VADER** → `s_vad ∈ [-1,1]`.
- Blend: `s = clip(0.6*s_fin + 0.4*s_vad, -0.9, +0.9)`.
- Options tilt: +0.1 for call/long phrasing, −0.1 for put/short (clamped).
- Label thresholds: bull if `s ≥ +0.15`, bear if `s ≤ −0.15`, else neutral.
- Store `sentiment_score`, `sentiment_label`, `sentiment_conf`.

### 3.3 Aggregations
- Tumbling 1‑minute windows per ticker: `mentions`, `unique_authors`, `threads_touched`, `avg_sentiment`.
- Baselines:
  - **Short** μ,σ over last 2–6 hours.
  - **Diurnal** μ,σ per minute‑of‑day over last 7 days.

### 3.4 Detectors
- Z‑score: `z = (m_now − μ_short) / max(σ_short, σ_floor)`.
- **EARS C2/C3** on recent windows (guard band 2–3).
- **CUSUM** (positive shift):
  - `S⁺ = max(0, S⁺ + m_now − (μ_diurnal + k))`; alarm if `S⁺ > h`.
- **Guards:** `unique_authors ≥ 3` and `threads_touched ≥ 2`.

### 3.5 Hype Score & Alerting
- Sentiment multiplier: `sent_mult = 1 + clamp(avg_sentiment, -0.25, +0.25)`.
- `hype = z * log1p(unique_authors) * sent_mult`.
- **Heads‑up** if `z ≥ 2.0` and guards; **Actionable** if `z ≥ 3.0` and (EARS or CUSUM alarm) and guards.
- Suppress actionable if `|ΔP_10m| ≥ 3%` without corresponding mention ramp (late‑to‑news filter).

### 3.6 Price & Impact
- Align event time `ts_utc` to minute bars.
- Store:
  - `price_at_mention` per mention (derived at parse time or join later),
  - `price_at_alert` per alert,
  - Forward returns at +15m, +1h, EOD, +1d.
- Compute abnormal returns vs SPY (CAR) with simple market model (β estimated from 60d).

---

## 4) Public APIs (FastAPI)

### 4.1 Trending
```
GET /v1/trending?window=5m&min_mentions=3&limit=50
200 [
  {
    "ticker":"PLTR",
    "mentions":42,
    "unique_authors":27,
    "zscore":3.6,
    "avg_sentiment":0.22,
    "hype_score":7.8,
    "sparkline":[...],
    "first_seen":"2025-11-10T14:03:00Z"
  }
]
```

### 4.2 Live Alerts (SSE)
```
GET /v1/alerts/live
event: alert
data: {
  "ts":"2025-11-10T14:05:00Z",
  "ticker":"BYND",
  "tier":"actionable",
  "hype_score":6.3,
  "zscore":3.1,
  "unique_authors":5,
  "threads_touched":3,
  "avg_sentiment":0.31,
  "price_at_alert":9.42,
  "meta":{"ears":true,"cusum":5.8}
}
```

### 4.3 Ticker Mentions
```
GET /v1/tickers/{sym}/mentions?granularity=1m&start=...&end=...
200 {
  "series":[{"ts":"...","mentions":...,"unique_authors":...,"avg_sentiment":...,"zscore":...}]
}
```

### 4.4 Impact
```
GET /v1/tickers/{sym}/impact?window=7d&only_spikes=true
200 {"samples":187,"avg":{"+15m":0.004,"+1h":0.012,"+1d":0.021},"car":{"+1h":0.009}}
```

### 4.5 Leaderboards
```
GET /v1/posters/leaderboard?metric=alpha_1d&min_calls=10&window=30d
200 [{"author":"u/foo","n":24,"alpha_1d_med":0.018,"win_rate":0.63}]
```

**Auth & Limits**  
- API keys per partner; rate limits (e.g., 60 rpm default).  
- Caching: Redis for `/trending` & `/ticker/*` windows.

---

## 5) Frontend (Next.js)

- **Pages:** `/now`, `/ticker/[sym]`, `/alerts`, `/leaders`, `/backtest`.
- **Components:** Heatboard grid, Sparkline, Sentiment donut, Burst bands overlay, Alert card with provenance links.
- **Data:** SWR/React Query for cached endpoints; WebSocket/SSE for `/alerts/live`.
- **Accessibility:** keyboard nav, reduced motion, color‑blind friendly palettes.

---

## 6) Performance & SLOs

- Ingest→mention_event p95 < 15s  
- mention_event→alert p95 < 45s  
- API cached p95 < 300ms; uncached p95 < 800ms  
- Data loss < 0.1%/day with retries & DLQ

---

## 7) Observability

- **Metrics:** ingest lag, parse error rate, extractor precision (sampled QA), alert rate by tier, alert precision/cohorts, API latency.
- **Tracing:** propagate `trace_id` across services; correlate by `reddit_id`.
- **Logging:** structured JSON; no PII; sampling for verbose paths.

---

## 8) Security & Compliance

- Store only necessary public metadata; purge on deletion if detected.
- Secrets in Vault/KMS; per‑service tokens; RBAC on API.
- Respect Reddit rate limits; backoff 429s; exponential retry policies.
- Market data: display delayed feeds publicly unless licensed for real‑time.
- “Not Investment Advice” banner and Terms link in UI.

---

## 9) Testing

- **Unit:** extractor (positive/negative cases), sentiment spans, detector math.
- **Property:** stoplist/regex fuzz; detector monotonicity.
- **Integration:** ingest→parse→alert E2E over recorded fixtures.
- **Load:** 10× typical event rate; ensure alert lag budget not exceeded.
- **Backtests:** deterministic replays with seeds; generate cohort metrics & plots.

---

## 10) Deployment

- Docker images per service; K8s + HPA; rolling deploy; blue/green for API.
- Feature flags for thresholds, sentiment on/off, delayed vs real‑time prices.
- Runbooks: ingestion lag, alert storms, provider outage fallback (delayed feed + backfill).

---

## 11) Milestones

- **M0 (2–3 wks):** Ingestion, extraction, counts, `/now`.
- **M1 (2 wks):** Sentiment service; UI surfaces.
- **M2 (2–3 wks):** Detectors + Alerts (SSE) + price at alert.
- **M3 (2 wks):** Impact analytics, leaderboards, backtests.
- **M4:** Hardening, docs, public API.

---

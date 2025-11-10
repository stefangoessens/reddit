# PRD — WSB Hype Radar

> **One‑liner:** Detect and quantify WallStreetBets (WSB) ticker hype early, correlate it with price moves, and surface actionable, explainable alerts with transparent backtests.  
> **Disclaimer:** This product surfaces community chatter and analytics. It is **not** investment advice.

---

## 1) Summary

**Problem**  
Traders and researchers struggle to catch *emerging* meme‑stock chatter early enough, and to evaluate whether mention spikes precede price moves.

**Solution**  
Continuously ingest r/wallstreetbets posts/comments; robustly extract tickers; compute stance‑aware sentiment; run low‑latency burst detection; stamp **price‑at‑mention**/**price‑at‑alert** and forward returns; expose dashboards, alerts, leaderboards, and APIs.

---

## 2) Goals & Non‑Goals

### Goals
- **Early detection:** Identify *new or accelerating* ticker mentions within minute‑level latency and emit alerts with confidence & provenance.
- **Directional signal:** Per‑ticker stance (bull/neutral/bear) per comment span; aggregate sentiment per window.
- **Impact tracking:** Store `price_at_mention`/`price_at_alert` and forward returns (+15m, +1h, EOD, +1d).
- **Dashboards & APIs:** Heatboard (“Now”), Ticker drilldown, Impact (event‑study), Poster leaderboards; public endpoints for partners.
- **Backtests:** Reproduce historical alert streams; measure precision/lead time.

### Non‑Goals (v1)
- Executing trades or portfolio management.
- Cross‑subreddit coverage beyond r/wallstreetbets.
- Real‑time redistribution of exchange‑licensed prices without entitlements (public views may show **delayed** data).

---

## 3) Users & Jobs

- **Momentum Trader:** Wants instant heads‑up when a ticker starts trending with bullish bias and a price overlay.
- **Quant/PM/Researcher:** Wants structured data to test if mention bursts predict short‑term returns and abnormal returns.
- **Desk/Analyst/Content:** Wants explainability (why a name is moving) with direct links to top source comments.
- **Partner Apps:** Want an embeddable widget/API for trending tickers and alerts.

---

## 4) Success Metrics (90‑day KPIs)

- **Lead time:** Median minutes from first alert → local max of mention rate (↑ is better).
- **Actionability:** % alerts with **positive excess return** vs SPY at +30m/+1h (by cohort).
- **Latency:** p95 ingest→alert < **60s**; API p95 < **300ms** for cached endpoints.
- **Data quality:** < **1%** false ticker positives on a holdout set; ≥ **90%** precision for cashtagged mentions.
- **Stability:** 99.9% ingestion uptime; alert drop rate < **0.1%**.

---

## 5) Feature Scope

### 5.1 Ingestion
- OAuth to Reddit; stream comments & submissions from r/wallstreetbets (focus on Daily Discussion threads).
- De‑dup across cross‑posts; capture UTC timestamps, author, upvotes, permalinks.
- Anti‑spam caps per author and per thread.

### 5.2 Ticker Extraction
- Dictionary of US equities/ETFs (NYSE/Nasdaq/Amex) + company alias map.
- Rules:
  - `$TICKER` → accept.
  - ALL‑CAPS 1–5 chars in dictionary → candidate; require finance‑term context within ±3 tokens.
  - **Stoplist** (A, IT, ON, ALL, ARE, FOR, GO, BE, etc.) unless $‑prefixed or strong finance context.
  - One credit per (comment, ticker).

### 5.3 Sentiment / Stance
- Span around each ticker (±8–12 tokens); **FinBERT** + light lexicon + options‑intent tilt (calls → bullish, puts → bearish).
- Output per (comment, ticker): `sentiment_label ∈ {bull, neu, bear}`, `sentiment_score ∈ [-1,1]`, `confidence`, `has_options_intent`, `option_side`.

### 5.4 Early Detection
- Minute buckets per ticker: `mentions`, `unique_authors`, `threads_touched`, `avg_sentiment`.
- Baselines: short (2–6h rolling) and diurnal (7‑day time‑of‑day).
- Detectors: Z‑score screen, **EARS (C2/C3)**, **CUSUM**. Diversity guard (authors ≥ 3; threads ≥ 2).
- Alert tiers: **Heads‑up** (low SNR) and **Actionable** (high SNR).

### 5.5 Price & Impact
- Minute bars; `price_at_mention` and `price_at_alert`.
- Forward returns (+15m, +1h, EOD, +1d); abnormal returns vs SPY (event‑study).
- Liquidity filters: ADV, price range, halt/spread guardrails.

### 5.6 Dashboards
- **Now / Heatboard:** Top tickers by 5m/1h mentions; hype score; EARLY badge; sentiment split.
- **Ticker detail:** Mentions & net sentiment stacked with price; top comments; shaded burst periods.
- **Impact:** Average CAR after spikes; cohort sizes, confidence intervals.
- **Leaderboards:** Posters by realized alpha, win‑rate, early‑caller score.

### 5.7 APIs
- `/v1/trending`, `/v1/alerts/live` (SSE), `/v1/tickers/{sym}/mentions`, `/v1/tickers/{sym}/impact`, `/v1/posters/leaderboard`.

### 5.8 Backtesting
- Historical re‑play; threshold sweeps; cohort stats; CSV export.

---

## 6) Requirements

### Functional
- Subscribe to alerts filtered by min distinct authors, sentiment bias, liquidity.
- Inspect alert provenance (top comments & times).
- Download mention & price‑at‑event data; query impact for ranges.

### Non‑Functional
- Near‑real‑time; scale to >1,000 1‑min updates/s across tickers.
- Idempotent ingestion; exactly‑once semantics for mentions.
- Observability: traces + metrics per stage; anomaly detection on data flow.
- Compliance: Reddit policies; market‑data licensing; **delayed** data for public pages if required.

---

## 7) Dependencies & Constraints
- Reddit API access and rate limits.
- Minute‑bar provider (e.g., Polygon/Alpaca/Tiingo or equivalent).
- Storage engine (TimescaleDB or ClickHouse), cache (Redis), message bus (Kafka/Redpanda or Redis Streams).

---

## 8) Risks & Mitigations
- **Ticker false positives:** stoplist + finance‑context check + company alias map.
- **Bots/brigading:** cap per‑author credit; require multi‑thread diversity; detect abnormal author profiles.
- **Licensing:** use delayed data publicly; gate real‑time behind auth if licensed.
- **Latency spikes:** backpressure, circuit breakers, cached ranks.

---

## 9) Rollout Plan
- **MVP (v0.1):** ingestion, extraction, counts, price‑at‑mention, basic trending.
- **v0.2:** sentiment, “Now” board.
- **v0.3:** early detection + alerts (heads‑up/actionable), price‑at‑alert.
- **v1.0:** impact analytics, leaderboards, backtests, public API.

---

## 10) Analytics & Experimentation
- Track alert precision by threshold cohorts; weekly A/B of thresholds.
- Instrument time‑to‑first‑alert per burst; alert CTR/engagement.

---

## 11) Glossary
- **Mention:** parsed (comment, ticker) after rules.
- **Hype score:** composite of z‑score × log1p(unique authors) × sentiment multiplier.
- **Actionable alert:** passes diversity guard + secondary detector (EARS/CUSUM).

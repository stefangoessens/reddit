-- Initial schema for WSB Hype Radar
-- Based on Alembic migrations: 202502111200 and 202502111245

-- Create alembic version table
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Ticker master table
CREATE TABLE IF NOT EXISTS ticker_master (
    symbol TEXT PRIMARY KEY,
    exchange TEXT NOT NULL,
    name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Reddit items table
CREATE TABLE IF NOT EXISTS reddit_items (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    parent_id TEXT,
    link_id TEXT,
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    permalink TEXT NOT NULL
);

-- Mention events table
CREATE TABLE IF NOT EXISTS mention_events (
    id BIGSERIAL PRIMARY KEY,
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    subreddit TEXT NOT NULL,
    reddit_id TEXT NOT NULL REFERENCES reddit_items(id),
    author TEXT NOT NULL,
    ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
    confidence DOUBLE PRECISION NOT NULL,
    upvotes INTEGER,
    span_text TEXT,
    sentiment_label SMALLINT,
    sentiment_score DOUBLE PRECISION,
    sentiment_conf DOUBLE PRECISION,
    has_options_intent BOOLEAN NOT NULL DEFAULT FALSE,
    option_side SMALLINT,
    price_at_mention NUMERIC(18, 6),
    CONSTRAINT uniq_reddit_ticker UNIQUE (reddit_id, ticker)
);

-- Minute bars table
CREATE TABLE IF NOT EXISTS minute_bars (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
    open NUMERIC(18, 6),
    high NUMERIC(18, 6),
    low NUMERIC(18, 6),
    close NUMERIC(18, 6),
    volume BIGINT,
    PRIMARY KEY (ticker, ts_utc)
);

-- Mentions 1-minute aggregation table
CREATE TABLE IF NOT EXISTS mentions_1m (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
    mentions INTEGER NOT NULL,
    unique_authors INTEGER NOT NULL,
    threads_touched INTEGER NOT NULL,
    avg_sentiment DOUBLE PRECISION,
    zscore DOUBLE PRECISION,
    ears_flag BOOLEAN,
    cusum_stat DOUBLE PRECISION,
    PRIMARY KEY (ticker, ts_utc)
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    ts_alert TIMESTAMP WITH TIME ZONE NOT NULL,
    ticker TEXT NOT NULL REFERENCES ticker_master(symbol),
    tier TEXT NOT NULL,
    hype_score DOUBLE PRECISION NOT NULL,
    zscore DOUBLE PRECISION NOT NULL,
    unique_authors INTEGER NOT NULL,
    threads_touched INTEGER NOT NULL,
    avg_sentiment DOUBLE PRECISION,
    price_at_alert NUMERIC(18, 6),
    meta JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_alerts_ts_alert ON alerts(ts_alert);

-- Try to create hypertables (will fail gracefully if TimescaleDB not installed)
DO $$
BEGIN
    -- Check if TimescaleDB is available
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb') THEN
        -- Enable TimescaleDB extension
        CREATE EXTENSION IF NOT EXISTS timescaledb;

        -- Create hypertables
        PERFORM create_hypertable('reddit_items', 'created_utc', if_not_exists => TRUE);
        PERFORM create_hypertable('mention_events', 'ts_utc', if_not_exists => TRUE);
        PERFORM create_hypertable('minute_bars', 'ts_utc', if_not_exists => TRUE);
        PERFORM create_hypertable('mentions_1m', 'ts_utc', if_not_exists => TRUE);
        PERFORM create_hypertable('alerts', 'ts_alert', if_not_exists => TRUE);
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'TimescaleDB not available, skipping hypertable creation';
END$$;

-- Mark migrations as applied
INSERT INTO alembic_version (version_num) VALUES ('20250211_1245')
ON CONFLICT (version_num) DO NOTHING;

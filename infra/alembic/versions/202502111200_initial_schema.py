"""Initial Timescale schema for WSB Hype Radar."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250211_1200"
down_revision = None
branch_labels = None
dependent_revisions = None


def upgrade() -> None:
    op.create_table(
        "ticker_master",
        sa.Column("symbol", sa.Text(), primary_key=True),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "reddit_items",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column("link_id", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("permalink", sa.Text(), nullable=False),
    )

    op.create_table(
        "mention_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ts_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subreddit", sa.Text(), nullable=False),
        sa.Column("reddit_id", sa.Text(), sa.ForeignKey("reddit_items.id"), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("ticker", sa.Text(), sa.ForeignKey("ticker_master.symbol"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("upvotes", sa.Integer(), nullable=True),
        sa.Column("span_text", sa.Text(), nullable=True),
        sa.Column("sentiment_label", sa.SmallInteger(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("sentiment_conf", sa.Float(), nullable=True),
        sa.Column("has_options_intent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("option_side", sa.SmallInteger(), nullable=True),
        sa.UniqueConstraint("reddit_id", "ticker", name="uniq_reddit_ticker"),
    )

    op.create_table(
        "minute_bars",
        sa.Column("ts_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.Text(), sa.ForeignKey("ticker_master.symbol"), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=True),
        sa.Column("high", sa.Numeric(18, 6), nullable=True),
        sa.Column("low", sa.Numeric(18, 6), nullable=True),
        sa.Column("close", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("ticker", "ts_utc"),
    )

    op.create_table(
        "mentions_1m",
        sa.Column("ts_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.Text(), sa.ForeignKey("ticker_master.symbol"), nullable=False),
        sa.Column("mentions", sa.Integer(), nullable=False),
        sa.Column("unique_authors", sa.Integer(), nullable=False),
        sa.Column("threads_touched", sa.Integer(), nullable=False),
        sa.Column("avg_sentiment", sa.Float(), nullable=True),
        sa.Column("zscore", sa.Float(), nullable=True),
        sa.Column("ears_flag", sa.Boolean(), nullable=True),
        sa.Column("cusum_stat", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("ticker", "ts_utc"),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ts_alert", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.Text(), sa.ForeignKey("ticker_master.symbol"), nullable=False),
        sa.Column("tier", sa.Text(), nullable=False),
        sa.Column("hype_score", sa.Float(), nullable=False),
        sa.Column("zscore", sa.Float(), nullable=False),
        sa.Column("unique_authors", sa.Integer(), nullable=False),
        sa.Column("threads_touched", sa.Integer(), nullable=False),
        sa.Column("avg_sentiment", sa.Float(), nullable=True),
        sa.Column("price_at_alert", sa.Numeric(18, 6), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_alerts_ts_alert", "alerts", ["ts_alert"])

    # Optional hypertable calls (no-op if TimescaleDB not installed)
    for table, column in (
        ("reddit_items", "created_utc"),
        ("mention_events", "ts_utc"),
        ("minute_bars", "ts_utc"),
        ("mentions_1m", "ts_utc"),
        ("alerts", "ts_alert"),
    ):
        op.execute(
            f"SELECT create_hypertable('{table}', '{column}', if_not_exists=>TRUE);"
        )


def downgrade() -> None:
    op.drop_index("idx_alerts_ts_alert", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("mentions_1m")
    op.drop_table("minute_bars")
    op.drop_table("mention_events")
    op.drop_table("reddit_items")
    op.drop_table("ticker_master")

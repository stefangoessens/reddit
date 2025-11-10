"""Typed domain models shared across services."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Sequence

from pydantic import BaseModel, Field

SentimentLabel = Literal[-1, 0, 1]
AlertTier = Literal["heads-up", "actionable"]


class RedditItem(BaseModel):
    """Raw Reddit comment or submission metadata."""

    id: str
    kind: Literal["comment", "post"]
    subreddit: str
    author: str
    body: str
    created_utc: datetime
    score: int = 0
    permalink: str
    parent_id: str | None = None
    link_id: str | None = None


class MentionEvent(BaseModel):
    """Single (comment, ticker) mention enriched with sentiment."""

    ts_utc: datetime
    subreddit: str
    reddit_id: str
    author: str
    thread_id: str | None = None
    ticker: str
    confidence: float = Field(ge=0.0, le=1.0)
    upvotes: int = 0
    span_text: str | None = None
    price_at_mention: float | None = None
    sentiment_label: SentimentLabel = 0
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    sentiment_conf: float = Field(default=0.0, ge=0.0, le=1.0)
    has_options_intent: bool = False
    option_side: SentimentLabel = 0


class MinuteAggregation(BaseModel):
    """Per-ticker 1 minute rollup used by detectors."""

    ts_utc: datetime
    ticker: str
    mentions: int
    unique_authors: int
    threads_touched: int
    avg_sentiment: float
    zscore: float | None = None
    ears_flag: bool | None = None
    cusum_stat: float | None = None


class AlertEvent(BaseModel):
    """Structured alert ready for persistence and SSE broadcast."""

    ts_alert: datetime
    ticker: str
    tier: AlertTier
    hype_score: float
    zscore: float
    unique_authors: int
    threads_touched: int
    avg_sentiment: float
    price_at_alert: float | None = None
    meta: dict[str, object] = Field(default_factory=dict)
    references: Sequence[str] = Field(default_factory=tuple)

"""Shared Pydantic settings that keep the stack configs consistent."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class KafkaSettings(BaseSettings):
    """Kafka/Redpanda connectivity shared by ingest/trend services."""

    bootstrap_servers: str = Field(..., description="Comma separated broker addresses")
    mention_events_topic: str = Field(default="mention.events")
    alert_topic: str = Field(default="trend.alerts")
    security_protocol: str = Field(default="PLAINTEXT")
    sasl_username: str | None = None
    sasl_password: str | None = None


class PostgresSettings(BaseSettings):
    """Timescale/Postgres configuration."""

    dsn: AnyUrl = Field(..., description="postgresql+asyncpg:// user DSN")
    pool_size: int = 10
    max_overflow: int = 5


class RedditSettings(BaseSettings):
    """OAuth credentials for the Reddit ingestion worker."""

    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str = Field(default="wsb-hype-radar/0.1")
    subreddit: str = Field(default="wallstreetbets")
    poll_interval_seconds: float = Field(default=2.0)


class PriceFeedSettings(BaseSettings):
    """Price harvester access and caching knobs."""

    provider: str = Field(default="polygon")
    api_key: str
    redis_url: AnyUrl
    cache_ttl_seconds: int = 30
    symbols: List[str] = Field(default_factory=list)


class ApiSettings(BaseSettings):
    """FastAPI server options and auth toggles."""

    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: List[str] = Field(default_factory=list)
    enable_docs: bool = False
    rate_limit_per_minute: int = 60


class AppSettings(BaseSettings):
    """Top-level settings aggregator for dependency injection."""

    env: str = Field(default="development", validation_alias="APP_ENV")
    kafka: KafkaSettings
    postgres: PostgresSettings
    reddit: RedditSettings
    price_feed: PriceFeedSettings
    api: ApiSettings

    model_config = {
        "env_nested_delimiter": "__",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> AppSettings:
    """Load settings once per process for fast access."""

    return AppSettings()  # type: ignore[arg-type]

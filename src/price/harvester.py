"""Minute-bar ingestion + caching skeleton."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

from common.config import PriceFeedSettings, get_settings


class PriceHarvester:
    """Fetches minute bars from provider and caches them in Redis."""

    def __init__(self, settings: PriceFeedSettings | None = None) -> None:
        self._settings = settings or get_settings().price_feed

    async def fetch_bar(self, ticker: str, ts: datetime) -> Mapping[str, float]:
        """Fetch a minute bar from the upstream provider."""

        raise NotImplementedError("Price provider integration pending")

    async def cache_bar(self, ticker: str, bar: Mapping[str, float]) -> None:
        """Cache the bar for low-latency reuse."""

        raise NotImplementedError("Redis integration pending")

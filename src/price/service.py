"""Price stamping and storage service."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol

from common.db import PostgresClient
from price.client import PriceProvider


class MinuteBarWriter(Protocol):
    async def upsert_bar(self, ticker: str, ts: datetime, bar: Mapping[str, float]) -> None:  # pragma: no cover - interface
        ...


class MinuteBarRepository(MinuteBarWriter):
    def __init__(self, db: PostgresClient) -> None:
        self._db = db

    async def upsert_bar(self, ticker: str, ts: datetime, bar: Mapping[str, float]) -> None:
        query = """
        INSERT INTO minute_bars (ticker, ts_utc, open, high, low, close, volume)
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT (ticker, ts_utc) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
        await self._db.execute(query, ticker, ts, bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close"), bar.get("volume"))


class PriceService:
    """Fetches price bars and writes them to storage."""

    def __init__(self, provider: PriceProvider, repo: MinuteBarRepository) -> None:
        self._provider = provider
        self._repo = repo

    async def fetch_and_store(self, ticker: str, ts: datetime) -> Mapping[str, float]:
        bar = await self._provider.fetch_minute_bar(ticker, ts)
        await self._repo.upsert_bar(ticker, ts, bar)
        return bar

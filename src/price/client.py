"""Price provider client abstraction."""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

import httpx

from common.config import PriceFeedSettings


class PriceProvider(Protocol):
    async def fetch_minute_bar(self, ticker: str, ts: datetime) -> dict[str, float]:  # pragma: no cover - interface
        ...


class PolygonClient(PriceProvider):
    """Minimal Polygon.io client for minute bars."""

    def __init__(self, settings: PriceFeedSettings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(base_url="https://api.polygon.io")

    async def fetch_minute_bar(self, ticker: str, ts: datetime) -> dict[str, float]:
        date_str = ts.strftime("%Y-%m-%d")
        params = {
            "multiplier": 1,
            "timespan": "minute",
            "from": date_str,
            "to": date_str,
            "apiKey": self._settings.api_key,
        }
        resp = await self._client.get(f"/v2/aggs/ticker/{ticker}/range/1/minute/{date_str}/{date_str}", params=params)
        resp.raise_for_status()
        data = resp.json()
        for result in data.get("results", []):
            if datetime.fromtimestamp(result["t"] / 1000).replace(second=0, microsecond=0) == ts.replace(second=0, microsecond=0):
                return {
                    "open": result.get("o"),
                    "high": result.get("h"),
                    "low": result.get("l"),
                    "close": result.get("c"),
                    "volume": result.get("v"),
                }
        raise ValueError("Bar not found")

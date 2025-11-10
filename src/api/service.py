"""Application-facing services powering FastAPI handlers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import log1p
from typing import Any, Callable, Dict, List, Mapping

from common.db import PostgresClient

_WINDOW_DEFAULTS = {
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
}


class TrendService:
    """Queries mentions aggregates and formats trending payloads."""

    def __init__(self, db: PostgresClient, now_fn: Callable[[], datetime] | None = None) -> None:
        self._db = db
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    async def top_trending(self, window: str = "5m", limit: int = 10) -> List[Dict[str, Any]]:
        interval = self._parse_window(window)
        now = self._now()
        since = now - interval
        rows = await self._db.fetch(
            """
            SELECT agg.ticker,
                   SUM(agg.mentions) AS mentions,
                   SUM(agg.unique_authors) AS unique_authors,
                   AVG(agg.avg_sentiment) AS avg_sentiment,
                   MAX(agg.zscore) AS zscore,
                   MIN(agg.ts_utc) AS first_seen,
                   p.close AS last_price
            FROM mentions_1m agg
            LEFT JOIN LATERAL (
              SELECT close
              FROM minute_bars
              WHERE ticker = agg.ticker
              ORDER BY ts_utc DESC
              LIMIT 1
            ) p ON TRUE
            WHERE agg.ts_utc >= $1
            GROUP BY agg.ticker, p.close
            ORDER BY mentions DESC
            LIMIT $2
            """,
            since,
            limit,
        )
        return [self._format_row(row, window) for row in rows]

    def _parse_window(self, window: str) -> timedelta:
        if window in _WINDOW_DEFAULTS:
            return _WINDOW_DEFAULTS[window]
        if window.endswith("m") and window[:-1].isdigit():
            return timedelta(minutes=int(window[:-1]))
        if window.endswith("h") and window[:-1].isdigit():
            return timedelta(hours=int(window[:-1]))
        return _WINDOW_DEFAULTS["5m"]

    def _format_row(self, row: Mapping[str, Any], window: str) -> Dict[str, Any]:
        mentions = row["mentions"] or 0
        unique_authors = row["unique_authors"] or 0
        avg_sentiment = float(row["avg_sentiment"] or 0.0)
        zscore = float(row["zscore"] or 0.0)
        hype = zscore * log1p(unique_authors) * (1 + max(min(avg_sentiment, 0.25), -0.25))
        first_seen = row["first_seen"] or self._now()
        return {
            "ticker": row["ticker"],
            "mentions": int(mentions),
            "unique_authors": int(unique_authors),
            "avg_sentiment": avg_sentiment,
            "zscore": zscore,
            "hype_score": hype,
            "first_seen": first_seen.isoformat(),
            "window": window,
            "last_price": row.get("last_price"),
        }

    def _now(self) -> datetime:
        value = self._now_fn()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

from datetime import datetime, timezone

import pytest

from api.service import TrendService


class FakeDB:
    def __init__(self) -> None:
        self.queries: list[tuple[str, tuple]] = []
        self._rows = []

    def seed(self, rows):
        self._rows = rows

    async def fetch(self, query, *args):
        self.queries.append((query.strip(), args))
        return self._rows


@pytest.mark.asyncio
async def test_trend_service_formats_rows() -> None:
    db = FakeDB()
    now = datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc)
    db.seed(
        [
            {
                "ticker": "PLTR",
                "mentions": 20,
                "unique_authors": 10,
                "avg_sentiment": 0.2,
                "zscore": 3.0,
                "first_seen": datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc),
                "last_price": 14.5,
            }
        ]
    )
    service = TrendService(db, now_fn=lambda: now)  # type: ignore[arg-type]

    result = await service.top_trending(window="5m", limit=5)

    assert result[0]["ticker"] == "PLTR"
    assert result[0]["mentions"] == 20
    assert result[0]["last_price"] == 14.5
    assert db.queries[0][1][1] == 5

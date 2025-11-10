from datetime import datetime, timezone

import pytest

from common.models import MinuteAggregation
from trend.aggregator import AggregationRepository


class FakeDB:
    def __init__(self) -> None:
        self.executed = []

    async def executemany(self, query, rows):
        self.executed.append((query.strip(), list(rows)))

    async def fetch(self, query, arg):
        return []


@pytest.mark.asyncio
async def test_upsert_writes_rows() -> None:
    db = FakeDB()
    repo = AggregationRepository(db)  # type: ignore[arg-type]
    agg = MinuteAggregation(
        ts_utc=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        ticker="PLTR",
        mentions=5,
        unique_authors=3,
        threads_touched=2,
        avg_sentiment=0.2,
        zscore=None,
        ears_flag=None,
        cusum_stat=None,
    )

    await repo.upsert([agg])

    assert len(db.executed) == 1
    assert "INSERT INTO mentions_1m" in db.executed[0][0]
    assert db.executed[0][1][0][1] == "PLTR"

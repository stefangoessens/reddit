from datetime import datetime, timezone

import pytest

from price.service import MinuteBarRepository, PriceService


class FakeProvider:
    def __init__(self) -> None:
        self.calls = []

    async def fetch_minute_bar(self, ticker, ts):
        self.calls.append((ticker, ts))
        return {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100}


class FakeDB:
    def __init__(self) -> None:
        self.executed = []

    async def execute(self, query, *args):
        self.executed.append((query.strip(), args))


@pytest.mark.asyncio
async def test_price_service_fetches_and_stores():
    db = FakeDB()
    provider = FakeProvider()
    repo = MinuteBarRepository(db)  # type: ignore[arg-type]
    service = PriceService(provider, repo)  # type: ignore[arg-type]
    ts = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    bar = await service.fetch_and_store("PLTR", ts)

    assert bar["close"] == 1.5
    assert provider.calls[0][0] == "PLTR"
    assert "INSERT INTO minute_bars" in db.executed[0][0]

import asyncio
import pytest

from scripts.seed_tickers import upsert_tickers


class FakeDB:
    def __init__(self) -> None:
        self.rows = []

    async def executemany(self, query, payload):
        self.rows.extend(payload)


@pytest.mark.asyncio
async def test_upsert_tickers_batches_rows():
    db = FakeDB()
    rows = [
        {"symbol": "PLTR", "exchange": "NASDAQ", "name": "Palantir"},
        {"symbol": "AAPL", "exchange": "NASDAQ", "name": "Apple"},
    ]

    count = await upsert_tickers(db, rows)  # type: ignore[arg-type]

    assert count == 2
    assert db.rows[0][0] == "PLTR"
    assert db.rows[1][2] == "Apple"

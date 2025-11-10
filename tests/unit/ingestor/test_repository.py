from datetime import datetime

import pytest

from common.models import MentionEvent, RedditItem
from ingestor.repository import MentionRepository


class FakeDB:
    def __init__(self) -> None:
        self.executed: list[tuple[str, object]] = []
        self.prices: dict[tuple[str, datetime], float] = {}

    async def execute(self, query, *args):
        self.executed.append(("execute", query.strip(), args))

    async def executemany(self, query, rows):
        self.executed.append(("executemany", query.strip(), list(rows)))

    async def fetch(self, query, *args):
        key = (args[0], args[1])
        if key in self.prices:
            return [{"close": self.prices[key]}]
        return []


class FakePriceService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, datetime]] = []

    async def fetch_and_store(self, ticker, ts):
        self.calls.append((ticker, ts))
        return {"close": 10.0}


def make_item() -> RedditItem:
    return RedditItem(
        id="abc",
        kind="comment",
        subreddit="wallstreetbets",
        author="u/test",
        body="Sample body",
        created_utc=datetime(2024, 1, 1, 0, 0, 0),
        score=1,
        permalink="https://reddit.com/abc",
    )


def make_mention() -> MentionEvent:
    return MentionEvent(
        ts_utc=datetime(2024, 1, 1, 0, 0, 0),
        subreddit="wallstreetbets",
        reddit_id="abc",
        author="u/test",
        ticker="PLTR",
        confidence=0.9,
        upvotes=1,
        span_text="PLTR calls",
        sentiment_label=1,
        sentiment_score=0.3,
        sentiment_conf=0.8,
        has_options_intent=True,
        option_side=1,
    )


@pytest.mark.asyncio
async def test_repository_persists_item_and_mentions():
    db = FakeDB()
    repo = MentionRepository(db, price_service=FakePriceService())  # type: ignore[arg-type]

    count = await repo.persist(make_item(), [make_mention()])

    assert count == 1
    assert len(db.executed) == 2
    assert db.executed[0][0] == "execute"
    assert "INSERT INTO reddit_items" in db.executed[0][1]
    assert db.executed[1][0] == "executemany"
    assert "INSERT INTO mention_events" in db.executed[1][1]

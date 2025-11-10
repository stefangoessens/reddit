from datetime import datetime

import pytest

from common.config import RedditSettings
from common.models import MentionEvent, RedditItem
from ingestor.service import RedditStreamIngestor
from nlp.pipeline import MentionExtractor, SentimentAnnotator

TICKERS = {"PLTR", "A"}
STOPLIST = {"A", "IT", "ON", "ALL", "ARE", "FOR", "GO", "BE"}
ALIAS_MAP = {"palantir": "PLTR"}


class FakeClient:
    def __init__(self, items: list[RedditItem]) -> None:
        self._items = items

    async def stream_comments(self):  # type: ignore[override]
        for item in self._items:
            yield item


class InMemoryWriter:
    def __init__(self) -> None:
        self.items: list[RedditItem] = []
        self.mentions: list[MentionEvent] = []

    async def persist(self, item: RedditItem, mentions: list[MentionEvent]) -> int:
        self.items.append(item)
        self.mentions.extend(mentions)
        return len(mentions)


def make_item(body: str) -> RedditItem:
    return RedditItem(
        id="t1",
        kind="comment",
        subreddit="wallstreetbets",
        author="u/test",
        body=body,
        created_utc=datetime(2024, 1, 1, 0, 0, 0),
        score=5,
        permalink="https://reddit.com/t1",
    )


@pytest.mark.asyncio
async def test_ingestor_handles_items_and_publishes_mentions() -> None:
    extractor = MentionExtractor(TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    annotator = SentimentAnnotator()
    writer = InMemoryWriter()
    client = FakeClient([])
    settings = RedditSettings(
        client_id="c",
        client_secret="s",
        username="u",
        password="p",
        user_agent="wsb",
        subreddit="wallstreetbets",
    )
    ingestor = RedditStreamIngestor(extractor, annotator, writer, reddit_client=client, settings=settings)

    count = await ingestor.handle_item(make_item("$PLTR is ripping"))

    assert count == 1
    assert len(writer.mentions) == 1
    assert writer.mentions[0].ticker == "PLTR"


@pytest.mark.asyncio
async def test_fetch_items_streams_from_client() -> None:
    extractor = MentionExtractor(TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    annotator = SentimentAnnotator()
    writer = InMemoryWriter()
    item = make_item("$PLTR to the moon")
    client = FakeClient([item])
    settings = RedditSettings(
        client_id="c",
        client_secret="s",
        username="u",
        password="p",
        user_agent="wsb",
        subreddit="wallstreetbets",
    )
    ingestor = RedditStreamIngestor(extractor, annotator, writer, reddit_client=client, settings=settings)

    items = []
    async for fetched in ingestor.fetch_items():
        items.append(fetched)
        break

    assert items[0].id == item.id

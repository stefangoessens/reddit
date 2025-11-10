from datetime import datetime, timezone

import pytest

from common.models import MentionEvent, MinuteAggregation
from trend.aggregator import MentionsAggregator, MinuteAggregationWriter


class FakeWriter(MinuteAggregationWriter):
    def __init__(self) -> None:
        self.aggregations: list[MinuteAggregation] = []

    async def upsert(self, aggregations):  # type: ignore[override]
        self.aggregations.extend(aggregations)


def make_mention(ts: datetime, ticker: str, author: str, thread_id: str) -> MentionEvent:
    return MentionEvent(
        ts_utc=ts,
        subreddit="wallstreetbets",
        reddit_id=thread_id,
        author=author,
        thread_id=thread_id,
        ticker=ticker,
        confidence=0.9,
        upvotes=1,
        span_text="sample",
        sentiment_label=1,
        sentiment_score=0.2,
        sentiment_conf=0.8,
        has_options_intent=False,
        option_side=0,
    )


@pytest.mark.asyncio
async def test_mentions_aggregator_groups_by_minute() -> None:
    writer = FakeWriter()
    aggregator = MentionsAggregator(writer)
    base = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    aggregator.add(make_mention(base, "PLTR", "u1", "t1"))
    aggregator.add(make_mention(base.replace(second=30), "PLTR", "u2", "t2"))
    aggregator.add(make_mention(base.replace(minute=1), "AAPL", "u1", "t3"))

    count = await aggregator.flush()

    assert count == 2
    first = writer.aggregations[0]
    assert first.mentions == 2
    assert first.unique_authors == 2
    assert first.threads_touched == 2

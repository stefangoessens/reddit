"""Mention aggregation helpers."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, Protocol, Sequence

from common.db import PostgresClient
from common.models import MentionEvent, MinuteAggregation


class MinuteAggregationWriter(Protocol):
    async def upsert(self, aggregations: Sequence[MinuteAggregation]) -> None:
        ...


@dataclass
class _Bucket:
    mentions: int = 0
    authors: set[str] = field(default_factory=set)
    threads: set[str] = field(default_factory=set)
    sentiment_sum: float = 0.0


class MentionsAggregator:
    """Accumulates mention events into 1-minute aggregations."""

    def __init__(self, writer: MinuteAggregationWriter) -> None:
        self._writer = writer
        self._buckets: dict[tuple[str, datetime], _Bucket] = defaultdict(_Bucket)

    def add(self, mention: MentionEvent) -> None:
        key = (mention.ticker, self._minute_bucket(mention.ts_utc))
        bucket = self._buckets[key]
        bucket.mentions += 1
        bucket.authors.add(mention.author)
        bucket.threads.add(mention.thread_id or mention.reddit_id)
        bucket.sentiment_sum += mention.sentiment_score

    def extend(self, mentions: Iterable[MentionEvent]) -> None:
        for mention in mentions:
            self.add(mention)

    async def flush(self) -> int:
        aggs: list[MinuteAggregation] = []
        for (ticker, ts), bucket in self._buckets.items():
            avg_sent = bucket.sentiment_sum / bucket.mentions if bucket.mentions else 0.0
            aggs.append(
                MinuteAggregation(
                    ts_utc=ts,
                    ticker=ticker,
                    mentions=bucket.mentions,
                    unique_authors=len(bucket.authors),
                    threads_touched=len(bucket.threads),
                    avg_sentiment=avg_sent,
                )
            )
        if aggs:
            await self._writer.upsert(aggs)
        count = len(aggs)
        self._buckets.clear()
        return count

    @staticmethod
    def _minute_bucket(ts: datetime) -> datetime:
        tz = ts.tzinfo or timezone.utc
        return ts.replace(second=0, microsecond=0, tzinfo=tz)


class AggregationRepository(MinuteAggregationWriter):
    """DB interactions for mention aggregations."""

    def __init__(self, db: PostgresClient) -> None:
        self._db = db

    async def upsert(self, aggregations: Sequence[MinuteAggregation]) -> None:
        query = """
        INSERT INTO mentions_1m (
            ts_utc,
            ticker,
            mentions,
            unique_authors,
            threads_touched,
            avg_sentiment,
            zscore,
            ears_flag,
            cusum_stat
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9
        )
        ON CONFLICT (ticker, ts_utc) DO UPDATE SET
            mentions = EXCLUDED.mentions,
            unique_authors = EXCLUDED.unique_authors,
            threads_touched = EXCLUDED.threads_touched,
            avg_sentiment = EXCLUDED.avg_sentiment,
            zscore = EXCLUDED.zscore,
            ears_flag = EXCLUDED.ears_flag,
            cusum_stat = EXCLUDED.cusum_stat
        """
        rows = [
            (
                agg.ts_utc,
                agg.ticker,
                agg.mentions,
                agg.unique_authors,
                agg.threads_touched,
                agg.avg_sentiment,
                agg.zscore,
                agg.ears_flag,
                agg.cusum_stat,
            )
            for agg in aggregations
        ]
        await self._db.executemany(query, rows)

    async def fetch_mentions_since(self, since: datetime) -> list[MentionEvent]:
        query = """
        SELECT me.ts_utc,
               me.subreddit,
               me.reddit_id,
               me.author,
               me.ticker,
               me.confidence,
               me.upvotes,
               me.span_text,
               me.sentiment_label,
               me.sentiment_score,
               me.sentiment_conf,
               me.has_options_intent,
               me.option_side,
               ri.link_id AS thread_id
        FROM mention_events me
        JOIN reddit_items ri ON ri.id = me.reddit_id
        WHERE me.ts_utc >= $1
        ORDER BY me.ts_utc ASC
        """
        rows = await self._db.fetch(query, since)
        mentions: list[MentionEvent] = []
        for row in rows:
            mentions.append(
                MentionEvent(
                    ts_utc=row["ts_utc"],
                    subreddit=row["subreddit"],
                    reddit_id=row["reddit_id"],
                    author=row["author"],
                    thread_id=row["thread_id"],
                    ticker=row["ticker"],
                    confidence=row["confidence"],
                    upvotes=row["upvotes"],
                    span_text=row["span_text"],
                    sentiment_label=row["sentiment_label"],
                    sentiment_score=row["sentiment_score"],
                    sentiment_conf=row["sentiment_conf"],
                    has_options_intent=row["has_options_intent"],
                    option_side=row["option_side"],
                )
            )
        return mentions

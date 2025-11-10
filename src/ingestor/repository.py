"""Persistence layer for Reddit items and mention events."""
from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from common.models import MentionEvent, RedditItem
from price.service import PriceService


class DatabaseClient(Protocol):
    async def execute(self, query: str, *args) -> object:  # pragma: no cover - interface
        ...

    async def executemany(self, query: str, args) -> None:  # pragma: no cover - interface
        ...

    async def fetch(self, query: str, *args) -> list[dict]:  # pragma: no cover - interface
        ...


class MentionWriter:
    """Publishes mention events into durable storage."""

    async def persist(self, item: RedditItem, mentions: Sequence[MentionEvent]) -> int:  # pragma: no cover - interface
        raise NotImplementedError


class MentionRepository(MentionWriter):
    """Stores Reddit metadata and mention events in Postgres."""

    def __init__(self, db: DatabaseClient, price_service: PriceService | None = None) -> None:
        self._db = db
        self._price_service = price_service

    async def persist(self, item: RedditItem, mentions: Sequence[MentionEvent]) -> int:
        await self._upsert_reddit_item(item)
        if mentions:
            await self._insert_mentions(mentions)
        return len(mentions)

    async def _upsert_reddit_item(self, item: RedditItem) -> None:
        query = """
        INSERT INTO reddit_items (id, kind, parent_id, link_id, author, body, created_utc, score, permalink)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        ON CONFLICT (id) DO UPDATE
          SET score = EXCLUDED.score,
              body = EXCLUDED.body,
              author = EXCLUDED.author
        """
        await self._db.execute(
            query,
            item.id,
            item.kind,
            item.parent_id,
            item.link_id,
            item.author,
            item.body,
            item.created_utc,
            item.score,
            item.permalink,
        )

    async def _insert_mentions(self, mentions: Sequence[MentionEvent]) -> None:
        query = """
        INSERT INTO mention_events (
            ts_utc,
            subreddit,
            reddit_id,
            author,
            ticker,
            confidence,
            upvotes,
            span_text,
            price_at_mention,
            sentiment_label,
            sentiment_score,
            sentiment_conf,
            has_options_intent,
            option_side
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14
        )
        ON CONFLICT (reddit_id, ticker) DO UPDATE SET
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_score = EXCLUDED.sentiment_score,
            sentiment_conf = EXCLUDED.sentiment_conf,
            confidence = EXCLUDED.confidence,
            upvotes = EXCLUDED.upvotes,
            span_text = EXCLUDED.span_text,
            price_at_mention = EXCLUDED.price_at_mention,
            has_options_intent = EXCLUDED.has_options_intent,
            option_side = EXCLUDED.option_side
        """
        price_cache: dict[tuple[str, datetime], float | None] = {}
        rows = []
        for mention in mentions:
            if mention.price_at_mention is None:
                key = (mention.ticker, self._minute_bucket(mention.ts_utc))
                if key not in price_cache:
                    price_cache[key] = await self._get_price(*key)
                mention.price_at_mention = price_cache[key]
            rows.append(
                (
                    mention.ts_utc,
                    mention.subreddit,
                    mention.reddit_id,
                    mention.author,
                    mention.ticker,
                    mention.confidence,
                    mention.upvotes,
                    mention.span_text,
                    mention.price_at_mention,
                    mention.sentiment_label,
                    mention.sentiment_score,
                    mention.sentiment_conf,
                    mention.has_options_intent,
                    mention.option_side,
                )
            )
        await self._db.executemany(query, rows)

    async def _get_price(self, ticker: str, ts: datetime) -> float | None:
        price_row = await self._db.fetch(
            "SELECT close FROM minute_bars WHERE ticker=$1 AND ts_utc=$2 LIMIT 1",
            ticker,
            ts,
        )
        if price_row:
            return price_row[0]["close"]
        if self._price_service:
            bar = await self._price_service.fetch_and_store(ticker, ts)
            return bar.get("close")
        return None

    @staticmethod
    def _minute_bucket(ts: datetime) -> datetime:
        return ts.replace(second=0, microsecond=0)

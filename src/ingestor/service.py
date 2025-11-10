"""Reddit ingestion worker skeleton."""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from common.config import RedditSettings, get_settings
from common.models import RedditItem
from ingestor.reddit_client import RedditClient
from ingestor.repository import MentionWriter
from nlp.pipeline import MentionExtractor, SentimentAnnotator



class RedditStreamIngestor:
    """Polls Reddit, runs extraction/sentiment, and publishes mention events."""

    def __init__(
        self,
        extractor: MentionExtractor,
        annotator: SentimentAnnotator,
        writer: MentionWriter,
        reddit_client: RedditClient | None = None,
        settings: RedditSettings | None = None,
    ) -> None:
        self._settings = settings or get_settings().reddit
        self._extractor = extractor
        self._annotator = annotator
        self._writer = writer
        self._client = reddit_client or RedditClient(self._settings)

    async def fetch_items(self) -> AsyncIterator[RedditItem]:
        async for item in self._client.stream_comments():
            yield item

    async def run(self) -> None:
        """Continuously read Reddit and push into message queue."""

        while True:
            async for item in self.fetch_items():
                await self.handle_item(item)
            await asyncio.sleep(self._settings.poll_interval_seconds)

    async def handle_item(self, item: RedditItem) -> int:
        """Run NLP over a Reddit item and publish resulting mentions."""

        extraction = self._extractor.extract(item)
        annotated = self._annotator.annotate(list(extraction.mentions))
        return await self._writer.persist(item, annotated)

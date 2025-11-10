"""Reddit API client wrapper."""
from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import datetime, timezone
from typing import AsyncIterator

import praw
from praw.models import Comment

from common.config import RedditSettings
from common.models import RedditItem


class RedditClient:
    """Thin wrapper around PRAW for fetching subreddit comments."""

    def __init__(self, settings: RedditSettings) -> None:
        self._settings = settings
        self._client = praw.Reddit(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            password=settings.password,
            username=settings.username,
            user_agent=settings.user_agent,
        )

    async def stream_comments(self) -> AsyncIterator[RedditItem]:
        subreddit = self._client.subreddit(self._settings.subreddit)
        iterator = subreddit.stream.comments(skip_existing=True)
        loop = asyncio.get_running_loop()
        while True:
            comment = await loop.run_in_executor(None, next, iterator)
            yield self._to_item(comment)

    def _to_item(self, comment: Comment) -> RedditItem:
        return RedditItem(
            id=comment.id,
            kind="comment",
            subreddit=comment.subreddit.display_name,
            author=str(comment.author) if comment.author else "[deleted]",
            body=comment.body,
            created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            score=comment.score,
            permalink=comment.permalink,
            parent_id=comment.parent_id,
            link_id=comment.link_id,
        )

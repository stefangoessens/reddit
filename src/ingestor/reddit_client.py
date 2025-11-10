"""Reddit API client using public JSON endpoints."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from common.config import RedditSettings
from common.models import RedditItem


class RedditClient:
    """Client for fetching subreddit comments using Reddit's public JSON API."""

    def __init__(self, settings: RedditSettings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": settings.user_agent,
            },
            timeout=30.0,
        )
        self._seen_ids: set[str] = set()

    async def stream_comments(self) -> AsyncIterator[RedditItem]:
        """Stream new comments from the subreddit by polling the JSON API."""
        url = f"https://www.reddit.com/r/{self._settings.subreddit}/comments.json"

        while True:
            try:
                response = await self._client.get(url, params={"limit": 100})
                response.raise_for_status()
                data = response.json()

                # Extract comments from JSON response
                comments = data.get("data", {}).get("children", [])

                # Process comments in reverse order (oldest first)
                for comment_data in reversed(comments):
                    comment = comment_data.get("data", {})
                    comment_id = comment.get("id")

                    # Skip if we've already seen this comment
                    if comment_id in self._seen_ids:
                        continue

                    self._seen_ids.add(comment_id)

                    # Keep set size manageable (last 10k comments)
                    if len(self._seen_ids) > 10000:
                        self._seen_ids.pop()

                    yield self._to_item(comment)

                # Wait before polling again (Reddit rate limit: ~60 requests/min)
                await asyncio.sleep(2)

            except Exception as e:
                print(f"Error fetching comments: {e}")
                await asyncio.sleep(10)

    def _to_item(self, comment: dict) -> RedditItem:
        """Convert Reddit JSON comment to RedditItem."""
        return RedditItem(
            id=comment.get("id", ""),
            kind="comment",
            subreddit=comment.get("subreddit", self._settings.subreddit),
            author=comment.get("author", "[deleted]"),
            body=comment.get("body", ""),
            created_utc=datetime.fromtimestamp(
                comment.get("created_utc", 0), tz=timezone.utc
            ),
            score=comment.get("score", 0),
            permalink=comment.get("permalink", ""),
            parent_id=comment.get("parent_id", ""),
            link_id=comment.get("link_id", ""),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

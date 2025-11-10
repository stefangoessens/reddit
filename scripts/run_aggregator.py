"""Runs the mention aggregator over a rolling window."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from common.config import get_settings
from common.db import PostgresClient
from trend.aggregator import AggregationRepository, MentionsAggregator


async def main(window_minutes: int) -> None:
    settings = get_settings()
    db = PostgresClient(dsn=str(settings.postgres.dsn))
    await db.connect()
    try:
        repo = AggregationRepository(db)
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        mentions = await repo.fetch_mentions_since(since)
        aggregator = MentionsAggregator(repo)
        aggregator.extend(mentions)
        buckets = await aggregator.flush()
    finally:
        await db.close()
    print(f"Aggregated {buckets} minute buckets from {len(mentions)} mentions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run mention aggregator once")
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(main(args.window))

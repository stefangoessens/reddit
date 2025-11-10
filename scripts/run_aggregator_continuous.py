"""Continuously runs the mention aggregator at regular intervals."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from common.config import get_settings
from common.db import PostgresClient
from trend.aggregator import AggregationRepository, MentionsAggregator


async def aggregate_once(repo: AggregationRepository, window_minutes: int) -> int:
    """Run one aggregation cycle."""
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    mentions = await repo.fetch_mentions_since(since)
    aggregator = MentionsAggregator(repo)
    aggregator.extend(mentions)
    buckets = await aggregator.flush()
    print(f"[{datetime.now(timezone.utc).isoformat()}] Aggregated {buckets} minute buckets from {len(mentions)} mentions")
    return buckets


async def main(window_minutes: int, poll_seconds: int) -> None:
    """Main loop that continuously aggregates mentions."""
    settings = get_settings()
    db = PostgresClient(dsn=str(settings.postgres.dsn))
    await db.connect()
    try:
        repo = AggregationRepository(db)
        while True:
            try:
                await aggregate_once(repo, window_minutes)
            except Exception as e:
                print(f"Error during aggregation: {e}")
            await asyncio.sleep(poll_seconds)
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run mention aggregator continuously")
    parser.add_argument("--window", type=int, default=5, help="Window in minutes to look back")
    parser.add_argument("--poll-seconds", type=int, default=60, help="Polling interval in seconds")
    args = parser.parse_args()
    asyncio.run(main(args.window, args.poll_seconds))

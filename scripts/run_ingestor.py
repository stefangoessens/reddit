"""Entry point for Reddit ingestion worker."""
from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from common.config import get_settings
from common.db import PostgresClient
from ingestor.repository import MentionRepository
from ingestor.reddit_client import RedditClient
from ingestor.service import RedditStreamIngestor
from nlp.pipeline import MentionExtractor, SentimentAnnotator

STOPLIST = {"A", "IT", "ON", "ALL", "ARE", "FOR", "GO", "BE"}


def load_tickers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row["symbol"].upper() for row in reader]


async def main(ticker_file: Path) -> None:
    settings = get_settings()
    tickers = load_tickers(ticker_file)
    db = PostgresClient(dsn=str(settings.postgres.dsn))
    await db.connect()
    repo = MentionRepository(db)
    extractor = MentionExtractor(tickers, STOPLIST)
    annotator = SentimentAnnotator()
    reddit_client = RedditClient(settings.reddit)
    ingestor = RedditStreamIngestor(extractor, annotator, repo, reddit_client=reddit_client, settings=settings.reddit)
    try:
        await ingestor.run()
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Reddit ingestion worker")
    parser.add_argument("--tickers", type=Path, default=Path("data/tickers.csv"))
    args = parser.parse_args()
    asyncio.run(main(args.tickers))

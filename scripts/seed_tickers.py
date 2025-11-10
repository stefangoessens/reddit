"""Seed ticker_master from CSV file."""
from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path
from typing import Iterable

from common.config import get_settings
from common.db import PostgresClient


async def upsert_tickers(db: PostgresClient, rows: Iterable[dict[str, str]]) -> int:
    query = """
    INSERT INTO ticker_master (symbol, exchange, name, is_active)
    VALUES ($1, $2, $3, TRUE)
    ON CONFLICT (symbol) DO UPDATE
      SET exchange = EXCLUDED.exchange,
          name = EXCLUDED.name,
          is_active = TRUE
    """
    payload = [(row["symbol"], row["exchange"], row["name"]) for row in rows]
    await db.executemany(query, payload)
    return len(payload)


async def main(path: Path) -> None:
    settings = get_settings()
    db = PostgresClient(dsn=str(settings.postgres.dsn))
    await db.connect()
    try:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            count = await upsert_tickers(db, reader)
    finally:
        await db.close()
    print(f"Seeded {count} tickers from {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed ticker_master from CSV")
    parser.add_argument("--file", type=Path, default=Path("data/tickers.csv"))
    args = parser.parse_args()
    asyncio.run(main(args.file))

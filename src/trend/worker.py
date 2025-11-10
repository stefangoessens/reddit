"""Background alert worker that loads aggregations and publishes alerts."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from common.config import get_settings
from common.db import PostgresClient
from api.stream import broadcaster
from trend.alerts import AlertService, PostgresAlertRepository
from trend.detectors import BaselineWindow, DetectionInput, TrendEngine
from trend.aggregator import AggregationRepository


async def fetch_detections(db: PostgresClient, since: datetime) -> list[DetectionInput]:
    query = """
    SELECT ts_utc,
           ticker,
           mentions,
           unique_authors,
           threads_touched,
           avg_sentiment
    FROM mentions_1m
    WHERE ts_utc >= $1
    ORDER BY ts_utc ASC
    LIMIT 500
    """
    rows = await db.fetch(query, since)
    detections: list[DetectionInput] = []
    for row in rows:
        agg = row
        detections.append(
            DetectionInput(
                aggregation=agg,
                short_baseline=BaselineWindow(mean=max(1, agg["mentions"] - 1), stddev=1.0),
                diurnal_mean=1.0,
            )
        )
    return detections


async def run_alert_worker(poll_seconds: int = 30) -> None:
    settings = get_settings()
    db = PostgresClient(dsn=str(settings.postgres.dsn))
    await db.connect()
    repo = PostgresAlertRepository(db)
    engine = TrendEngine()

    # Optional price service (only if price_feed config is provided)
    price_service = None
    if settings.price_feed is not None:
        from price.client import PolygonClient
        from price.service import MinuteBarRepository, PriceService
        price_service = PriceService(PolygonClient(settings.price_feed), MinuteBarRepository(db))

    service = AlertService(engine, repo, price_service=price_service, alert_broadcaster=broadcaster)
    since = datetime.now(timezone.utc) - timedelta(minutes=15)
    try:
        while True:
            detections = await fetch_detections(db, since)
            if detections:
                await service.process(detections)
                since = detections[-1].aggregation.ts_utc
            await asyncio.sleep(poll_seconds)
    finally:
        await db.close()

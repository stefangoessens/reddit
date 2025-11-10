"""Alert generation service built on TrendEngine."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol, Sequence

from common.db import PostgresClient
from common.models import AlertEvent, MinuteAggregation
from api.stream import AlertBroadcaster, broadcaster
from trend.detectors import DetectionInput, TrendEngine
from price.service import PriceService


class AlertRepository(Protocol):
    async def insert_alert(self, alert: AlertEvent) -> None:  # pragma: no cover - interface
        ...


class PostgresAlertRepository:
    def __init__(self, db: PostgresClient) -> None:
        self._db = db

    async def insert_alert(self, alert: AlertEvent) -> None:
        query = """
        INSERT INTO alerts (
            ts_alert,
            ticker,
            tier,
            hype_score,
            zscore,
            unique_authors,
            threads_touched,
            avg_sentiment,
            price_at_alert,
            meta
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10
        )
        """
        await self._db.execute(
            query,
            alert.ts_alert,
            alert.ticker,
            alert.tier,
            alert.hype_score,
            alert.zscore,
            alert.unique_authors,
            alert.threads_touched,
            alert.avg_sentiment,
            alert.price_at_alert,
            alert.meta,
        )


class AlertService:
    """Consumes minute aggregations, runs TrendEngine, stamps prices, and persists alerts."""

    def __init__(
        self,
        engine: TrendEngine,
        repo: AlertRepository,
        price_service: PriceService | None = None,
        alert_broadcaster: AlertBroadcaster | None = None,
    ) -> None:
        self._engine = engine
        self._repo = repo
        self._price_service = price_service
        self._broadcaster = alert_broadcaster or broadcaster

    async def process(self, detections: Iterable[DetectionInput]) -> list[AlertEvent]:
        alerts = self._engine.process(detections)
        for alert in alerts:
            if alert.price_at_alert is None and self._price_service:
                bar = await self._price_service.fetch_and_store(alert.ticker, alert.ts_alert)
                alert.price_at_alert = bar.get("close")
            await self._repo.insert_alert(alert)
            if self._broadcaster:
                await self._broadcaster.publish(alert)
        return alerts

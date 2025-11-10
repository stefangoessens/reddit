from datetime import datetime, timezone

import pytest

from common.models import AlertEvent, MinuteAggregation
from api.stream import AlertBroadcaster
from trend.alerts import AlertService
from trend.detectors import BaselineWindow, DetectionInput, TrendEngine


class FakeRepo:
    def __init__(self) -> None:
        self.alerts: list[AlertEvent] = []

    async def insert_alert(self, alert: AlertEvent) -> None:
        self.alerts.append(alert)


@pytest.mark.asyncio
async def test_alert_service_persists_alerts() -> None:
    repo = FakeRepo()
    engine = TrendEngine(heads_up_z=0.5)
    class FakePriceService:
        def __init__(self) -> None:
            self.calls = []

        async def fetch_and_store(self, ticker, ts):
            self.calls.append((ticker, ts))
            return {"close": 9.5}

    class RecordingBroadcaster(AlertBroadcaster):
        def __init__(self) -> None:
            super().__init__()
            self.published: list[AlertEvent] = []

        async def publish(self, alert: AlertEvent) -> None:  # type: ignore[override]
            self.published.append(alert)
            await super().publish(alert)

    broadcaster = RecordingBroadcaster()
    service = AlertService(engine, repo, price_service=FakePriceService(), alert_broadcaster=broadcaster)
    agg = MinuteAggregation(
        ts_utc=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        ticker="PLTR",
        mentions=10,
        unique_authors=5,
        threads_touched=3,
        avg_sentiment=0.2,
        zscore=3.0,
    )
    detection = DetectionInput(
        aggregation=agg,
        short_baseline=BaselineWindow(mean=1, stddev=1),
        diurnal_mean=1,
    )

    alerts = await service.process([detection])

    assert alerts
    assert repo.alerts[0].price_at_alert == 9.5
    assert broadcaster.published[0].ticker == "PLTR"

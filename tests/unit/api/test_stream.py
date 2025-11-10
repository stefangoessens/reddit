import asyncio

import pytest

from datetime import datetime, timezone

from api.stream import AlertBroadcaster
from common.models import AlertEvent


@pytest.mark.asyncio
async def test_broadcaster_replays_history():
    broadcaster = AlertBroadcaster(max_history=2)
    alert = AlertEvent(
        ts_alert=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        ticker="PLTR",
        tier="heads-up",
        hype_score=1.0,
        zscore=2.0,
        unique_authors=3,
        threads_touched=2,
        avg_sentiment=0.2,
    )
    await broadcaster.publish(alert)
    gen = broadcaster.subscribe()
    result = await gen.__anext__()
    assert result.ticker == "PLTR"

from datetime import datetime, timedelta

import pytest

from common.models import MinuteAggregation
from trend.detectors import (
    BaselineWindow,
    CusumDetector,
    DetectionInput,
    EarsDetector,
    TrendEngine,
    compute_zscore,
)


def make_agg(
    mentions: int,
    unique_authors: int = 4,
    threads: int = 3,
    avg_sentiment: float = 0.1,
    ts: datetime | None = None,
) -> MinuteAggregation:
    return MinuteAggregation(
        ts_utc=ts or datetime(2024, 1, 1, 0, 0, 0),
        ticker="PLTR",
        mentions=mentions,
        unique_authors=unique_authors,
        threads_touched=threads,
        avg_sentiment=avg_sentiment,
    )


def test_compute_zscore_honors_floor() -> None:
    agg = make_agg(mentions=10)
    baseline = BaselineWindow(mean=5, stddev=0)
    assert compute_zscore(agg, baseline, floor=2.0) == pytest.approx(2.5)


def test_ears_detector_triggers_after_baseline() -> None:
    detector = EarsDetector(baseline_length=3, guard_band=1, threshold=2.0)
    for value in [5, 5, 5]:
        assert detector.update(value) is False
    assert detector.update(12) is True


def test_cusum_detector_accumulates_positive_shift() -> None:
    detector = CusumDetector(k=1.0, h=3.0)
    alarms = [detector.update(value, expected=4.0) for value in [6, 6, 6, 6]]
    assert alarms[-1] is True


def test_trend_engine_enforces_guardrails() -> None:
    engine = TrendEngine(min_authors=3, min_threads=2, heads_up_z=1.5)
    baseline = BaselineWindow(mean=2, stddev=1)
    detection = DetectionInput(
        aggregation=make_agg(mentions=6, unique_authors=2, threads=1),
        short_baseline=baseline,
        diurnal_mean=2,
    )
    assert engine.process([detection]) == []


def test_trend_engine_emits_actionable_when_ears_fires() -> None:
    engine = TrendEngine(
        heads_up_z=1.5,
        actionable_z=2.5,
        ears_baseline_len=3,
        ears_guard_band=1,
        ears_threshold=2.0,
    )
    baseline = BaselineWindow(mean=5, stddev=1)
    start = datetime(2024, 1, 1, 0, 0, 0)
    inputs: list[DetectionInput] = []
    for idx, value in enumerate([5, 5, 5, 15]):
        inputs.append(
            DetectionInput(
                aggregation=make_agg(mentions=value, ts=start + timedelta(minutes=idx)),
                short_baseline=baseline,
                diurnal_mean=5,
            )
        )
    alerts = engine.process(inputs)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.tier == "actionable"
    assert alert.meta["ears"] is True


def test_trend_engine_actionable_via_cusum_only() -> None:
    engine = TrendEngine(
        heads_up_z=1.5,
        actionable_z=2.0,
        ears_baseline_len=5,
        ears_guard_band=2,
        ears_threshold=100.0,  # effectively disable EARS
        cusum_k=0.5,
        cusum_h=2.0,
    )
    baseline = BaselineWindow(mean=4, stddev=1)
    inputs: list[DetectionInput] = []
    for idx, value in enumerate([4, 5, 6, 7, 8]):
        inputs.append(
            DetectionInput(
                aggregation=make_agg(mentions=value, ts=datetime(2024, 1, 1, 0, idx)),
                short_baseline=baseline,
                diurnal_mean=4,
            )
        )
    alerts = engine.process(inputs)
    assert alerts[-1].meta["cusum"] is True
    assert alerts[-1].tier == "actionable"

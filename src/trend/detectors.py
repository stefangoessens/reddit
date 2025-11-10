"""Burst detection utilities used by the Trend Engine."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Deque, Iterable, Sequence

from common.models import AlertEvent, MinuteAggregation


@dataclass
class BaselineWindow:
    """Holds rolling statistics for the z-score detector."""

    mean: float
    stddev: float


@dataclass
class DetectionInput:
    """All signals required to evaluate a minute aggregation."""

    aggregation: MinuteAggregation
    short_baseline: BaselineWindow
    diurnal_mean: float


def compute_zscore(agg: MinuteAggregation, baseline: BaselineWindow, floor: float = 1.0) -> float:
    """Return z-score guarding against zero std deviation."""

    denom = max(baseline.stddev, floor)
    return (agg.mentions - baseline.mean) / denom


def hype_score(zscore: float, unique_authors: int, avg_sentiment: float) -> float:
    """Composite hype metric described in the SPEC."""

    sent_multiplier = 1 + max(min(avg_sentiment, 0.25), -0.25)
    return zscore * (unique_authors + 1) ** 0.5 * sent_multiplier


class EarsDetector:
    """CDC EARS C2/C3 style anomaly detector with rolling baseline."""

    def __init__(self, baseline_length: int = 7, guard_band: int = 2, threshold: float = 3.0) -> None:
        if baseline_length <= 0:
            msg = "baseline_length must be > 0"
            raise ValueError(msg)
        self._baseline_length = baseline_length
        self._guard_band = guard_band
        self._threshold = threshold
        self._history: Deque[int] = deque(maxlen=baseline_length + guard_band + 1)

    def update(self, value: int) -> bool:
        self._history.append(value)
        if len(self._history) < self._baseline_length + self._guard_band:
            return False
        history_list = list(self._history)
        baseline = history_list[-(self._guard_band + self._baseline_length) : -self._guard_band]
        mu = mean(baseline)
        sigma = pstdev(baseline)
        z = (value - mu) / max(sigma, 1.0)
        return z >= self._threshold


class CusumDetector:
    """Positive CUSUM detector for persistent mention lifts."""

    def __init__(self, k: float = 1.0, h: float = 5.0) -> None:
        self._k = k
        self._h = h
        self._s_pos = 0.0

    def update(self, value: float, expected: float) -> bool:
        self._s_pos = max(0.0, self._s_pos + value - (expected + self._k))
        return self._s_pos >= self._h


@dataclass
class TrendEngine:
    """Stateful detector coordinator mapping tickers to detector instances."""

    min_authors: int = 3
    min_threads: int = 2
    heads_up_z: float = 2.0
    actionable_z: float = 3.0
    cusum_k: float = 1.0
    cusum_h: float = 5.0
    ears_baseline_len: int = 7
    ears_guard_band: int = 2
    ears_threshold: float = 3.0
    zscore_floor: float = 1.0
    _ears: dict[str, EarsDetector] = field(default_factory=dict, init=False)
    _cusum: dict[str, CusumDetector] = field(default_factory=dict, init=False)

    def process(self, detections: Iterable[DetectionInput]) -> list[AlertEvent]:
        alerts: list[AlertEvent] = []
        for detection in detections:
            alert = self._process_single(detection)
            if alert:
                alerts.append(alert)
        return alerts

    def _process_single(self, detection: DetectionInput) -> AlertEvent | None:
        agg = detection.aggregation
        z = compute_zscore(agg, detection.short_baseline, self.zscore_floor)
        ears_alarm = self._ears_for(agg.ticker).update(agg.mentions)
        cusum_alarm = self._cusum_for(agg.ticker).update(agg.mentions, detection.diurnal_mean)
        hype = hype_score(z, agg.unique_authors, agg.avg_sentiment)

        if not self._passes_guards(agg):
            return None

        tier: str | None = None
        if z >= self.actionable_z and (ears_alarm or cusum_alarm):
            tier = "actionable"
        elif z >= self.heads_up_z:
            tier = "heads-up"
        if tier is None:
            return None

        return AlertEvent(
            ts_alert=agg.ts_utc,
            ticker=agg.ticker,
            tier=tier,
            hype_score=hype,
            zscore=z,
            unique_authors=agg.unique_authors,
            threads_touched=agg.threads_touched,
            avg_sentiment=agg.avg_sentiment,
            price_at_alert=None,
            meta={
                "ears": ears_alarm,
                "cusum": cusum_alarm,
            },
            references=(),
        )

    def _passes_guards(self, agg: MinuteAggregation) -> bool:
        return agg.unique_authors >= self.min_authors and agg.threads_touched >= self.min_threads

    def _ears_for(self, ticker: str) -> EarsDetector:
        if ticker not in self._ears:
            self._ears[ticker] = EarsDetector(
                baseline_length=self.ears_baseline_len,
                guard_band=self.ears_guard_band,
                threshold=self.ears_threshold,
            )
        return self._ears[ticker]

    def _cusum_for(self, ticker: str) -> CusumDetector:
        if ticker not in self._cusum:
            self._cusum[ticker] = CusumDetector(k=self.cusum_k, h=self.cusum_h)
        return self._cusum[ticker]

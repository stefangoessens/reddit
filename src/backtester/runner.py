"""Backtest harness placeholder."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BacktestConfig:
    """Controls time range, tickers, and output destination."""

    start: datetime
    end: datetime
    output_dir: Path


def run_backtest(config: BacktestConfig) -> None:
    """Replay mention + alert streams to compute cohort metrics."""

    raise NotImplementedError("Backtest logic pending implementation")

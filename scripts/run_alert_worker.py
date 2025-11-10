"""Entry point for alert detection worker."""
from __future__ import annotations

import argparse
import asyncio

from trend.worker import run_alert_worker


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the alert detection worker")
    parser.add_argument("--poll-seconds", type=int, default=30, help="Polling interval in seconds")
    args = parser.parse_args()
    asyncio.run(run_alert_worker(args.poll_seconds))

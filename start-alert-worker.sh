#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:/app/src"
cd /app
exec python scripts/run_alert_worker.py --poll-seconds 30

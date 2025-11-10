#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:/app/src"
cd /app
exec python scripts/run_aggregator_continuous.py --window 5 --poll-seconds 60

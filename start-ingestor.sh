#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:/app/src"
cd /app
exec python scripts/run_ingestor.py --tickers data/tickers.csv

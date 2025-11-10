# WSB Hype Radar

Codename for the WallStreetBets hype detection stack described in `docs/PRD.md` and `docs/SPEC.md`.

## Repo Layout

```
docs/               # Product + technical docs
src/                # Python services (ingestor, nlp, price, trend, api, backtester)
web/                # Next.js front-end (Now board, alerts, leaders, backtests)
infra/helm/         # Deployment charts (pending)
tests/              # Python unit/integration suites + fixtures
```

## Getting Started

1. **Python toolchain**
   ```bash
   pyenv shell 3.11
   pipenv install --dev
   ```
2. **Node toolchain**
   ```bash
   corepack enable
   cd web && pnpm install
   ```
3. **Environment** — copy `.env.example` (coming soon) and export credentials for Reddit, Kafka, Redis, and Timescale (see `src/common/config.py`).
4. **Run checks**
   ```bash
   make lint
   make typecheck
   make test
   make web/dev-up
   ```
5. **Database migrations**
   ```bash
   pyenv exec pipenv run alembic upgrade head
   ```
6. **Seed tickers**
   ```bash
   pyenv exec pipenv run python scripts/seed_tickers.py --file data/tickers.csv
   ```
7. **Aggregate mentions**
   ```bash
   pyenv exec pipenv run python scripts/run_aggregator.py --window 5
   ```
8. **Run Reddit ingestion worker**
   ```bash
   pyenv exec pipenv run python scripts/run_ingestor.py --tickers data/tickers.csv
   ```
9. **Run alert worker**
   ```bash
   pyenv exec pipenv run python -m trend.worker
   ```

## Next Steps

- Flesh out the ingestion/NLP/trend services per `docs/SPEC.md`.
- Add Alembic migrations under `infra/` for the Timescale schema.
- Wire the web dashboard to `/v1/trending`, `/v1/alerts/live`, and `/v1/tickers/{sym}` endpoints once the API gateway is implemented.
- Seed `ticker_master` using `scripts/seed_tickers.py` before running ingestion/trend services.
- Run ingestion → aggregation → alert workers sequentially to backfill metrics before enabling the SSE `/v1/alerts/live` stream in the web app.

## Database Migrations

- Config entrypoint: `alembic.ini`
- Scripts + revisions live under `infra/alembic/`
- Create a new revision:
  ```bash
  pyenv exec pipenv run alembic revision -m "describe-change"
  ```

## Data Seeding

- Default universe file: `data/tickers.csv`
- Seed command: `pyenv exec pipenv run python scripts/seed_tickers.py --file data/tickers.csv`

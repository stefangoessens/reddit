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

## AI SDK Copilot (`web/src/app/ai`)

- Copy `web/.env.example` to `web/.env.local` and set `OPENAI_API_KEY` with an OpenAI key that has access to `gpt-4o-mini`.
- From `web/`, run `pnpm dev` and open `http://localhost:3000/ai` to load the chat playground.
- The page uses the [AI SDK getting-started guide](https://ai-sdk.dev/docs/getting-started) verbatim: `useChat` from `@ai-sdk/react` on the client and a streaming `/api/chat` route on the server powered by `streamText` + OpenAI.
- Every question automatically includes the trending table (selected timeframe) plus the latest alert tape so the assistant reasons over the same data visible on the homepage.
- Responses stream token-by-token, so you can stop midway or keep iterating as you explore WallStreetBets hype data.

## Dashboard Notes

- The Now board supports 5m/1h/24h/7d/30d windows; switch using the chips above the table.
- Use the **Save record** button to persist the current leaderboard locally (handy when mention counts fall and you want a receipt). Records live in `localStorage` and you can clear or remove them individually from the sidebar panel.
- Heatboard cards (top 6 tickers) and the sortable table both pull from `/v1/trending` so they stay in sync with the API data described in `docs/SPEC.md`.
- `/alerts` streams the full alert tape, supports tier filtering, and surfaces actionable rates in real time.
- `/ticker/[sym]` pulls minute-level mentions plus impact stats so you can inspect hype vs. returns per ticker.
- `/leaders` calls `/v1/posters/leaderboard` for alpha/win-rate tables; swap metrics with the chips.

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

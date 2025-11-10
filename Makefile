.PHONY: install lint typecheck test format web/dev-up db/migrate

install:
	pyenv exec pipenv install --dev
	corepack enable
	cd web && pnpm install

lint:
	pyenv exec pipenv run ruff check src tests
	cd web && pnpm lint

typecheck:
	pyenv exec pipenv run mypy src
	cd web && pnpm tsc --noEmit

format:
	pyenv exec pipenv run ruff format src tests
	cd web && pnpm format

test:
	pyenv exec pipenv run pytest
	cd web && pnpm test

web/dev-up:
	cd web && pnpm dev

db/migrate:
	pyenv exec pipenv run alembic -c alembic.ini upgrade head

seed/tickers:
	pyenv exec pipenv run python scripts/seed_tickers.py --file data/tickers.csv

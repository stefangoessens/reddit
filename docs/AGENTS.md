# AGENTS.md — Collaboration, Coding Standards, and Playbook

> This document specifies how humans and AI assistants (“agents”) plan, code, test, and ship this project.  
> It is the **entry point** for contributors and tools.  
> See also: [PRD](./PRD.md) • [SPEC](./SPEC.md)

---

## 0) Principles

- **Single source of truth:** Issues and docs drive all work (no orphaned code).  
- **Small, verifiable increments:** Each task ends with runnable code and tests.  
- **Deterministic builds:** Pin versions; same input → same output.  
- **Security by default:** No secrets in code, prompts, or logs.  
- **Explainability:** Every alert is inspectable; every model decision is reproducible.

---

## 1) Roles & Autonomy

- **Human PM/Lead:** Owns roadmap, prioritization, acceptance criteria.  
- **Human Engineers:** Own service boundaries, performance, reliability.  
- **AI Architect Agent:** Translates PRD→SPEC changes; proposes diagrams; flags risks.  
- **AI Coder Agent:** Scaffolds modules/tests; implements pure functions; respects interfaces.  
- **AI Reviewer Agent:** Runs lint/tests, SAST, checks diffs, suggests fixes.  
- **AI Data Agent:** Curates ticker/alias lists; builds label sets; runs backtests.

**Autonomy levels**  
- *L0:* Read‑only suggestions.  
- *L1 (default):* PRs gated by human review.  
- *L2:* May merge docs/tests; code behind flags with approval.  
- *L3:* Release manager (humans only).

---

## 2) Docs Index

- Product requirements: **[PRD](./PRD.md)**  
- Technical design: **[SPEC](./SPEC.md)**  
- Any change to APIs, thresholds, or schemas **must** update the SPEC.

---

## 3) Repository Layout

```
/docs/PRD.md
/docs/SPEC.md
/docs/AGENTS.md
/src/ingestor/...
/src/nlp/...
/src/trend/...
/src/price/...
/src/api/...
/web/...
/infra/helm/...
/tests/unit/...
/tests/integration/...
/tests/fixtures/...
```

---

## 4) Setup & Common Commands

- Python: `pyenv shell 3.11 && pipenv install --dev`
- Node: `corepack enable && pnpm i`
- DB (docker): `docker compose up -d db redis` → `make db/migrate`
- Seed tickers: `python services/nlp/tools/load_tickers.py --source nasdaq`
- Start stack (dev): `docker compose up --build ingest nlp trend price api web`
- Lint: `make lint` (ruff, mypy, eslint, prettier)
- Test: `make test` (pytest + vitest)
- Typecheck FE: `pnpm -C web tsc --noEmit`

---

## 5) Workflow

### 5.1 Plan
- Open a GitHub Issue using `/templates/issue.md` with **Problem**, **Context**, **Acceptance Criteria**, **Test Plan**.
- Label by domain: `ingest`, `nlp`, `trend`, `api`, `ui`, `infra`, `ops`.

### 5.2 Scaffold
- AI Architect drafts module skeleton + interfaces + contract tests.
- AI Coder generates code **only** under `/src/<service>/` and `/tests/`.

### 5.3 Implement
- Prefer **pure functions** for extractors/sentiment/detectors.
- No network calls in unit tests; use fixtures/golden files.
- Secrets from env/Vault; never hardcode.
- Every public function gets tests (happy + edge cases).

### 5.4 Review
- AI Reviewer runs lint, type checks, unit tests, **SAST** (semgrep/bandit), dependency audits.
- Humans review architecture, performance, external API usage.

### 5.5 Ship
- Trunk‑based development; feature flags for risky paths.
- Conventional Commits; semantic versioning on API.
- Blue/green deploys on API; rollbacks documented.

---

## 6) Coding Standards

### Python (backend)
- Python ≥3.11; **ruff** for lint; **mypy --strict**; Google‑style docstrings with examples.
- Dependency injection for services; no hidden globals.
- Logging via `structlog` in JSON; include `trace_id`; no PII.

### TypeScript (web)
- TS strict; ESLint + Prettier; SWR/React Query for data fetching.
- OpenAPI‑generated clients; avoid ad‑hoc fetch.
- Accessibility first; avoid heavy chart libs unless justified.

### SQL
- Explicit types & constraints; PKs on (ticker, ts) for time series.
- Migrations via Alembic (or Goose/Atlas); always include rollback.

### Prompts / Agent I/O
- Provide **Context**, **Constraints**, **Acceptance Criteria**, **Interfaces**.
- Supply **fixtures** and **expected outputs** up front.
- Request diff‑friendly output for large changes.

---

## 7) Definition of Done

- Code + tests merged to `main`; CI green.
- Observability hooks added (metrics/logs).
- Feature flag wired (if applicable).
- Docs updated: **[SPEC](./SPEC.md)** & READMEs.
- Security checklist passed (below).

---

## 8) Security & Compliance Checklist

- [ ] No secrets in code, prompts, or configs; Vault/KMS used.  
- [ ] Rate‑limits & retries implemented; backoff on 429/5xx.  
- [ ] Logs are PII‑free; Reddit policies respected.  
- [ ] Market‑data display mode (delayed vs real‑time) enforced by flag.  
- [ ] Third‑party licenses reviewed/recorded.

---

## 9) Testing Playbook

- **Unit:** function‑level; ≥80% coverage on `nlp` and `trend`.  
- **Property:** stoplist/regex fuzz; detector monotonicity.  
- **Integration:** ingest→parse→alert E2E with fixtures.  
- **Load:** 10× event rate soak; alert lag budget < 2m.  
- **Backtests:** deterministic with fixed seeds; artifacts saved under `/artifacts`.

---

## 10) Good vs Bad Agent Requests

**Good**
```
Context: Implement CUSUM in /src/trend/cusum.py.
Constraints: Pure function; numpy‑based; no I/O.
Acceptance: tests/test_cusum.py pass; docstring explains k/h params.
Interface:
  def cusum_pos(x: np.ndarray, k: float, h: float) -> np.ndarray: ...
```

**Bad**
```
“Detect spikes quickly in whatever way.”
```

---

## 11) Operational Runbooks

- **Ingestion Lag:** If `ingest_lag_seconds > 90`, scale consumers, check 429s, enable backoff.  
- **Alert Storm:** Verify guards (authors, threads); temporarily raise thresholds via flag.  
- **Data Provider Outage:** Switch to delayed feed; queue mentions; backfill when restored.

---

## 12) Communication & PR Hygiene

- Conventional Commits: `feat:`, `fix:`, `perf:`, `refactor:`, `test:`, `chore:`, `docs:`.  
- PR template includes **Problem, Approach, Tests, Screens, Rollout, Risks**.  
- Keep PRs < 400 LOC; split large changes; stage behind flags.

---

## 13) Ethics

- We surface **community chatter**, not advice.  
- We avoid manipulative amplification; guard against brigading/botting.  
- Transparency: each alert links to sources and shows detection math.

---

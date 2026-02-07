# Repository Guidelines

## Purpose and Scope
- Service: CP-first wallet ledger for agentic commerce.
- Ledger model: strict double-entry accounting, append-only journal, derived balances from projection table.
- Scope: single tenant, single currency (USD default) for v1.

## Core Invariants (Non-Negotiable)
- Journal entries are append-only and immutable.
- Every transaction has at least 2 entries.
- Sum of all entries for a transaction equals zero.
- Idempotency key is mandatory on every write API.
- Same idempotency key with different payload must return `409`.

## Technology Rules
- Always use `uv` for dependency and execution workflows.
- Do not use `pip` commands in docs/scripts/contributing examples.
- Python 3.12+ with FastAPI + PostgreSQL.

## Project Layout
- `src/wallet_service/`: app code (API, auth, ledger, DB, observability).
- `migrations/`: ordered SQL migrations.
- `tests/`: unit, integration, and reliability suites.
- `load/k6/`: load, spike, soak, and resiliency scenarios.
- `deploy/doks/`: Helm chart and observability manifests.
- `deploy/droplet/`: docker-compose runtime fallback.

## API and Auth Contracts
- Endpoints: `/v1/wallets`, `/v1/transfers`, `/v1/adjustments`, `/v1/transactions/{id}`, `/v1/health`, `/v1/ready`.
- Auth: service-to-service JWT with scopes.
- Required claims: `sub`, `aud`, `scope`, `exp`.
- Required scopes:
  - `wallet:read`
  - `wallet:write`
  - `wallet:admin`

## CAP and Reliability Expectations
- Write-path is CP-first and fail-closed on DB unavailability.
- No optimistic acceptance of writes during partitions.
- Reads default to DB-backed consistency; stale reads disabled by default.
- Use serializable transaction boundaries for ledger mutation paths.

## Migration and Schema Rules
- Migrations are append-only SQL files with sortable names (`NNN_description.sql`).
- Never alter old migration files after merge.
- Add new migration for every schema change.
- Keep trigger/constraint logic in DB for balance/invariant protection.

## Observability Standards
- OpenTelemetry traces/metrics/logs enabled by default.
- OTLP exports target Alloy.
- Metrics exposed to Prometheus; logs shipped to Loki.
- Log fields should include trace and business correlation IDs where available.

## Test and Validation Gates
- Unit tests: invariants, auth, validation.
- Integration tests: end-to-end transfers, idempotency behavior, projection correctness.
- Reliability tests: DB-failure fail-closed behavior.
- Load tests (k6): smoke, baseline, spike, soak, partition-resiliency.
- Baseline objective: sustain 1k tx/s and p95 write latency under 150ms.

## Commands
- Install: `uv sync --extra dev`
- Migrate/bootstrap: `./scripts/bootstrap_db.sh`
- Run service: `./scripts/run_dev.sh`
- Test suite: `./scripts/test.sh`
- Load suite: `./scripts/run_load_suite.sh`
- Resiliency load: `./scripts/run_resiliency_suite.sh`

## Deployment
- Primary: DigitalOcean Kubernetes (DOKS) using Helm chart in `deploy/doks/helm/wallet-service`.
- Secondary: Docker Compose in `deploy/droplet/docker-compose.yml`.
- Observability stack definitions are under `deploy/doks/observability`.

## Incident and Debugging Runbook (Quick)
- Check `/v1/ready` for DB and migration health.
- Inspect logs for idempotency conflicts and DB connection failures.
- Validate journal/projection consistency using `/v1/wallets/{id}/balance/audit`.
- During outages, confirm write APIs return 503 rather than accepting state changes.

# Contributing

## Development Setup

1. Install dependencies:
```bash
uv sync --extra dev
```

2. Start local PostgreSQL and bootstrap schema:
```bash
./scripts/bootstrap_db.sh
```

3. Run service:
```bash
./scripts/run_dev.sh
```

## Development Rules

- Use `uv` for dependency and command execution.
- Keep ledger invariants intact (double-entry, append-only journal).
- Write APIs must remain idempotent and fail-closed on DB outage.
- Add or update tests for behavior changes.

## Pull Request Process

1. Create a focused branch.
2. Run checks before opening PR:
```bash
uv run ruff check src tests scripts
uv run pytest
```
3. Include in PR description:
- What changed
- Why it changed
- How it was validated
- Any migration or deployment impact

## Commit Guidelines

Use concise, imperative commits, for example:
- `Add conflict handling for idempotency mismatch`
- `Add resiliency load test scenario`

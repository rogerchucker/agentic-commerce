#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-wallet_service}"
DB_URL="${DATABASE_URL:-postgresql://raj@localhost:5432/${DB_NAME}}"

psql -h localhost -U raj -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || psql -h localhost -U raj -d postgres -c "CREATE DATABASE ${DB_NAME}"

uv run python - <<'PY'
from wallet_service.db.migrations import apply_migrations
apply_migrations()
print("migrations applied")
PY

echo "Database bootstrapped at ${DB_URL}"

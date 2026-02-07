#!/usr/bin/env bash
set -euo pipefail

# Seed wallets against a DOKS-deployed wallet-service via a temporary port-forward.
#
# Usage:
#   COUNT=3000 ./scripts/seed_wallets_doks.sh
#
# Environment overrides:
# - NAMESPACE (default: wallet-prod)
# - SERVICE   (default: wallet-service)
# - LOCAL_PORT (default: 18080)
# - REMOTE_PORT (default: 8080)
# - BASE_URL (default: http://127.0.0.1:${LOCAL_PORT})
# - JWT_SECRET (default: read from k8s secret wallet-service-secrets)
# - JWT_AUDIENCE (default: agentic-commerce)
# - COUNT (default: 3000)
# - START (default: 1)

NAMESPACE="${NAMESPACE:-wallet-prod}"
SERVICE="${SERVICE:-wallet-service}"
LOCAL_PORT="${LOCAL_PORT:-18080}"
REMOTE_PORT="${REMOTE_PORT:-8080}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${LOCAL_PORT}}"
JWT_AUDIENCE="${JWT_AUDIENCE:-agentic-commerce}"
COUNT="${COUNT:-3000}"
START="${START:-1}"

if [[ -z "${JWT_SECRET:-}" ]]; then
  JWT_SECRET="$(kubectl -n "$NAMESPACE" get secret wallet-service-secrets -o jsonpath='{.data.JWT_SECRET}' | base64 --decode)"
fi

kubectl -n "$NAMESPACE" port-forward "svc/${SERVICE}" "${LOCAL_PORT}:${REMOTE_PORT}" >/tmp/wallet_seed_pf.log 2>&1 &
PF_PID=$!
cleanup() { kill "$PF_PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

for _ in $(seq 1 60); do
  if curl -fsS "${BASE_URL}/v1/ready" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

curl -fsS "${BASE_URL}/v1/ready" >/dev/null 2>&1 || {
  echo "port-forward not ready; see /tmp/wallet_seed_pf.log" >&2
  exit 1
}

BASE_URL="$BASE_URL" JWT_AUDIENCE="$JWT_AUDIENCE" JWT_SECRET="$JWT_SECRET" \
  uv run python scripts/seed_wallets.py \
    --base-url "$BASE_URL" \
    --count "$COUNT" \
    --start "$START" \
    --jwt-secret "$JWT_SECRET" \
    --jwt-audience "$JWT_AUDIENCE"


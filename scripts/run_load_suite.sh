#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
export BASE_URL

mkdir -p load/reports

k6 run --summary-export load/reports/smoke.json load/k6/smoke.js
k6 run --summary-export load/reports/baseline.json load/k6/baseline.js
k6 run --summary-export load/reports/spike.json load/k6/spike.js
k6 run --summary-export load/reports/soak.json load/k6/soak.js

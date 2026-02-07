#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
export BASE_URL

mkdir -p load/reports

echo "Start resiliency test. In another shell, execute fault injection (db restart/network block) during run."
k6 run --summary-export load/reports/resiliency_partition.json load/k6/resiliency_partition.js

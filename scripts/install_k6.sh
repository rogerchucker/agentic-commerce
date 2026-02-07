#!/usr/bin/env bash
set -euo pipefail
if command -v k6 >/dev/null 2>&1; then
  echo "k6 already installed: $(k6 version | head -n1)"
  exit 0
fi

if command -v brew >/dev/null 2>&1; then
  brew install k6
  exit 0
fi

echo "Install k6 manually from https://grafana.com/docs/k6/latest/set-up/install-k6/"
exit 1

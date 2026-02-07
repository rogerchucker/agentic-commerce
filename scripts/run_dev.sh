#!/usr/bin/env bash
set -euo pipefail
uv run uvicorn wallet_service.main:app --host 0.0.0.0 --port 8080 --reload

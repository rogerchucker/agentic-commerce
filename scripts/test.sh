#!/usr/bin/env bash
set -euo pipefail
uv run pytest tests/unit tests/integration tests/reliability

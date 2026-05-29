#!/usr/bin/env bash
# Runs the full automated defense suite: business logic + every fix the
# student was expected to make (nginx config, schemas, routers, typos).
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d postgres >/dev/null

echo "==> Running ALL automated defense tests..."
pytest fastapi/tests -v

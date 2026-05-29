#!/usr/bin/env bash
# Runs ONLY the inventory / capacity enforcement business-logic suite.
# Requires Postgres reachable on the URL in fastapi/.env (or DATABASE_URL).
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d postgres >/dev/null

echo "==> Running inventory/capacity business-logic tests..."
pytest fastapi/tests/test_business_logic_inventory.py -v

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}== Sistema de Reservas LOUD :: Exam test runner ==${NC}"
echo

usage() {
    cat <<EOF
Usage: $0 [target]

Targets:
  all          Run every exam test (default)
  inventory    Run only the inventory / capacity business-logic tests
  fixes        Run only the planted-bug fix verification tests
  events       Run only the original API smoke tests
  local        Force local execution (skip docker compose)

The script auto-detects whether the fastapi container is running:
  * If 'docker compose ps fastapi' reports a running container, tests run inside it.
  * Otherwise it falls back to a local 'pytest' invocation from ./fastapi.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

TARGET="${1:-all}"

case "$TARGET" in
    all)        TEST_ARGS="tests/" ;;
    inventory)  TEST_ARGS="tests/test_inventory.py" ;;
    fixes)      TEST_ARGS="tests/test_exam_fixes.py" ;;
    events)     TEST_ARGS="tests/test_events.py" ;;
    local)      TEST_ARGS="tests/"; FORCE_LOCAL=1 ;;
    *)
        echo -e "${RED}Unknown target: $TARGET${NC}"
        usage
        exit 2
        ;;
esac

run_in_container() {
    echo -e "${YELLOW}Running inside the 'fastapi' container...${NC}"
    docker compose exec -T fastapi pytest -vv $TEST_ARGS
}

run_locally() {
    echo -e "${YELLOW}Running locally with pytest...${NC}"
    if ! command -v pytest >/dev/null 2>&1; then
        echo -e "${RED}pytest not found in PATH. Either install fastapi/requirements.txt or start docker compose up -d fastapi.${NC}"
        exit 3
    fi
    (cd fastapi && pytest -vv $TEST_ARGS)
}

if [[ "${FORCE_LOCAL:-0}" == "1" ]]; then
    run_locally
elif command -v docker >/dev/null 2>&1 && docker compose ps fastapi 2>/dev/null | grep -q "Up\|running"; then
    run_in_container
else
    run_locally
fi

echo
echo -e "${GREEN}== Done ==${NC}"

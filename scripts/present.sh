#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  printf 'Run ./scripts/setup.sh first.\n' >&2
  exit 1
fi
(cd frontend && npm run build)
export PYTHONPATH="$PWD/backend"
printf '\nPlantGraph Twin presentation: http://127.0.0.1:8000\nAPI documentation: http://127.0.0.1:8000/docs\n\n'
exec .venv/bin/uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" --no-access-log

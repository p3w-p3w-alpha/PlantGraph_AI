#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { printf 'Install uv: https://docs.astral.sh/uv/\n' >&2; exit 1; }
command -v npm >/dev/null || { printf 'Install Node.js 22+ and npm.\n' >&2; exit 1; }
uv python install 3.12
if [[ ! -x .venv/bin/python ]]; then uv venv --python 3.12 .venv; fi
uv pip install --python .venv/bin/python -r backend/requirements.lock.txt
(cd frontend && npm ci --no-audit --no-fund)
if [[ ! -f .env ]]; then cp .env.example .env; chmod 600 .env; fi
printf '\nReady. Configure GOOGLE_API_KEY and GEMMA_MODEL in .env, then ./scripts/present.sh\n'

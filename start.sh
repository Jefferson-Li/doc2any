#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ ! -x .venv/bin/uvicorn ]]; then
  python3 -m venv .venv
  .venv/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
fi

export DOC2ANY_ENV="${DOC2ANY_ENV:-development}"
PORT="${DOC2ANY_PORT:-8000}"
echo "Doc2Any (${DOC2ANY_ENV}) → http://localhost:${PORT}"
exec .venv/bin/uvicorn app.main:app --reload --host "${DOC2ANY_HOST:-0.0.0.0}" --port "${PORT}"

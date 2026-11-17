#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if [ ! -x ".venv/bin/python" ]; then
  echo "[i] Creating a virtual environment..."
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

if ! python -c "import importlib.metadata as m; m.version('birthdex')" >/dev/null 2>&1; then
  echo "[i] Installing BirthDex and dependencies (first run only)..."
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -e .
fi

export PORT="${PORT:-5002}"
export HOST="${HOST:-0.0.0.0}"
export THREADS="${THREADS:-8}"

echo
echo "  BirthDex on http://localhost:${PORT}"
echo "  Health:    http://localhost:${PORT}/health"
echo

exec birthdex --host "$HOST" --port "$PORT" --threads "$THREADS"

#!/usr/bin/env bash
# dev.sh — development mode
# Starts uvicorn (--reload) on :8000 and Vite dev server on :5173 in parallel.
# Vite proxies /ws and /frames to the backend automatically.
# Ctrl+C kills both processes.
#
# Supports: macOS and Ubuntu/Linux.
# On Ubuntu: run ./install.sh once before first use.
#
# Usage:
#   ./dev.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer venv python if install.sh was run
PYTHON="python3"
if [[ -f "$SCRIPT_DIR/.venv/bin/python3" ]]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python3"
fi

# Install frontend deps if node_modules is missing.
if [[ ! -d "$SCRIPT_DIR/frontend/node_modules" ]]; then
  echo "==> Installing frontend dependencies…"
  cd "$SCRIPT_DIR/frontend" && npm install --silent && cd "$SCRIPT_DIR"
fi

echo ""
echo "  Vallis Simulacri — dev mode"
echo "  Backend:  http://localhost:8000  (uvicorn --reload)"
echo "  Frontend: http://localhost:5173  (Vite HMR)"
echo "  Press Ctrl+C to stop both."
echo ""

cleanup() {
  echo ""
  echo "Stopping backend and frontend…"
  kill "$UVICORN_PID" "$VITE_PID" 2>/dev/null || true
  wait "$UVICORN_PID" "$VITE_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

"$PYTHON" -m uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  --reload-dir backend \
  --reload-dir core \
  --reload-dir vision \
  --reload-dir catalog \
  --reload-dir data &
UVICORN_PID=$!

cd "$SCRIPT_DIR/frontend"
npm run dev &
VITE_PID=$!
cd "$SCRIPT_DIR"

wait

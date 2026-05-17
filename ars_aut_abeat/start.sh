#!/usr/bin/env bash
# start.sh — production mode
# Builds the React frontend (if dist/ is missing or --build is passed),
# then starts the FastAPI server which serves everything on :8000.
#
# Usage:
#   ./start.sh           — start (skips build if dist/ already exists)
#   ./start.sh --build   — force rebuild before starting
#   ./start.sh --port 9000

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8000
REBUILD=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --build) REBUILD=1; shift ;;
    --port)  PORT="$2"; shift 2 ;;
    *)       echo "Unknown option: $1"; exit 1 ;;
  esac
done

DIST="$SCRIPT_DIR/frontend/dist"

if [[ $REBUILD -eq 1 || ! -d "$DIST" ]]; then
  echo "==> Building frontend…"
  cd "$SCRIPT_DIR/frontend"
  npm install --silent
  npm run build
  cd "$SCRIPT_DIR"
  echo "==> Build complete: $DIST"
fi

echo ""
echo "  Vallis Simulacri — gallery installation"
echo "  http://localhost:$PORT"
echo "  Press Ctrl+C to stop."
echo ""

# Trap signals so Ctrl+C shuts down cleanly.
trap 'echo ""; echo "Stopping…"; kill $UVICORN_PID 2>/dev/null; exit 0' INT TERM

python3 -m uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port "$PORT" &
UVICORN_PID=$!

wait $UVICORN_PID

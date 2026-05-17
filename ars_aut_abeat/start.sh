#!/usr/bin/env bash
# start.sh — production launcher for Vallis Simulacri
#
# Designed for a vertically mounted 65-inch display (portrait orientation).
# Opens Brave in kiosk mode after the server is ready — no URL bar, no chrome.
#
# Usage:
#   ./start.sh              — start (skips rebuild if dist/ already exists)
#   ./start.sh --build      — force rebuild before starting
#   ./start.sh --port 9000
#   ./start.sh --no-browser — headless / server only (no Brave window)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8000
REBUILD=0
OPEN_BROWSER=1

while [[ $# -gt 0 ]]; do
  case $1 in
    --build)      REBUILD=1;      shift ;;
    --port)       PORT="$2";      shift 2 ;;
    --no-browser) OPEN_BROWSER=0; shift ;;
    *)            echo "Unknown option: $1"; exit 1 ;;
  esac
done

DIST="$SCRIPT_DIR/frontend/dist"

if [[ $REBUILD -eq 1 || ! -d "$DIST" ]]; then
  echo "==> Building frontend…"
  cd "$SCRIPT_DIR/frontend"
  npm install --silent
  npm run build
  cd "$SCRIPT_DIR"
  echo "==> Build complete."
fi

echo ""
echo "  Vallis Simulacri — gallery installation"
echo "  Display: 65-inch portrait TV"
echo "  http://localhost:$PORT"
echo "  Press Ctrl+C to stop."
echo ""

trap 'echo ""; echo "Stopping…"; kill $UVICORN_PID 2>/dev/null; pkill -f "brave.*kiosk" 2>/dev/null; exit 0' INT TERM

python3 -m uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port "$PORT" &
UVICORN_PID=$!

# Wait until the server is accepting connections before opening the browser.
if [[ $OPEN_BROWSER -eq 1 ]]; then
  echo "==> Waiting for server…"
  until curl -s "http://localhost:$PORT" > /dev/null 2>&1; do
    sleep 0.5
  done
  echo "==> Opening Brave in kiosk mode…"
  # --kiosk: true fullscreen, no browser chrome, no address bar, no cursor shortcuts.
  # --app: isolates the window so Cmd+T / Cmd+L are suppressed.
  # --start-fullscreen: ensures fullscreen even if a previous session wasn't.
  # --disable-pinch: prevents accidental zoom on touch/trackpad.
  open -a "Brave Browser" --args \
    --kiosk \
    --app="http://localhost:$PORT" \
    --start-fullscreen \
    --disable-pinch \
    --noerrdialogs \
    --disable-infobars \
    2>/dev/null || \
  open -a "Google Chrome" --args \
    --kiosk \
    --app="http://localhost:$PORT" \
    --start-fullscreen \
    --disable-pinch \
    --noerrdialogs \
    --disable-infobars \
    2>/dev/null || \
  echo "  Could not open browser automatically — open http://localhost:$PORT manually."
fi

wait $UVICORN_PID

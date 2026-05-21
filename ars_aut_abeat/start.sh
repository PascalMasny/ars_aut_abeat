#!/usr/bin/env bash
# start.sh — production launcher for Vallis Simulacri
#
# Designed for a vertically mounted 65-inch display (portrait orientation).
# Opens Brave (or Chrome/Chromium) in kiosk mode after the server is ready.
#
# Supports: macOS and Ubuntu/Linux.
# On Ubuntu: run ./install.sh once before first use.
#
# Usage:
#   ./start.sh              — start (skips rebuild if dist/ already exists)
#   ./start.sh --build      — force rebuild before starting
#   ./start.sh --port 9000
#   ./start.sh --no-browser — headless / server only (no browser window)

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

# ─── Python: prefer venv if install.sh was run ───────────────────────────────
PYTHON="python3"
if [[ -f "$SCRIPT_DIR/.venv/bin/python3" ]]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python3"
fi

# ─── Frontend build ──────────────────────────────────────────────────────────
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

# ─── Cleanup on exit ─────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "Stopping…"
  kill "$UVICORN_PID" 2>/dev/null || true
  # Kill kiosk browser (both macOS and Linux process names)
  pkill -f "brave.*kiosk"      2>/dev/null || true
  pkill -f "chrome.*kiosk"     2>/dev/null || true
  pkill -f "chromium.*kiosk"   2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

# ─── Start server ────────────────────────────────────────────────────────────
"$PYTHON" -m uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port "$PORT" &
UVICORN_PID=$!

# ─── Open browser in kiosk mode ──────────────────────────────────────────────
if [[ $OPEN_BROWSER -eq 1 ]]; then
  echo "==> Waiting for server…"
  until curl -s "http://localhost:$PORT" > /dev/null 2>&1; do
    # Check server didn't die immediately
    if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
      echo "ERROR: Server exited unexpectedly." >&2
      exit 1
    fi
    sleep 0.5
  done
  echo "==> Opening browser in kiosk mode…"

  OS="$(uname -s)"

  if [[ "$OS" == "Darwin" ]]; then
    # ── macOS ──────────────────────────────────────────────────────────────
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
    echo "  Could not open browser — open http://localhost:$PORT manually."

  else
    # ── Linux / Ubuntu ─────────────────────────────────────────────────────
    # Chromium-based browsers accept the same flags on Linux but launch directly
    # (no 'open -a' wrapper). Try Brave, Chrome, Chromium in order.
    KIOSK_ARGS=(
      "--kiosk"
      "--app=http://localhost:$PORT"
      "--start-fullscreen"
      "--disable-pinch"
      "--noerrdialogs"
      "--disable-infobars"
      "--disable-session-crashed-bubble"
      "--disable-infobars"
    )

    # On Wayland sessions force X11 mode so kiosk geometry works reliably.
    if [[ "${XDG_SESSION_TYPE}" == "wayland" ]]; then
      KIOSK_ARGS+=("--ozone-platform=x11")
    fi

    BROWSER=""
    for b in brave-browser google-chrome chromium-browser chromium; do
      if command -v "$b" &>/dev/null; then
        BROWSER="$b"
        break
      fi
    done

    if [[ -n "$BROWSER" ]]; then
      "$BROWSER" "${KIOSK_ARGS[@]}" 2>/dev/null &
    else
      echo "  No browser found."
      echo "  Install Brave: sudo apt-get install brave-browser"
      echo "  Or open http://localhost:$PORT manually."
    fi
  fi
fi

wait $UVICORN_PID

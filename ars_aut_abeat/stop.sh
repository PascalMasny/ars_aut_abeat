#!/usr/bin/env bash
# stop.sh — kill all running Vallis Simulacri processes.

pkill -f "uvicorn backend.main:app" 2>/dev/null && echo "Stopped uvicorn."    || echo "uvicorn not running."
pkill -f "vite"                     2>/dev/null && echo "Stopped Vite."       || echo "Vite not running."
pkill -f "brave.*kiosk"             2>/dev/null && echo "Stopped Brave."      || true
pkill -f "chrome.*kiosk"            2>/dev/null && echo "Stopped Chrome."     || true
pkill -f "chromium.*kiosk"          2>/dev/null && echo "Stopped Chromium."   || true

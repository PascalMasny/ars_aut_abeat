#!/usr/bin/env bash
# stop.sh — kill any running uvicorn and Vite processes for this project.

pkill -f "uvicorn backend.main:app" 2>/dev/null && echo "Stopped uvicorn." || echo "uvicorn not running."
pkill -f "vite"                     2>/dev/null && echo "Stopped Vite."    || echo "Vite not running."

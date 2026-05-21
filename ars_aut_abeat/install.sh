#!/usr/bin/env bash
# install.sh — Ubuntu/Debian setup for Vallis Simulacri
#
# Run once after cloning the repo. Creates a Python venv, installs all
# dependencies, and builds the frontend.
#
# Requirements: Ubuntu 22.04+ / Debian 12+, sudo access
#
# Usage:
#   ./install.sh              — install everything
#   ./install.sh --no-browser — skip browser (Brave) installation

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

INSTALL_BROWSER=1
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-browser) INSTALL_BROWSER=0; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ─── 1. OS check ─────────────────────────────────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "ERROR: install.sh is for Ubuntu/Debian only."
  echo "On macOS: pip install -r requirements.txt && cd frontend && npm install"
  exit 1
fi
if ! command -v apt-get &>/dev/null; then
  echo "ERROR: apt-get not found. This script targets Debian/Ubuntu only."
  exit 1
fi

echo ""
echo "  Vallis Simulacri — Ubuntu installer"
echo "  ======================================"
echo ""

# ─── 2. System packages ───────────────────────────────────────────────────────
echo "==> Installing system packages…"
sudo apt-get update -qq
sudo apt-get install -y \
  python3 python3-pip python3-venv python3-dev \
  libgl1-mesa-glx libglib2.0-0 libgthread-2.0-0 \
  libsm6 libxext6 libxrender-dev libxcb1 \
  libfontconfig1 libdbus-1-3 \
  curl wget git build-essential \
  v4l-utils

# Camera group — allows access to /dev/video* without sudo
if ! groups "$USER" | grep -qw video; then
  echo "==> Adding $USER to 'video' group (camera access)…"
  sudo usermod -aG video "$USER"
  echo "    NOTE: Log out and back in for group change to take effect."
fi

# ─── 3. Node.js 20 ───────────────────────────────────────────────────────────
NODE_OK=0
if command -v node &>/dev/null; then
  NODE_VER="$(node -v | cut -d. -f1 | tr -d v)"
  [[ "$NODE_VER" -ge 18 ]] && NODE_OK=1
fi

if [[ $NODE_OK -eq 0 ]]; then
  echo "==> Installing Node.js 20 via NodeSource…"
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
else
  echo "==> Node.js $(node -v) already installed — skipping."
fi

# ─── 4. Python venv ──────────────────────────────────────────────────────────
echo "==> Setting up Python virtual environment…"

# MediaPipe 0.10 supports Python 3.8–3.12. Prefer 3.12 if available.
PYTHON="python3"
for py in python3.12 python3.11 python3.10 python3; do
  if command -v "$py" &>/dev/null; then
    PYTHON="$py"
    break
  fi
done

PY_VERSION="$($PYTHON --version)"
echo "    Using $PY_VERSION ($PYTHON)"

if [[ ! -d ".venv" ]]; then
  "$PYTHON" -m venv .venv
  echo "    Created .venv"
else
  echo "    .venv already exists — updating packages."
fi

.venv/bin/pip install --upgrade pip --quiet
echo "==> Installing Python dependencies…"
.venv/bin/pip install -r requirements.txt

# ─── 5. Frontend ─────────────────────────────────────────────────────────────
echo "==> Installing frontend dependencies…"
cd frontend && npm install --silent && cd ..

# ─── 6. Brave Browser (optional, kiosk) ──────────────────────────────────────
if [[ $INSTALL_BROWSER -eq 1 ]]; then
  if ! command -v brave-browser &>/dev/null && \
     ! command -v google-chrome &>/dev/null && \
     ! command -v chromium-browser &>/dev/null; then
    echo "==> Installing Brave Browser…"
    sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
      https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64] \
https://brave-browser-apt-release.s3.brave.com/ stable main" \
      | sudo tee /etc/apt/sources.list.d/brave-browser-release.list
    sudo apt-get update -qq
    sudo apt-get install -y brave-browser
  else
    echo "==> Browser already installed — skipping Brave."
  fi
else
  echo "==> Skipping browser installation (--no-browser)."
fi

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "  Installation complete!"
echo ""
echo "  Start the installation:  ./start.sh"
echo "  Development mode:        ./dev.sh"
echo "  Stop all services:       ./stop.sh"
echo ""
echo "  NOTE: MediaPipe models (~40 MB) download automatically on first startup."
if groups "$USER" | grep -qw video; then
  true
else
  echo "  NOTE: Log out and back in for camera (video group) access."
fi
echo ""

#!/usr/bin/env bash

set -e

echo "=== BLACKHAVEN FRAME INSTALLER ==="

BASE_DIR="$HOME/.blackhaven"
TOOLS_DIR="$BASE_DIR/tools"
CONFIG_DIR="$BASE_DIR/config"
LOG_DIR="$BASE_DIR/logs"

BLACKHAVEN_LOCAL="$HOME/BlackHaven"
DEADNS_LOCAL="$HOME/DeadNS"

mkdir -p "$TOOLS_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

echo "[+] Installing dependencies..."

sudo apt update
sudo apt install -y git nodejs npm python3 python3-pip python3-venv

echo "[+] Installing BlackHaven..."

if [ ! -d "$TOOLS_DIR/blackhaven" ]; then
    git clone "$BLACKHAVEN_REPO" "$TOOLS_DIR/blackhaven"
else
    echo "[✓] BlackHaven already installed"
fi

echo "[+] Installing DeadNS..."

if [ ! -d "$TOOLS_DIR/deadns" ]; then
    echo "[+] Copying DeadNS from local directory..."
    cp -r "$DEADNS_LOCAL" "$TOOLS_DIR/deadns"
else
    echo "[✓] DeadNS already installed"
fi

echo "[+] Installing dnsReaper..."

DNSREAPER_REPO="https://github.com/punk-security/dnsReaper.git"
DNSREAPER_DIR="$TOOLS_DIR/dnsreaper"
DNSREAPER_VENV="$DNSREAPER_DIR/.venv"

if [ ! -d "$DNSREAPER_DIR" ]; then
    git clone "$DNSREAPER_REPO" "$DNSREAPER_DIR"
else
    echo "[✓] dnsReaper repo already present"
fi

# Prefer a local venv to avoid "externally-managed-environment" errors.
if [ ! -d "$DNSREAPER_VENV" ]; then
    echo "[+] Creating dnsReaper venv..."
    if ! python3 -m venv "$DNSREAPER_VENV"; then
        echo "[!] Failed to create venv for dnsReaper"
    fi
fi

if [ -d "$DNSREAPER_VENV" ]; then
    echo "[+] Installing dnsReaper dependencies into venv..."
    "$DNSREAPER_VENV/bin/pip" install --upgrade pip
    "$DNSREAPER_VENV/bin/pip" install -r "$DNSREAPER_DIR/requirements.txt"
else
    # Fallback: use pipx if it is available on the system.
    if command -v pipx >/dev/null 2>&1; then
        echo "[!] Falling back to pipx for dnsReaper..."
        pipx install --force "$DNSREAPER_DIR"
    else
        echo "[!] dnsReaper install failed: no venv and pipx not available"
        echo "    Install pipx or fix Python venv support, then re-run installer."
    fi
fi

echo "[+] Installation complete."
echo "Run with: npm start"

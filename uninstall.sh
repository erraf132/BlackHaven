#!/usr/bin/env bash
set -euo pipefail

python3 -m pip uninstall -y blackhaven || true

if [ -d "$HOME/.blackhaven" ]; then
  rm -rf "$HOME/.blackhaven"
fi

echo "Uninstalled BlackHaven."

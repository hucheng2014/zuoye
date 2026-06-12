#!/usr/bin/env bash
# setup-macos.sh — Initialize zuoye workspace on macOS
# Usage: source ~/zuoye/tools/setup-macos.sh
set -euo pipefail

export ZUOYE_ROOT="${ZUOYE_ROOT:-$HOME/zuoye}"

echo "==> ZUOYE_ROOT=$ZUOYE_ROOT"

# Check Docker Desktop
if ! command -v docker &>/dev/null; then
  echo "WARNING: Docker not found. Install Docker Desktop for Mac:"
  echo "  https://docs.docker.com/desktop/install/mac-install/"
else
  echo "==> Docker: $(docker --version)"
  if ! docker info &>/dev/null; then
    echo "WARNING: Docker daemon not running. Start Docker Desktop."
  fi
fi

# Check Homebrew
if ! command -v brew &>/dev/null; then
  echo "WARNING: Homebrew not found. Install:"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
else
  echo "==> Homebrew: $(brew --version | head -1)"
fi

# Check Python3
if ! command -v python3 &>/dev/null; then
  echo "WARNING: python3 not found. Install via brew: brew install python3"
else
  echo "==> Python: $(python3 --version)"
fi

# Check Node.js
if ! command -v node &>/dev/null; then
  echo "WARNING: node not found. Install via brew or nvm."
else
  echo "==> Node: $(node --version)"
fi

echo ""
echo "==> Environment ready. Project root: $ZUOYE_ROOT"
echo "==> Run 'docker compose up' in subprojects to start services."

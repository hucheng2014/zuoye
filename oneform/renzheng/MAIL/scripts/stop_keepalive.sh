#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT/MAIL/runs/keepalive.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No Starshot Keepalive process running (no PID file found)."
  exit 0
fi

PID="$(cat "$PID_FILE" || true)"
if [[ -z "$PID" ]]; then
  echo "Empty PID file. Removing it."
  rm -f "$PID_FILE"
  exit 0
fi

if kill -0 "$PID" 2>/dev/null; then
  echo "Stopping Starshot Keepalive (PID $PID)..."
  kill "$PID"
  
  # Wait for it to stop
  for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
      break
    fi
    sleep 0.5
  done
  
  if kill -0 "$PID" 2>/dev/null; then
    echo "Force killing PID $PID..."
    kill -9 "$PID"
  fi
  echo "Stopped."
else
  echo "Process with PID $PID is not running."
fi

rm -f "$PID_FILE"

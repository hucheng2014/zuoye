#!/bin/bash
set -e

echo "[agent] Waiting for browser CDP at ${CDP_ENDPOINT}..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -H "Host: localhost:9222" "${CDP_ENDPOINT}/json/version" > /dev/null 2>&1; then
        echo "[agent] ✓ Browser CDP is ready!"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[agent] ERROR: Browser CDP not ready after ${MAX_WAIT}s"
    exit 1
fi

echo "[agent] ========================================="
echo "[agent] Oneform Agent Ready!"
echo "[agent] - CDP: ${CDP_ENDPOINT}"
echo "[agent] - AD project: /app/AD"
echo "[agent] - ADJIAN project: /app/ADJIAN"
echo "[agent] - Mode: Event-driven (continuous monitoring)"
echo "[agent] ========================================="

# Event-driven task monitor: continuously watches page for task signals
# instead of sleeping between checks
echo "[agent] Starting event-driven task monitor..."
while true; do
    python3 /app/check_new_tasks.py 2>&1 | while read line; do echo "[monitor] $line"; done
    # Short cooldown to avoid tight loop when no tasks found
    sleep 5
done &

# Keep container alive
exec sleep infinity

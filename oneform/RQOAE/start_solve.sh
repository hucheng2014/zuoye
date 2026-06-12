#!/usr/bin/env bash
# Start RQOAE auto-solver in oneform-agent (single instance).
set -euo pipefail

CONTAINER=oneform-agent
LOG=/app/RQOAE/solve.log

if docker exec "$CONTAINER" sh -c 'test -f /tmp/rqoae_solve.lock && kill -0 "$(cat /tmp/rqoae_solve.lock)" 2>/dev/null'; then
  echo "solve_tasks already running in $CONTAINER (pid $(docker exec $CONTAINER cat /tmp/rqoae_solve.lock))"
  exit 1
fi

echo "Starting solve_tasks in $CONTAINER → $LOG"
docker exec -d "$CONTAINER" bash -c "exec python3 -u /app/RQOAE/solve_tasks.py >> $LOG 2>&1"
sleep 2
echo "Tail log: tail -f $(dirname "$0")/solve.log"
echo "noVNC:    http://127.0.0.1:6081/vnc.html"

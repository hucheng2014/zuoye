#!/usr/bin/env bash
# Stop RQOAE auto-solver in oneform-agent.
set -euo pipefail

CONTAINER=oneform-agent

docker exec "$CONTAINER" sh -c 'killall python3 2>/dev/null || true; rm -f /tmp/rqoae_solve.lock'
echo "Stopped solve_tasks in $CONTAINER"

#!/bin/bash
# Call after submit + NEXT TASK so watchdog restarts keepalive for the next task.
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
RUNS="$ROOT/runs"
mkdir -p "$RUNS"
date -Iseconds > "$RUNS/submitted.flag"
echo "submitted.flag written — watchdog will restart keepalive."

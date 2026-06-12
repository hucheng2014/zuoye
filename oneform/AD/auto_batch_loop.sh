#!/bin/bash
# Auto loop: wait 9 min from last submit, fill+submit one batch record, repeat.
set -euo pipefail
RECORD="$1"
CONTAINER=oneform-agent
WORKDIR=/app/AD

echo "[$(date -Iseconds)] Waiting 9 minutes before submit..."
sleep 540

echo "[$(date -Iseconds)] Filling $RECORD"
docker exec -w "$WORKDIR" "$CONTAINER" python3 fill_ad_page.py "$RECORD"

echo "[$(date -Iseconds)] Submitting $RECORD"
docker exec -w "$WORKDIR" "$CONTAINER" python3 submit_ad_page.py "$RECORD"

echo "[$(date -Iseconds)] Done: $RECORD"

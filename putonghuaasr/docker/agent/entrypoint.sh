#!/bin/bash
set -e

echo "[agent] Validating ASR model mounts..."

# Check Qwen3-ASR model
if [ -n "$PUTONGHUAASR_QWEN3_ASR_MODEL" ]; then
    QWEN3_ASR_MODEL="$PUTONGHUAASR_QWEN3_ASR_MODEL"
elif echo "$PUTONGHUAASR_MODEL" | grep -qi "faster-whisper"; then
    QWEN3_ASR_MODEL="${PUTONGHUAASR_BASE:-/app}/models/Qwen3-ASR"
else
    QWEN3_ASR_MODEL="${PUTONGHUAASR_MODEL:-${PUTONGHUAASR_BASE:-/app}/models/Qwen3-ASR}"
fi
if [ ! -d "$QWEN3_ASR_MODEL" ]; then
    echo "[agent] ERROR: Qwen3-ASR model directory not found: $QWEN3_ASR_MODEL"
    echo "[agent] Make sure models/ is mounted correctly, or set PUTONGHUAASR_QWEN3_ASR_MODEL."
    exit 1
fi

if [ ! -f "$QWEN3_ASR_MODEL/config.json" ]; then
    echo "[agent] ERROR: config.json not found in Qwen3-ASR model directory: $QWEN3_ASR_MODEL"
    exit 1
fi

QWEN3_MODEL_FILE=$(find -L "$QWEN3_ASR_MODEL" \( -name "*.safetensors" -o -name "pytorch_model*.bin" -o -name "model*.bin" \) | head -1)
if [ -z "$QWEN3_MODEL_FILE" ]; then
    echo "[agent] ERROR: No Qwen3-ASR weight files found in $QWEN3_ASR_MODEL"
    exit 1
fi
echo "[agent] ✓ Qwen3-ASR model found: $QWEN3_MODEL_FILE"

# Check FireRedASR model
if [ ! -d "$PUTONGHUAASR_FIRERED_MODEL" ]; then
    echo "[agent] ERROR: FireRedASR model directory not found: $PUTONGHUAASR_FIRERED_MODEL"
    echo "[agent] Make sure models/ is mounted correctly."
    exit 1
fi

FIRERED_MODEL_FILE=$(find "$PUTONGHUAASR_FIRERED_MODEL" -name "*.pt" -o -name "*.bin" -o -name "*.ckpt" -o -name "*.pth" -o -name "*.pth.tar" | head -1)
if [ -z "$FIRERED_MODEL_FILE" ]; then
    echo "[agent] ERROR: No model files found in $PUTONGHUAASR_FIRERED_MODEL"
    exit 1
fi
echo "[agent] ✓ FireRedASR model found: $FIRERED_MODEL_FILE"

# Check FireRedASR source
if [ ! -d "$PUTONGHUAASR_FIRERED_REPO" ]; then
    echo "[agent] ERROR: FireRedASR source not found: $PUTONGHUAASR_FIRERED_REPO"
    exit 1
fi
echo "[agent] ✓ FireRedASR source found: $PUTONGHUAASR_FIRERED_REPO"

# Wait for browser CDP endpoint
echo "[agent] Waiting for browser CDP endpoint at ${PUTONGHUAASR_CDP_ENDPOINT}..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -H "Host: localhost:9222" "${PUTONGHUAASR_CDP_ENDPOINT}/json/version" > /dev/null 2>&1; then
        echo "[agent] ✓ Browser CDP is ready!"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    if [ $((WAITED % 10)) -eq 0 ]; then
        echo "[agent] Still waiting for browser... (${WAITED}s/${MAX_WAIT}s)"
    fi
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[agent] ERROR: Browser CDP not ready after ${MAX_WAIT}s"
    echo "[agent] Check browser container logs: docker compose logs browser"
    exit 1
fi

echo "[agent] ========================================="
echo "[agent] Container ready!"
echo "[agent] - CDP endpoint: ${PUTONGHUAASR_CDP_ENDPOINT}"
echo "[agent] - Qwen3-ASR model: ${QWEN3_ASR_MODEL}"
echo "[agent] - Work audio: ${PUTONGHUAASR_WORK_AUDIO}"
echo "[agent] - Work context: /app/_work_context"
echo "[agent] ========================================="
echo "[agent] Use 'docker compose exec agent bash' to enter this container."

# Keep container alive
exec sleep infinity

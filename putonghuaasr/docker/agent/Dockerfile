# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies (cached layer)
COPY docker/agent/requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Install Node.js 20 LTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install runtime system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Install Node.js dependencies
COPY package.json package-lock.json* /app/
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

# Copy entrypoint
COPY docker/agent/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Environment defaults
ENV PUTONGHUAASR_BASE=/app
ENV PUTONGHUAASR_QWEN3_ASR_MODEL=/app/models/Qwen3-ASR
ENV PUTONGHUAASR_MODEL=/app/models/Qwen3-ASR
ENV PUTONGHUAASR_QWEN3_ASR_DEVICE=cpu
ENV PUTONGHUAASR_QWEN3_ASR_LOCAL_FILES_ONLY=1
ENV PUTONGHUAASR_FIRERED_REPO=/app/third_party/FireRedASR
ENV PUTONGHUAASR_FIRERED_MODEL=/app/models/FireRedASR-AED-L
ENV PUTONGHUAASR_WORK_AUDIO=/app/_work_audio
ENV PUTONGHUAASR_CDP_PORT=9222
ENV PUTONGHUAASR_CDP_ENDPOINT=http://browser:9222

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

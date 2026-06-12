FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg libsndfile1 ffmpeg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install torch CPU first from PyTorch index
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python deps from PyPI
RUN pip install --no-cache-dir \
    websocket-client numpy librosa soundfile \
    laion-clap panns-inference transformers

WORKDIR /app
RUN npm init -y && npm install playwright

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY check_new_tasks.py /app/check_new_tasks.py
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV CDP_ENDPOINT=http://browser:9223
ENV CHECK_INTERVAL=3600

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

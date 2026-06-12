FROM python:3.11-slim
WORKDIR /app

# Install git and openssh-server (required for version control and Trae container SSH proxy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-server \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY repo/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy repo content (including .git)
COPY repo/ ./

EXPOSE 8078
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8078"]

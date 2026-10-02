# syntax=docker/dockerfile:1
#
# TV Show Chat API + built frontend, for Render or any container host.
#
# Supply chain: base images pinned by digest (update with Dependabot's docker
# ecosystem), Python deps installed only from the hash-locked requirements.txt,
# npm deps only from package-lock.json with install scripts disabled, and the
# embedding model baked in at its pinned revision so the running container
# never fetches code or weights from the internet.

# ---- Stage 1: frontend ------------------------------------------------------
FROM node:24.21.0-slim@sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6 AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python dependencies and the embedding model ---------------------
FROM python:3.12.15-slim@sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256 AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf

WORKDIR /build
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --require-hashes -r requirements.txt

# Download the model once, at the revision pinned in embedder.py.
COPY app/services/embedder.py /tmp/embedder.py
RUN /opt/venv/bin/python -c "import sys; sys.path.insert(0, '/tmp'); from embedder import load_embedder; load_embedder()"

# ---- Stage 3: runtime --------------------------------------------------------
FROM python:3.12.15-slim@sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf /opt/hf

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HF_HOME=/opt/hf \
    HF_HUB_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# Code and assets are root-owned and read-only to the app user; only the data
# and log directories are writable.
COPY app/ ./app/
COPY --from=frontend-builder /frontend/dist ./app/static
RUN mkdir -p app/data/episodes app/data/embeddings app/logs \
    && chown -R 10001:10001 app/data app/logs

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=5)"]

# Shell form is needed to expand $PORT (set by Render); exec makes uvicorn PID 1
# so it receives SIGTERM directly.
# hadolint ignore=DL3025
CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

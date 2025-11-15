# Multi-stage Dockerfile for TV Show Chat FastAPI app
# Optimized for production deployment on Render

# Stage 1: Build frontend
FROM node:20-slim as frontend-builder

WORKDIR /frontend

# Copy frontend package files first (for better caching)
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy all frontend source files (excluding node_modules via .dockerignore)
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Build Python dependencies
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ ./app/
COPY runtime.txt ./

# Copy frontend build to static directory
COPY --from=frontend-builder /frontend/dist ./app/static

# Create necessary directories
RUN mkdir -p app/data/episodes app/data/embeddings app/data/chroma app/logs

# Expose port (Render will set PORT env var, but default to 8000)
EXPOSE 8000

# Health check (simple port check - Render will use /health endpoint for actual health checks)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s = socket.socket(); s.settimeout(1); result = s.connect_ex(('localhost', 8000)); s.close(); exit(0 if result == 0 else 1)" || exit 1

# Run the application
# Render sets PORT env var, so we use it dynamically
CMD python -m uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1


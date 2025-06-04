# Multi-stage Docker build for Karen AI Assistant
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r karen && useradd -r -g karen karen

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/
COPY .env.example /app/.env

# Create necessary directories
RUN mkdir -p /app/logs /app/autonomous-agents/communication/{inbox,outbox,status,knowledge-base} \
    && chown -R karen:karen /app

# Set proper permissions
RUN chmod -R 755 /app

# Switch to non-root user
USER karen

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production API server
FROM base as api
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]

# Celery worker
FROM base as worker
CMD ["celery", "-A", "celery_app:celery_app", "worker", "-l", "INFO", "--pool=solo"]

# Celery beat scheduler
FROM base as beat
CMD ["celery", "-A", "celery_app:celery_app", "beat", "-l", "INFO", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]

# Default target (API server)
FROM api as default
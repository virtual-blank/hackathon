# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Builder — install dependencies with Poetry
# =============================================================================
FROM python:3.12-slim AS builder

# Install Poetry 1.8.5 (pinned version)
ENV POETRY_VERSION=1.8.5 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /build


# Copy dependency manifests and lock file
COPY pyproject.toml poetry.lock ./

# Install dependencies (production only, no root package)
RUN poetry install --without dev --no-root

# =============================================================================
# Stage 2: Runtime — minimal image with app code
# =============================================================================
FROM python:3.12-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /build/.venv /app/.venv

# Copy application code
COPY --chown=app:app . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Создаем папку для логов и выдаем права пользователю app
RUN mkdir -p /app/logs && chown app:app /app/logs

# Switch to non-root user
USER app

# Activate virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

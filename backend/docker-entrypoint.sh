#!/bin/sh
set -e

echo "[entrypoint] Running Alembic migrations..."
python -m alembic upgrade head

echo "[entrypoint] Starting uvicorn server..."
exec python -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*"

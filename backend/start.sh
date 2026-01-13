#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Installing Playwright browsers..."
python -m playwright install chromium
python -m playwright install-deps chromium

echo "Running database migrations..."
python -m alembic upgrade head

echo "Setting up admin account..."
python scripts/auto_setup_admin.py

echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}


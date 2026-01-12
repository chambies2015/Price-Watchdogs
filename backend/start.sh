#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Running database migrations..."
python -m alembic upgrade head

echo "Setting up admin account..."
python scripts/auto_setup_admin.py

echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}


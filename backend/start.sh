#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
# Use the PORT environment variable if available, otherwise default to 8000
PORT=${PORT:-8000}
echo "Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT

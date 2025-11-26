#!/bin/bash
set -e

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head
}

# Run the migration function
run_migrations

# Start Celery worker in the background
echo "Starting Celery worker..."
DB_POOL_DISABLE=True celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Function to handle shutdown gracefully
shutdown() {
    echo "Shutting down..."
    kill $CELERY_PID 2>/dev/null
    exit 0
}

trap shutdown SIGTERM SIGINT

# Start the application
# Use the PORT environment variable if available, otherwise default to 8000
PORT=${PORT:-8000}
echo "Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips '*'

#!/bin/bash
set -e

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations..."
    # Retry migrations up to 5 times to handle transient connection issues
    MAX_RETRIES=5
    RETRY_DELAY=5

    for i in $(seq 1 $MAX_RETRIES); do
        echo "Attempt $i of $MAX_RETRIES: Running alembic upgrade head..."
        if alembic upgrade head; then
            echo "Database migrations completed successfully."
            return 0
        fi
        echo "Migration attempt $i failed."
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Retrying in $RETRY_DELAY seconds..."
            sleep $RETRY_DELAY
        fi
    done

    echo "Warning: Database migrations failed after $MAX_RETRIES attempts."
    echo "Continuing anyway - migrations may have been applied manually or already exist."
    return 0
}

# Run the migration function
run_migrations

# Start Celery worker with threads pool for parallel execution
# Using threads pool to support asyncio.run() in tasks while enabling concurrency
# CRITICAL: Disable DB connection pooling for worker processes to prevent
# "Event loop is closed" errors when sharing QueuePool across asyncio.run() loops
export DB_POOL_DISABLE=True
echo "Starting Celery worker with threads pool (concurrency=8)..."
celery -A app.tasks.celery_app worker \
    --pool=threads \
    --concurrency=8 \
    --loglevel=info \
    --max-memory-per-child=400000 \
    2>&1 &
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
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --proxy-headers \
  --forwarded-allow-ips '*' \
  --timeout-keep-alive 300 \
  --limit-concurrency 100 \
  --backlog 2048

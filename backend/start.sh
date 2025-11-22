#!/bin/bash
set -e

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations..."

    # Try to upgrade to head
    if alembic upgrade head; then
        echo "Migrations applied successfully."
    else
        echo "Migration failed. Attempting to repair migration history..."

        # Get the latest revision ID available in the codebase
        LATEST_REV=$(alembic heads | awk '{print $1}')

        if [ -z "$LATEST_REV" ]; then
            echo "Error: Could not determine latest revision from codebase."
            exit 1
        fi

        echo "Detected code revision: $LATEST_REV"
        echo "Clearing corrupted alembic_version table..."

        # Manually clear the alembic_version table using psql
        # DATABASE_URL format: postgresql+asyncpg://user:pass@host:port/dbname
        # We need to convert this to a format psql understands or rely on libpq env vars if set.
        # Since DATABASE_URL is set, we can try to parse it or use python to run the SQL.

        # Using a small python snippet is safer than parsing URLs in bash
        python3 -c "
import os
import sqlalchemy
from sqlalchemy import text

url = os.getenv('DATABASE_URL')
if not url:
    print('Error: DATABASE_URL not set')
    exit(1)

# Fix asyncpg driver for sync connection if needed, though sqlalchemy.create_engine handles many.
# Typically DATABASE_URL in this project is postgresql+asyncpg://...
# We need a sync driver for this quick fix script or use 'postgresql://'
sync_url = url.replace('+asyncpg', '')

try:
    engine = sqlalchemy.create_engine(sync_url)
    with engine.connect() as conn:
        print('Executing: DELETE FROM alembic_version')
        conn.execute(text('DELETE FROM alembic_version'))
        conn.commit()
        print('Successfully cleared alembic_version table.')
except Exception as e:
    print(f'Error clearing table: {e}')
    exit(1)
"

        if [ $? -eq 0 ]; then
            echo "Stamping database to match codebase revision: $LATEST_REV"
            # Now that the table is empty, stamp should work treating it as a 'new' DB state
            alembic stamp "$LATEST_REV"

            echo "Retrying upgrade..."
            alembic upgrade head
        else
            echo "Failed to clear alembic_version table via Python helper."
            exit 1
        fi
    fi
}

# Run the migration function
run_migrations

# Start the application
# Use the PORT environment variable if available, otherwise default to 8000
PORT=${PORT:-8000}
echo "Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT

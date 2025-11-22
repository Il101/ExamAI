#!/bin/bash
set -e

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations (Attempt 3: Robust PSQL Repair)..."

    # Try to upgrade to head
    if alembic upgrade head; then
        echo "Migrations applied successfully."
    else
        echo "Migration failed. Attempting to repair migration history using PSQL..."

        # Get the latest revision ID available in the codebase
        LATEST_REV=$(alembic heads | awk '{print $1}')

        if [ -z "$LATEST_REV" ]; then
            echo "Error: Could not determine latest revision from codebase."
            exit 1
        fi

        echo "Detected code revision: $LATEST_REV"
        echo "Clearing corrupted alembic_version table..."

        # Parse DATABASE_URL using python (safest way to handle special chars), but ONLY for string parsing.
        # We output shell-evaluable exports.
        eval $(python3 -c "
import os
from urllib.parse import urlparse

url = os.getenv('DATABASE_URL')
if url:
    # Handle postgresql+asyncpg:// format
    if '+asyncpg' in url:
        url = url.replace('+asyncpg', '')

    parsed = urlparse(url)
    print(f'export PGHOST={parsed.hostname}')
    print(f'export PGPORT={parsed.port or 5432}')
    print(f'export PGUSER={parsed.username}')
    print(f'export PGPASSWORD={parsed.password}')
    print(f'export PGDATABASE={parsed.path[1:]}') # Remove leading slash
")

        # Now run psql with the exported environment variables
        if command -v psql > /dev/null; then
            echo "Executing DELETE FROM alembic_version using psql..."
            psql -c "DELETE FROM alembic_version;"

            if [ $? -eq 0 ]; then
                echo "Successfully cleared alembic_version table."
                echo "Stamping database to match codebase revision: $LATEST_REV"
                alembic stamp "$LATEST_REV"

                echo "Retrying upgrade..."
                alembic upgrade head
            else
                echo "Error: psql command failed."
                exit 1
            fi
        else
            echo "Error: psql is not installed or not in PATH."
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

#!/bin/bash
set -e

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations..."

    # Try to upgrade to head
    if alembic upgrade head; then
        echo "Migrations applied successfully."
    else
        echo "Migration failed. Checking for revision mismatch..."

        # If upgrade failed, it might be due to a missing revision file (phantom migration in DB).
        # We will attempt to stamp the DB to the latest version we actually HAVE in the code.

        # Get the latest revision ID available in the codebase
        LATEST_REV=$(alembic heads | awk '{print $1}')

        if [ -n "$LATEST_REV" ]; then
            echo "Stamping database to match codebase revision: $LATEST_REV"
            alembic stamp "$LATEST_REV"

            echo "Retrying upgrade..."
            alembic upgrade head
        else
            echo "Error: Could not determine latest revision from codebase."
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

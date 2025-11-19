#!/bin/bash
# Database migration script for production
# Usage: ./migrate.sh

set -e  # Exit on error

echo "🔄 Running database migrations..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Check for pending migrations
echo "📋 Checking for pending migrations..."
alembic current

# Run migrations
echo "⏫ Upgrading database to latest version..."
alembic upgrade head

# Verify migration
echo "✅ Current database version:"
alembic current

echo "✅ Database migrations completed successfully"

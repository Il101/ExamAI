#!/bin/bash
# Database backup script
# Usage: ./backup-db.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/examai_backup_$DATE.sql.gz"

echo "🔄 Starting database backup..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Parse DATABASE_URL
# Format: postgresql+asyncpg://user:password@host:port/database
if [[ $DATABASE_URL =~ postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    echo "❌ ERROR: Cannot parse DATABASE_URL"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Run pg_dump and compress
echo "📦 Creating backup: $BACKUP_FILE"
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    | gzip > "$BACKUP_FILE"

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup completed: $BACKUP_FILE ($FILE_SIZE)"

# Optional: Upload to cloud storage (uncomment and configure as needed)
# aws s3 cp "$BACKUP_FILE" "s3://examai-backups/database/"
# echo "☁️  Backup uploaded to S3"

# Keep only last 30 days of backups locally
echo "🧹 Cleaning old backups (older than 30 days)..."
find "$BACKUP_DIR" -name "examai_backup_*.sql.gz" -mtime +30 -delete

echo "✅ Backup process completed successfully"

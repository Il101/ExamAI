#!/bin/bash

# Script to fix DATABASE_URL in Railway
# This script updates the DATABASE_URL to use Supabase Connection Pooler

echo "🔧 Fixing DATABASE_URL in Railway..."
echo ""
echo "⚠️  IMPORTANT: You need to get the Connection Pooler URL from Supabase first!"
echo ""
echo "Steps to get the correct DATABASE_URL:"
echo "1. Go to https://supabase.com/dashboard"
echo "2. Select your project: pjgtzblqhtpdtojgbzpe"
echo "3. Go to Settings → Database"
echo "4. Scroll to 'Connection Pooling' section"
echo "5. Select 'Session' mode"
echo "6. Copy the 'Connection string'"
echo ""
echo "The format should be:"
echo "postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-REGION.pooler.supabase.com:6543/postgres"
echo ""
echo "Then convert it to asyncpg format:"
echo "postgresql+asyncpg://postgres.PROJECT_REF:[PASSWORD]@aws-0-REGION.pooler.supabase.com:6543/postgres"
echo ""
echo "To update in Railway, run:"
echo "railway variables --set DATABASE_URL='postgresql+asyncpg://postgres.PROJECT_REF:[PASSWORD]@aws-0-REGION.pooler.supabase.com:6543/postgres' --service ExamAI"
echo ""
echo "❌ The current DATABASE_URL uses 'db.pjgtzblqhtpdtojgbzpe.supabase.co' which is NOT resolvable via DNS!"
echo "✅ You MUST use the Connection Pooler URL instead."

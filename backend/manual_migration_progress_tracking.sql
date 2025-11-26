-- Manual Migration: add_topic_progress_tracking
-- Run this SQL directly in Supabase SQL Editor if alembic migration fails

-- Add progress tracking columns to topics table
ALTER TABLE topics 
ADD COLUMN IF NOT EXISTS is_viewed BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE topics 
ADD COLUMN IF NOT EXISTS quiz_completed BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE topics 
ADD COLUMN IF NOT EXISTS last_viewed_at TIMESTAMPTZ;

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'topics'
AND column_name IN ('is_viewed', 'quiz_completed', 'last_viewed_at')
ORDER BY column_name;

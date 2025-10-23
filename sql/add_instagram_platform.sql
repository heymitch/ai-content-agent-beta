-- Migration: Add Instagram to generated_posts platform constraint
-- Date: 2025-10-22
-- Purpose: Allow Instagram SDK agent to save posts to generated_posts table

-- Drop the old constraint
ALTER TABLE generated_posts
DROP CONSTRAINT IF EXISTS generated_posts_platform_check;

-- Add new constraint with Instagram included
ALTER TABLE generated_posts
ADD CONSTRAINT generated_posts_platform_check
CHECK (platform IN ('linkedin', 'twitter', 'email', 'youtube', 'blog', 'instagram'));

-- Verify the constraint was added
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname = 'generated_posts_platform_check';

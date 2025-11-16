-- ============================================================================
-- MIGRATION: Make title column nullable in company_documents
-- ============================================================================
-- This migration removes the NOT NULL constraint from the title column
-- Safe to run multiple times (idempotent)
--
-- Run this if you get error: "null value in column 'title' violates not-null constraint"
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '🔧 Checking company_documents.title column constraint...';
END $$;

-- Remove NOT NULL constraint from title column
DO $$
DECLARE
  is_nullable TEXT;
BEGIN
  -- Check if title column is nullable
  SELECT is_nullable INTO is_nullable
  FROM information_schema.columns
  WHERE table_name = 'company_documents'
    AND column_name = 'title';

  IF is_nullable = 'NO' THEN
    RAISE NOTICE '➕ Making title column nullable...';
    ALTER TABLE company_documents ALTER COLUMN title DROP NOT NULL;
    RAISE NOTICE '✅ title column is now nullable';
  ELSE
    RAISE NOTICE '✅ title column is already nullable';
  END IF;
END $$;

-- Verify the migration
DO $$
DECLARE
  is_nullable TEXT;
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '🔍 Verifying migration...';

  SELECT is_nullable INTO is_nullable
  FROM information_schema.columns
  WHERE table_name = 'company_documents'
    AND column_name = 'title';

  IF is_nullable = 'YES' THEN
    RAISE NOTICE '';
    RAISE NOTICE '✅ ============================================';
    RAISE NOTICE '✅ Migration Complete!';
    RAISE NOTICE '✅ ============================================';
    RAISE NOTICE '';
    RAISE NOTICE '✓ title column is nullable';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your n8n workflow should now work without errors!';
    RAISE NOTICE '';
    RAISE NOTICE '💡 Note: The trigger sync_company_documents_fields()';
    RAISE NOTICE '   will auto-populate title from metadata if present.';
    RAISE NOTICE '';
  ELSE
    RAISE NOTICE '❌ Migration verification failed!';
    RAISE NOTICE '  title column is still NOT NULL';
  END IF;
END $$;

-- ============================================================================
-- MIGRATION 004: Make title column nullable in company_documents
-- ============================================================================
-- This migration removes the NOT NULL constraint from the title column
-- Safe to run multiple times (idempotent)
--
-- Auto-runs on: npm start (via bootstrap_database.js)
-- ============================================================================

DO $$
DECLARE
  col_nullable TEXT;
BEGIN
  -- Check if title column is nullable
  SELECT columns.is_nullable INTO col_nullable
  FROM information_schema.columns
  WHERE table_name = 'company_documents'
    AND column_name = 'title';

  IF col_nullable = 'NO' THEN
    RAISE NOTICE '➕ Making title column nullable...';
    ALTER TABLE company_documents ALTER COLUMN title DROP NOT NULL;
    RAISE NOTICE '✅ title column is now nullable';
  ELSE
    RAISE NOTICE '✅ title column is already nullable';
  END IF;

  RAISE NOTICE '✅ Migration 004 complete: title nullable';
  RAISE NOTICE '💡 Note: sync_company_documents_fields() trigger will auto-populate title from metadata';
END $$;

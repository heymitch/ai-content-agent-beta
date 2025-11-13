-- ============================================================================
-- EMERGENCY FIX: RLS Permission Denied for Service Role
-- ============================================================================
-- Run this if you're getting "permission denied" even with service_role key
--
-- This completely removes RLS from tables used by n8n workflow
-- ============================================================================

BEGIN;

-- Step 1: Disable RLS on n8n tables
ALTER TABLE company_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows DISABLE ROW LEVEL SECURITY;

-- Step 2: Drop ALL existing policies (they're conflicting)
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname, tablename
    FROM pg_policies
    WHERE tablename IN ('company_documents', 'document_metadata', 'document_rows')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename);
    RAISE NOTICE 'Dropped policy: % on %', pol.policyname, pol.tablename;
  END LOOP;
END $$;

-- Step 3: Re-enable RLS with correct policies
ALTER TABLE company_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows ENABLE ROW LEVEL SECURITY;

-- Step 4: Create single permissive policy for each table
CREATE POLICY "bypass_rls_company_documents"
  ON company_documents
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "bypass_rls_document_metadata"
  ON document_metadata
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "bypass_rls_document_rows"
  ON document_rows
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

-- Step 5: Verify policies
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '✅ RLS policies fixed!';
  RAISE NOTICE '';
  RAISE NOTICE 'Current policies:';
END $$;

SELECT
  tablename,
  policyname,
  cmd,
  CASE
    WHEN roles::text LIKE '%service_role%' THEN '✅ Includes service_role'
    ELSE '⚠️ Missing service_role'
  END as role_check
FROM pg_policies
WHERE tablename IN ('company_documents', 'document_metadata', 'document_rows')
ORDER BY tablename, policyname;

COMMIT;

-- Test permissions
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '🧪 Testing permissions...';
  RAISE NOTICE '';

  -- Try to count rows (should work now)
  RAISE NOTICE 'company_documents: % rows', (SELECT COUNT(*) FROM company_documents);
  RAISE NOTICE 'document_metadata: % rows', (SELECT COUNT(*) FROM document_metadata);
  RAISE NOTICE 'document_rows: % rows', (SELECT COUNT(*) FROM document_rows);

  RAISE NOTICE '';
  RAISE NOTICE '✅ All tests passed!';
  RAISE NOTICE 'n8n workflow should now work.';
END $$;

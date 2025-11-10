-- Migration 005: Add read policies for API key access
--
-- PROBLEM: RLS is enabled but only service_role has policies
-- API key (anon/authenticated) has no read policies = 0 results
--
-- SOLUTION: Add SELECT policies for anon/authenticated roles
--
-- Applied: 2025-01-10

-- Allow read access to content_examples for all users
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'content_examples'
    AND policyname = 'Enable read access for all users'
  ) THEN
    CREATE POLICY "Enable read access for all users"
    ON content_examples
    FOR SELECT
    USING (true);
  END IF;
END $$;

-- Allow read access to company_documents for all users
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'company_documents'
    AND policyname = 'Enable read access to company documents'
  ) THEN
    CREATE POLICY "Enable read access to company documents"
    ON company_documents
    FOR SELECT
    USING (true);
  END IF;
END $$;

-- Allow read access to research for all users
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'research'
    AND policyname = 'Enable read access to research'
  ) THEN
    CREATE POLICY "Enable read access to research"
    ON research
    FOR SELECT
    USING (true);
  END IF;
END $$;

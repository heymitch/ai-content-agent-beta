-- ============================================================================
-- GRANT EXPLICIT PERMISSIONS TO SERVICE ROLE
-- ============================================================================
-- Sometimes RLS policies alone aren't enough
-- This grants direct table permissions to service_role
-- ============================================================================

-- Grant all privileges on tables
GRANT ALL ON TABLE company_documents TO service_role;
GRANT ALL ON TABLE document_metadata TO service_role;
GRANT ALL ON TABLE document_rows TO service_role;

-- Grant usage on sequences
GRANT USAGE, SELECT ON SEQUENCE document_rows_id_seq TO service_role;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION match_documents(vector, integer, jsonb) TO service_role;

-- Verify grants
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '✅ Permissions granted to service_role';
  RAISE NOTICE '';
  RAISE NOTICE 'Checking grants:';
END $$;

SELECT
  tablename,
  string_agg(privilege_type, ', ') as privileges
FROM information_schema.table_privileges
WHERE grantee = 'service_role'
  AND table_schema = 'public'
  AND table_name IN ('company_documents', 'document_metadata', 'document_rows')
GROUP BY tablename
ORDER BY tablename;

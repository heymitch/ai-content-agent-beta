-- Check if trigger exists
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE event_object_table = 'company_documents';

-- Check if sync function exists
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name = 'sync_company_documents_fields';

-- Check what metadata looks like in existing records
SELECT
  id,
  title,
  metadata->>'title' as metadata_title,
  metadata->>'google_drive_file_id' as metadata_file_id,
  jsonb_pretty(metadata) as full_metadata
FROM company_documents
ORDER BY created_at DESC
LIMIT 3;

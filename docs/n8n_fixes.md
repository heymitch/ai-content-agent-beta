# n8n Agent Memory Template Fixes

## Issue: "Delete Old Doc Rows" Node Breaking

### Problem
The "Delete Old Doc Rows" node in the n8n template has an incorrect filter string:

```
filterString: "=metadata->>file_id=like.*{{ $json.file_id }}*"
```

### Issues:
1. **Wrong metadata key**: The template uses `google_drive_file_id` in metadata (line 12), but the delete tries to match `file_id`
2. **Incorrect PostgreSQL LIKE syntax**: `like.*...*` is not valid
3. **Wrong JSONB operator usage**: Mixing `->` and `=` incorrectly

### Solution 1: Fix the Filter String in n8n

Update the "Delete Old Doc Rows" node parameters to:

**For exact match:**
```json
{
  "operation": "delete",
  "tableId": "company_documents",
  "filterType": "string",
  "filterString": "metadata->>'google_drive_file_id'=eq.{{ $json.file_id }}"
}
```

**For LIKE match (if file_id might be partial):**
```json
{
  "operation": "delete",
  "tableId": "company_documents",
  "filterType": "string",
  "filterString": "metadata->>'google_drive_file_id'=like.*{{ $json.file_id }}*"
}
```

### Solution 2: Use Supabase Filter Format

Supabase expects PostgREST filter format. The correct syntax is:

- **Exact match**: `column=eq.value`
- **LIKE match**: `column=like.*pattern*`
- **JSONB field**: Use `->>` to extract text: `metadata->>'field_name'`

### Solution 3: Alternative - Use Filter Object

Instead of filterString, use the structured filter:

```json
{
  "operation": "delete",
  "tableId": "company_documents",
  "filters": {
    "conditions": [
      {
        "keyName": "metadata->>'google_drive_file_id'",
        "condition": "eq",
        "keyValue": "={{ $json.file_id }}"
      }
    ]
  }
}
```

## Testing the Fix

You can test the delete operation directly in PostgreSQL:

```sql
-- Test query to see what would be deleted
SELECT id, metadata->>'google_drive_file_id' as file_id, content
FROM company_documents
WHERE metadata->>'google_drive_file_id' = 'YOUR_FILE_ID';

-- Actual delete (be careful!)
DELETE FROM company_documents
WHERE metadata->>'google_drive_file_id' = 'YOUR_FILE_ID';
```

Or via Supabase client in Python:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Delete documents matching the file_id
result = supabase.table('company_documents').delete().eq(
    'metadata->>google_drive_file_id',
    'YOUR_FILE_ID'
).execute()

print(f"Deleted {len(result.data)} documents")
```

## Same Fix Needed for "Delete Old Data Rows"

The "Delete Old Data Rows" node (lines 619-648) has a similar structure but looks correct:

```json
{
  "operation": "delete",
  "tableId": "document_rows",
  "filters": {
    "conditions": [
      {
        "keyName": "dataset_id",
        "condition": "eq",
        "keyValue": "={{ $('Set File ID').item.json.file_id }}"
      }
    ]
  }
}
```

This one is fine because `dataset_id` is a regular column, not a JSONB field.

## Recommended n8n Template Update

Replace line 203 in your n8n template JSON:

**Before:**
```json
"filterString": "=metadata->>file_id=like.*{{ $json.file_id }}*"
```

**After:**
```json
"filterString": "metadata->>'google_drive_file_id'=eq.{{ $json.file_id }}"
```

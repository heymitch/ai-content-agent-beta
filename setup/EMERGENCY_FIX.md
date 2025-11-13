# 🚨 EMERGENCY FIX: "permission denied" with Correct Service Role Key

If you're getting **"permission denied for table company_documents"** even after using the correct `service_role` key, follow these steps.

---

## The Issue

The `service_role` key should bypass ALL RLS policies, but sometimes:
1. Conflicting RLS policies block even service_role
2. Direct table permissions are missing
3. Supabase authenticator role restrictions

---

## Fix 1: Nuclear Option - Disable RLS (Quick Fix)

Run this in **Supabase SQL Editor**:

```sql
-- Completely disable RLS on n8n tables
ALTER TABLE company_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('company_documents', 'document_metadata', 'document_rows');
```

**Expected result:**
```
tablename          | rowsecurity
-------------------|------------
company_documents  | false       ← Should be false
document_metadata  | false       ← Should be false
document_rows      | false       ← Should be false
```

**Test your n8n workflow now.** If it works, you're done!

**⚠️ Security Note:** This removes row-level security. Fine for:
- Private Supabase projects
- Internal tools
- Projects where ALL data belongs to one user/team

Not recommended for:
- Multi-tenant apps where users can only see their own data

---

## Fix 2: Clean RLS Policies (Proper Fix)

If you want to keep RLS enabled but fix the policies:

```sql
-- Step 1: Drop ALL existing policies
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
  END LOOP;
END $$;

-- Step 2: Create new permissive policies
CREATE POLICY "allow_all_company_documents"
  ON company_documents
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "allow_all_document_metadata"
  ON document_metadata
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "allow_all_document_rows"
  ON document_rows
  AS PERMISSIVE
  FOR ALL
  TO public, authenticated, anon, service_role
  USING (true)
  WITH CHECK (true);

-- Step 3: Verify
SELECT tablename, policyname, cmd, roles::text
FROM pg_policies
WHERE tablename IN ('company_documents', 'document_metadata', 'document_rows');
```

**Test your n8n workflow.**

---

## Fix 3: Grant Direct Permissions

If RLS fixes don't work, grant explicit permissions:

```sql
-- Grant all privileges to service_role
GRANT ALL ON TABLE company_documents TO service_role;
GRANT ALL ON TABLE document_metadata TO service_role;
GRANT ALL ON TABLE document_rows TO service_role;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Verify
SELECT
  tablename,
  grantee,
  string_agg(privilege_type, ', ') as privileges
FROM information_schema.table_privileges
WHERE grantee = 'service_role'
  AND table_schema = 'public'
  AND table_name IN ('company_documents', 'document_metadata', 'document_rows')
GROUP BY tablename, grantee;
```

**Test your n8n workflow.**

---

## Fix 4: Check n8n Configuration

Sometimes the issue is in how n8n is configured:

### Check 1: Verify Service Role Key Format

Your service role key should:
- ✅ Be 300-500 characters long
- ✅ Start with `eyJ`
- ✅ Have exactly 2 dots (`.`) separating 3 parts
- ✅ NOT have "Bearer " prefix
- ✅ NOT have quotes around it

**Decode your key** at https://jwt.io - payload should show:
```json
{
  "iss": "supabase",
  "role": "service_role",  ← Must say "service_role"
  "iat": 1736799595,
  "exp": 2052375595
}
```

### Check 2: n8n Supabase Credential Configuration

In n8n → Settings → Credentials → Supabase API:

```
Supabase URL: https://[project].supabase.co
Supabase Key: eyJhbGci... (full service_role key, no Bearer prefix)
```

### Check 3: Try Raw DELETE Request

Test if service_role key works outside n8n:

```bash
# Replace with your actual values
PROJECT_REF="deyqwroxutdebzfchzpb"
SERVICE_KEY="eyJhbGci..."  # Your full service_role key

# Try to delete (should work)
curl -X DELETE \
  "https://${PROJECT_REF}.supabase.co/rest/v1/company_documents?id=eq.00000000-0000-0000-0000-000000000000" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}"
```

If this returns `404` (not found) → **Good! Service role works**
If this returns `403` (forbidden) → **Bad! Key issue**

---

## Fix 5: Complete Reset (Last Resort)

If nothing else works, reset everything:

```sql
-- 1. Drop tables
DROP TABLE IF EXISTS document_rows CASCADE;
DROP TABLE IF EXISTS document_metadata CASCADE;
DROP TABLE IF EXISTS company_documents CASCADE;

-- 2. Re-run bootstrap script
-- See bootstrap_supabase.sql

-- 3. Test immediately after bootstrap
```

---

## Diagnostic Script

Run this to see what's blocking you:

```sql
-- Check RLS status
SELECT
  tablename,
  CASE WHEN rowsecurity THEN '🔒 RLS Enabled' ELSE '🔓 RLS Disabled' END as security_status
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('company_documents', 'document_metadata', 'document_rows');

-- Check policies
SELECT
  tablename,
  policyname,
  cmd,
  CASE
    WHEN roles::text LIKE '%service_role%' THEN '✅ Allows service_role'
    ELSE '❌ Blocks service_role'
  END as service_role_status
FROM pg_policies
WHERE tablename IN ('company_documents', 'document_metadata', 'document_rows')
ORDER BY tablename;

-- Check direct grants
SELECT
  tablename,
  grantee,
  privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public'
  AND table_name IN ('company_documents', 'document_metadata', 'document_rows')
  AND grantee IN ('service_role', 'postgres', 'authenticated', 'anon')
ORDER BY tablename, grantee;
```

**Analyze output:**
- If RLS is enabled + no policies allow service_role → Use Fix 2
- If RLS is disabled but still getting errors → Check n8n key (Fix 4)
- If direct grants are missing → Use Fix 3

---

## Recommended Fix Order

Try these in order until n8n works:

1. **Fix 1** (Disable RLS) - Fastest, works 90% of the time
2. **Fix 4** (Verify key) - Make sure you're actually using service_role key
3. **Fix 2** (Clean policies) - If you need RLS enabled
4. **Fix 3** (Grant permissions) - Nuclear option
5. **Fix 5** (Reset) - Last resort

---

## After It Works

Once your workflow runs successfully:

1. **Test end-to-end:**
   - Upload file to Google Drive
   - Verify file appears in `company_documents`
   - Check embeddings are created
   - Verify metadata in `document_metadata`

2. **Document what fixed it:**
   - Which fix worked?
   - Was it RLS, permissions, or key issue?
   - Share with other clients

3. **Prevent future issues:**
   - Always use service_role key in n8n
   - Run bootstrap script on fresh Supabase projects
   - Test with sample file before going live

---

## Quick Command Summary

**Nuclear option (disable RLS):**
```sql
ALTER TABLE company_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows DISABLE ROW LEVEL SECURITY;
```

**Or run the complete fix script:**
```bash
# In Supabase SQL Editor, run:
setup/fix_rls_issue.sql
```

**Or grant explicit permissions:**
```bash
# In Supabase SQL Editor, run:
setup/grant_permissions.sql
```

---

## Still Not Working?

Contact support with:
1. Full error message from n8n
2. Output of diagnostic script above
3. Screenshot of your n8n Supabase credential (hide key)
4. Which fixes you tried

The issue is solvable - we just need to identify the exact blocker!

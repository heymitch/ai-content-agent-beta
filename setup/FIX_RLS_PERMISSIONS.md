# 🔐 Fix: "permission denied for table company_documents"

## The Real Error

```
permission denied for table company_documents
```

This is **NOT** a missing table issue. This is a **Row Level Security (RLS) policy** issue.

---

## Root Cause

Your `company_documents` table has RLS enabled, but the policies **don't allow DELETE operations** for the service role or anon key you're using in n8n.

## The Fix (2 Minutes)

### Option 1: Quick Fix - Allow All Operations (Recommended for n8n)

Run this in your **Supabase SQL Editor**:

```sql
-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;

-- Create a new permissive policy that allows ALL operations
CREATE POLICY "Allow all operations on company_documents"
  ON company_documents
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Verify policy was created
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'company_documents';
```

### Option 2: Granular Policies (More Secure)

If you want separate policies for different operations:

```sql
-- Drop existing policies
DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;

-- Allow SELECT (read)
CREATE POLICY "Allow read on company_documents"
  ON company_documents
  FOR SELECT
  USING (true);

-- Allow INSERT (create)
CREATE POLICY "Allow insert on company_documents"
  ON company_documents
  FOR INSERT
  WITH CHECK (true);

-- Allow UPDATE (modify)
CREATE POLICY "Allow update on company_documents"
  ON company_documents
  FOR UPDATE
  USING (true)
  WITH CHECK (true);

-- Allow DELETE (remove)
CREATE POLICY "Allow delete on company_documents"
  ON company_documents
  FOR DELETE
  USING (true);

-- Verify policies
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'company_documents'
ORDER BY cmd;
```

---

## Apply Same Fix to Other Tables

Run this for ALL tables used by n8n:

```sql
-- Fix document_metadata
DROP POLICY IF EXISTS "Users can manage their own document metadata" ON document_metadata;
CREATE POLICY "Allow all operations on document_metadata"
  ON document_metadata FOR ALL
  USING (true) WITH CHECK (true);

-- Fix document_rows
DROP POLICY IF EXISTS "Users can manage their own document rows" ON document_rows;
CREATE POLICY "Allow all operations on document_rows"
  ON document_rows FOR ALL
  USING (true) WITH CHECK (true);
```

---

## Why This Happened

Your current policies look like this:

```sql
-- Current policy (BROKEN for DELETE)
CREATE POLICY "Enable read access to company documents"
  ON company_documents
  FOR SELECT  -- ⚠️ Only allows SELECT, not DELETE!
  USING (true);
```

This policy **only allows SELECT** operations. When n8n tries to DELETE, Supabase blocks it.

---

## Verify the Fix

After running the SQL above, test with this query:

```sql
-- This should return your new policy
SELECT
  tablename,
  policyname,
  cmd,  -- Should show 'ALL' or 'DELETE'
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'company_documents';
```

Expected output:
```
tablename          | policyname                              | cmd
-------------------|-----------------------------------------|-----
company_documents  | Allow all operations on company_documents | ALL
```

---

## Alternative: Check Your n8n Credentials

If you want to keep strict RLS, verify you're using the **Service Role Key** in n8n, not the **Anon Key**.

1. Go to Supabase Dashboard → Settings → API
2. Copy the **`service_role`** key (not `anon` key)
3. In n8n, update your Supabase credential:
   - **Supabase URL:** `https://[PROJECT].supabase.co`
   - **Supabase Key:** `[SERVICE_ROLE_KEY]` ← Must use this!

The service role key **bypasses RLS** and has full permissions.

---

## For Ross/Nishant/Other Clients

Send them this SQL script to run in Supabase SQL Editor:

```sql
-- Fix RLS permissions for n8n workflow

-- company_documents table
DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;
CREATE POLICY "Allow all operations on company_documents"
  ON company_documents FOR ALL USING (true) WITH CHECK (true);

-- document_metadata table
DROP POLICY IF EXISTS "Users can manage their own document metadata" ON document_metadata;
CREATE POLICY "Allow all operations on document_metadata"
  ON document_metadata FOR ALL USING (true) WITH CHECK (true);

-- document_rows table
DROP POLICY IF EXISTS "Users can manage their own document rows" ON document_rows;
CREATE POLICY "Allow all operations on document_rows"
  ON document_rows FOR ALL USING (true) WITH CHECK (true);

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ RLS policies updated!';
  RAISE NOTICE 'Your n8n workflow should now work.';
END $$;
```

---

## Updated Bootstrap Script

Good news: I already included the correct policies in `bootstrap_supabase.sql`:

```sql
CREATE POLICY "Service role can manage company_documents"
  ON company_documents FOR ALL USING (true);
```

But your existing database has old restrictive policies. Running the bootstrap script again will add the new policy, but won't remove the old one.

**To fully fix existing deployments**, run this cleanup script first:

```sql
-- Remove ALL existing policies
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname, tablename
    FROM pg_policies
    WHERE tablename IN (
      'company_documents',
      'document_metadata',
      'document_rows'
    )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename);
  END LOOP;
END $$;

-- Then re-run bootstrap_supabase.sql to add correct policies
```

---

## Summary

**The issue:** RLS policies blocking DELETE operations
**The fix:** Update policies to allow ALL operations
**Time to fix:** 2 minutes (copy/paste SQL)
**Clients affected:** Anyone with existing Supabase setup

This is separate from the "missing tables" issue - clients may have BOTH problems!

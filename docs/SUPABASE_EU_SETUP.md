# Supabase Setup for EU Regions

EU Supabase projects have different connection string formats than US projects. Here's how to configure them correctly.

## The Problem

You're seeing this error:
```
password authentication failed for user "postgres"
```

This happens because **EU regions** require a different connection string format than **US regions**.

## Quick Fix

### Current (Wrong) Format:
```bash
postgresql://postgres.urnpwymzdsucfxnqitef:b3UNr9IjTlA99z8T@aws-1-eu-west-3.pooler.supabase.com:6543/postgres
```

### Correct Format:
```bash
postgresql://postgres:b3UNr9IjTlA99z8T@aws-1-eu-west-3.pooler.supabase.com:6543/postgres
```

**Key change:** Remove `.urnpwymzdsucfxnqitef` from the username.

The username should be just `postgres`, not `postgres.xxx`.

## Why This Happens

Supabase provides two types of connection poolers:

### 1. Session Pooler (Default)
- Username format: `postgres.{project-ref}`
- Example: `postgres.urnpwymzdsucfxnqitef`
- **Issue:** Doesn't work well with serverless environments like Replit

### 2. Transaction Pooler (Recommended for Replit)
- Username format: `postgres` (just postgres, no suffix)
- **This is what we need!**

## How to Get the Correct URL

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **Project Settings** (gear icon)
4. Click **Database** in the left sidebar
5. Scroll to **Connection String**
6. Select **"Transaction pooler"** from the dropdown (NOT "Session pooler")
7. You'll see something like:

**For US regions:**
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:6543/postgres
```

**For EU regions:**
```
postgresql://postgres:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

8. Replace `[YOUR-PASSWORD]` with your actual database password

## Getting Your Database Password

If you don't know your database password:

1. Go to Project Settings → Database
2. Scroll to **Database Password**
3. Click **Reset Database Password** if needed
4. Copy the new password immediately (you won't see it again!)

## Final Connection String Format

Based on your region (`aws-1-eu-west-3`), your connection string should be:

```bash
SUPABASE_DB_URL=postgresql://postgres:YOUR-ACTUAL-PASSWORD@aws-1-eu-west-3.pooler.supabase.com:6543/postgres
```

Replace `YOUR-ACTUAL-PASSWORD` with your database password from Supabase.

## Verify It Works

After updating, run:

```bash
python tests/test_supabase_connection.py
```

This will:
- ✅ Check the connection string format
- ✅ Test API connection (SUPABASE_URL + SUPABASE_KEY)
- ✅ Test direct DB connection (SUPABASE_DB_URL)
- ✅ Show specific error messages if something is wrong

## Common Mistakes

### ❌ Wrong: Using Session pooler username
```bash
postgresql://postgres.urnpwymzdsucfxnqitef:password@...
```

### ✅ Correct: Using just "postgres"
```bash
postgresql://postgres:password@...
```

---

### ❌ Wrong: Port 5432 (Direct connection)
```bash
postgresql://postgres:password@aws-1-eu-west-3.pooler.supabase.com:5432/postgres
```

### ✅ Correct: Port 6543 (Transaction pooler)
```bash
postgresql://postgres:password@aws-1-eu-west-3.pooler.supabase.com:6543/postgres
```

---

### ❌ Wrong: Forgetting to replace [YOUR-PASSWORD]
```bash
postgresql://postgres:[YOUR-PASSWORD]@...
```

### ✅ Correct: Actual password
```bash
postgresql://postgres:b3UNr9IjTlA99z8T@...
```

## Region-Specific Patterns

Different EU regions have slightly different formats:

| Region | Format |
|--------|--------|
| EU West 1 | `aws-0-eu-west-1.pooler.supabase.com:6543` |
| EU West 2 | `aws-0-eu-west-2.pooler.supabase.com:6543` |
| EU West 3 | `aws-0-eu-west-3.pooler.supabase.com:6543` |
| EU Central 1 | `aws-0-eu-central-1.pooler.supabase.com:6543` |

**Note:** Your connection string shows `aws-1-eu-west-3` which is slightly different (has `1` instead of `0`). This is fine - use whatever Supabase shows you in the Transaction pooler connection string.

## Still Having Issues?

If you're still getting authentication errors after fixing the username:

1. **Reset your database password:**
   - Project Settings → Database → Reset Database Password
   - Copy the new password immediately

2. **Double-check you're using Transaction pooler:**
   - Look for the dropdown that says "Session pooler" and change it to "Transaction pooler"
   - The connection string should change when you select it

3. **Run the diagnostic:**
   ```bash
   python tests/test_supabase_connection.py
   ```

4. **Check for typos:**
   - Password copied correctly?
   - No extra spaces?
   - Correct port (6543)?

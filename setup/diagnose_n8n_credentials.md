# 🔍 Diagnose n8n Supabase Credential Issues

## Quick Check: Is Your Supabase Key Correct?

If you're getting **"permission denied"** errors in n8n, your Supabase credential is likely wrong.

---

## How to Check Your n8n Supabase Credential

### Step 1: Open Your Supabase Credential in n8n

1. In n8n, go to **Settings** → **Credentials**
2. Find your **Supabase API** credential
3. Click to edit it

### Step 2: Check the Key Format

Look at the **Supabase Key** field. What does it look like?

#### ❌ WRONG (Will Cause Permission Errors):

```
anon_key_1234567890
```
```
public_key_abcdef
```
```
sb_secret_ti9hY-MRXkJBPhAoikX_nA_Yy9RqZHW
```
```
Bearer eyJhbGci...
```

**Problems:**
- Too short (< 100 characters)
- Has `anon` or `public` in the name
- Starts with `sb_secret_` (this is a placeholder, not real key)
- Has `Bearer ` prefix (remove it)

#### ✅ CORRECT (Service Role Key):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRleXF3cm94dXRkZWJ6ZmNoenpwYiIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE3MzY3OTk1OTUsImV4cCI6MjA1MjM3NTU5NX0.1234567890abcdefghijklmnopqrstuvwxyz
```

**Characteristics:**
- Very long (300-500 characters)
- Starts with `eyJ`
- Has two `.` dots separating three parts
- Contains `"role":"service_role"` when decoded

---

## How to Get the Correct Key

### Step 1: Go to Supabase Dashboard

1. Open your Supabase project
2. Go to **Settings** (left sidebar, bottom)
3. Click **API**

### Step 2: Copy the Service Role Key

Scroll down to **Project API keys** section. You'll see:

```
┌─────────────────────────────────────────────────┐
│ anon public                                     │
│ eyJhbGci...ABC123 (shorter)                     │  ❌ Don't use this
│                                                 │
│ service_role secret                             │
│ eyJhbGci...XYZ789 (longer, has more chars)      │  ✅ Use this one!
└─────────────────────────────────────────────────┘
```

**Copy the `service_role` key** (the long one labeled "secret")

### Step 3: Update n8n Credential

1. Go back to n8n
2. Edit your **Supabase API** credential
3. **Paste the full service_role key** (no spaces, no "Bearer", just the key)
4. Save

---

## Why This Matters

### Using `anon` key (Public):
- ❌ Subject to Row Level Security (RLS)
- ❌ Can only SELECT (read) by default
- ❌ Cannot DELETE, UPDATE, or INSERT without specific policies
- ❌ Will cause "permission denied" errors

### Using `service_role` key (Secret):
- ✅ Bypasses all RLS policies
- ✅ Full admin access to all tables
- ✅ Can perform all operations (SELECT, INSERT, UPDATE, DELETE)
- ✅ Works immediately without policy configuration

---

## Test Your Credential

After updating the key, test it with this simple workflow:

1. Create a new workflow in n8n
2. Add a **Supabase** node
3. Operation: **Get All**
4. Table: `company_documents`
5. Execute the node

**Expected result:**
- ✅ Returns rows (or empty array if table is empty)
- ❌ "permission denied" = still using wrong key

---

## Common Mistakes

### 1. Using the Anon Key Instead of Service Role

**Wrong:**
```javascript
SUPABASE_KEY = "eyJ...anon_key..."  // Has "anon" in role
```

**Right:**
```javascript
SUPABASE_KEY = "eyJ...service_role..."  // Has "service_role" in role
```

### 2. Truncating the Key

**Wrong:**
```javascript
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX..."  // Cut off
```

**Right:**
```javascript
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRleXF3cm94dXRkZWJ6ZmNoenpwYiIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE3MzY3OTk1OTUsImV4cCI6MjA1MjM3NTU5NX0.FULL_KEY_HERE"  // Complete
```

### 3. Adding "Bearer" Prefix

**Wrong:**
```javascript
SUPABASE_KEY = "Bearer eyJ..."
```

**Right:**
```javascript
SUPABASE_KEY = "eyJ..."  // No "Bearer" prefix
```

---

## Decode Your Key to Verify

Want to check what's in your key? Decode it:

1. Go to https://jwt.io
2. Paste your key in the "Encoded" box
3. Look at the "Payload" section

**Service role key payload:**
```json
{
  "iss": "supabase",
  "ref": "your-project-ref",
  "role": "service_role",  ← Should say "service_role"
  "iat": 1736799595,
  "exp": 2052375595
}
```

**Anon key payload:**
```json
{
  "iss": "supabase",
  "ref": "your-project-ref",
  "role": "anon",  ← Says "anon" = WRONG for n8n
  "iat": 1736799595,
  "exp": 2052375595
}
```

---

## Still Having Issues?

If you've verified:
- ✅ Using service_role key (not anon)
- ✅ Key is complete (not truncated)
- ✅ No "Bearer" prefix
- ✅ Credential saved in n8n

And you still get "permission denied", then check:

1. **RLS policies** - Run the RLS fix script from `FIX_RLS_PERMISSIONS.md`
2. **Supabase URL** - Make sure it matches your project (`https://[project].supabase.co`)
3. **Network access** - Verify n8n can reach Supabase (check firewall/VPN)

---

## Quick Fix Checklist

- [ ] Go to Supabase Dashboard → Settings → API
- [ ] Copy the **service_role** key (not anon)
- [ ] Open n8n → Settings → Credentials → Supabase API
- [ ] Paste the full key (no spaces, no "Bearer")
- [ ] Save credential
- [ ] Re-run workflow
- [ ] Success! 🎉

---

## For Clients: Where to Find This

Send clients to:
1. **Supabase Dashboard**: https://supabase.com/dashboard/project/[PROJECT-ID]/settings/api
2. Copy **service_role** key under "Project API keys"
3. Update in n8n credentials

That's it!

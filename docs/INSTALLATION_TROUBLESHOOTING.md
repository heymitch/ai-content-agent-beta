# Installation Troubleshooting

Quick fixes for common deployment issues.

## Error: "Cannot find module 'pg'"

**Symptoms:**
```
Error: Cannot find module '/home/runner/workspace/node_modules/pg/lib/index.js'
```

**Cause:** Node modules corrupted during installation (common in Replit/containerized environments)

**Solution 1: Use fix-install script (Recommended)**
```bash
npm run fix-install
```

This will:
1. Remove corrupted `node_modules` and `package-lock.json`
2. Perform a clean reinstall
3. Automatically run via `postinstall` hook if `pg` is missing

**Solution 2: Manual cleanup**
```bash
rm -rf node_modules package-lock.json
npm install
npm start
```

**Solution 3: Force reinstall specific packages**
```bash
npm install --no-save --force pg dotenv
npm start
```

---

## Error: "SUPABASE_DB_URL not set"

**Symptoms:**
```
❌ SUPABASE_DB_URL environment variable is not set
```

**Solution:**
Add your Supabase database connection string to:
- **Replit:** Secrets tab → Add `SUPABASE_DB_URL`
- **Local:** `.env` file → `SUPABASE_DB_URL=postgresql://...`

**Getting your connection string:**
1. Go to Supabase project → Settings → Database
2. Copy "Transaction" pooler connection string
3. Format: `postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres`

---

## Error: Python module not found

**Symptoms:**
```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution:**
```bash
pip install -r requirements.txt
```

Or install specific package:
```bash
pip install anthropic
```

---

## Error: Port 5000 already in use

**Symptoms:**
```
Error: Address already in use: 0.0.0.0:5000
```

**Solution:**
```bash
pkill -f uvicorn
npm start
```

Or use the restart script:
```bash
npm run restart
```

---

## Verification Commands

**Check Node modules are installed:**
```bash
npm list pg dotenv
```

**Check Python packages are installed:**
```bash
pip list | grep -E "anthropic|supabase|openai"
```

**Check database connection:**
```bash
npm run validate
```

**Check Supabase tables exist:**
```bash
npm run diagnose
```

---

## Clean Slate (Nuclear Option)

If nothing works, start fresh:

```bash
# 1. Clean all dependencies
rm -rf node_modules package-lock.json
rm -rf __pycache__ .pytest_cache

# 2. Reinstall everything
npm install
pip install -r requirements.txt

# 3. Verify environment variables
cat .env | grep SUPABASE

# 4. Bootstrap database
npm run bootstrap

# 5. Start
npm start
```

---

## Getting Help

**Still stuck?**
1. Check the logs in your terminal for specific error messages
2. Verify all environment variables are set (see `.env.example`)
3. Ensure Supabase project is active and connection string is correct
4. Check Replit console for resource limits (RAM/CPU)

**Common gotchas:**
- ❌ Using Session pooler URL instead of Transaction pooler
- ❌ Missing environment variables in Replit Secrets
- ❌ Supabase project paused due to inactivity
- ❌ Node version <18 (requires Node 18+)

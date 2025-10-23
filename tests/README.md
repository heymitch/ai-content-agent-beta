# Pre-Deployment Test Suite

Run these tests before deploying to client environments to verify all integrations are working correctly.

## Quick Start

**Run all tests in one command:**

```bash
python tests/pre_deploy_test.py
```

This will test:
- ✅ Environment variables (API keys, tokens, URLs)
- ✅ Supabase connection & database operations
- ✅ Airtable connection & record creation
- ✅ RAG search (embeddings + vector similarity)
- ✅ Slack API connection
- ✅ Slack thread session management
- ✅ Content extraction (Haiku)

## Exit Codes

- `0` = All tests passed ✅ Ready to deploy
- `1` = Some tests failed ❌ Fix errors before deploying

## Example Output

```
======================================================================
PRE-DEPLOYMENT INTEGRATION TEST SUITE
======================================================================

======================================================================
TEST 1: Environment Variables
======================================================================
Required Variables:
  ✓ ANTHROPIC_API_KEY: sk-ant-a... (Claude API)
  ✓ SUPABASE_URL: https://... (Supabase connection)
  ...

✅ PASS: All required environment variables set

======================================================================
TEST 2: Supabase Connection & Save
======================================================================
1. Connecting to Supabase...
   ✓ Connected
2. Testing write to generated_posts...
   ✓ Created test record: abc-123
...

✅ PASS: Supabase connection, write, read, delete

...

======================================================================
TEST SUMMARY
======================================================================
Total Tests: 7
Passed: 7
Failed: 0
Warnings: 0
======================================================================

✅ ALL TESTS PASSED - Ready to deploy!
```

## Individual Tests

If you want to test specific components, you can import functions from `pre_deploy_test.py`:

```python
import asyncio
from tests.pre_deploy_test import test_airtable, TestResults

async def main():
    results = TestResults()
    await test_airtable(results)
    results.summary()

asyncio.run(main())
```

## Common Issues

### Environment Variables Missing
**Error:** "Missing required environment variables"

**Fix:** Add to Replit Secrets or `.env` file:
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_DB_URL`
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `AIRTABLE_ACCESS_TOKEN`
- `AIRTABLE_BASE_ID`
- `AIRTABLE_TABLE_NAME`

### Airtable Platform Error
**Error:** "Platform field doesn't have option 'Linkedin'"

**Fix:**
1. Open your Airtable base
2. Click Platform column → Customize field type
3. Add options: `Linkedin`, `X/Twitter`, `Email`, `Youtube`, `Instagram`

### Supabase Connection Failed
**Error:** "Connection failed: connection refused"

**Fix:**
- Check `SUPABASE_URL` format: `https://xxx.supabase.co`
- Check `SUPABASE_KEY` is the `anon` public key
- Check `SUPABASE_DB_URL` format: `postgresql://postgres:[password]@[host]:5432/postgres`

### Slack Auth Failed
**Error:** "Invalid auth"

**Fix:**
- Verify `SLACK_BOT_TOKEN` starts with `xoxb-`
- Verify `SLACK_APP_TOKEN` starts with `xapp-`
- Check tokens haven't been rotated/revoked

## CI/CD Integration

You can run this as part of your deployment pipeline:

```bash
#!/bin/bash
# deploy.sh

echo "Running pre-deployment tests..."
python tests/pre_deploy_test.py

if [ $? -eq 0 ]; then
    echo "Tests passed! Deploying..."
    # Your deployment commands here
else
    echo "Tests failed! Blocking deployment."
    exit 1
fi
```

## What Gets Created/Deleted

The test suite creates temporary records to verify write access:

**Supabase `generated_posts` table:**
- Creates one test record
- Immediately deletes it after verification

**Airtable:**
- Creates two test records (LinkedIn + Instagram)
- **Does NOT auto-delete** (left for manual verification)
- Records are marked "TEST - Delete Me" in Post Hook field

You should manually delete the Airtable test records after verifying they appear correctly.

## Test Data

All test records are marked with:
- `user_id: 'test_deployment'`
- `created_by_agent: 'pre_deploy_test'`
- Post hooks containing "TEST" or "Delete Me"

This makes them easy to identify and clean up.

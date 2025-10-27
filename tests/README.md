# Pre-Deployment Test Suite

Run these tests before deploying to client environments to verify all integrations are working correctly.

## Test Files Overview

### Integration Tests (Run Before Every Deployment)

**`pre_deploy_test.py`** - Main integration test suite
- Tests actual integrations (Supabase, Airtable, Slack, RAG)
- No dependencies (just Python standard library)
- Safe to run in production environments
- **This is what you run before client deployments**

```bash
python tests/pre_deploy_test.py
```

### Unit Tests (For Development Only)

These require `pytest` and are for development/testing new features:

- **`test_instagram_sdk.py`** - Tests Instagram SDK agent tools (generate_5_hooks, create_caption_draft, etc.)
- **`test_cowriting_workflow.py`** - Tests CMO co-writing tools (generate_post_*, quality_check_*, apply_fixes_*)
- **`test_validation_integration.py`** - Tests validation workflow

**To run unit tests (development only):**
```bash
pytest tests/test_instagram_sdk.py -v
pytest tests/test_cowriting_workflow.py -v
```

## Quick Start (Pre-Deployment)

**Run all integration tests in one command:**

```bash
python tests/pre_deploy_test.py
```

This will test:
- ✅ Environment variables (API keys, tokens, URLs)
- ✅ Supabase connection & database operations
- ✅ Airtable connection & record creation (tests actual tools!)
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

---

## 🧪 Mock Test Suite (No API Calls)

Complete test coverage for your content generation system **without burning API credits**.

### Why Mock Tests?

Your system has:
- **5 SDK Agents** (LinkedIn, Twitter, Email, YouTube, Instagram)
- **20+ MCP Tools** per platform
- **Batch orchestration** with context learning
- **Complex tool chaining** and error handling

Testing this normally would cost **~$0.20 per test run** and take **2-3 minutes**.
With these mocks: **$0.00** and **~1 second**.

### Mock Test Files

#### 1. `test_full_system_mock.py`
**Complete system integration test**
- Tests all 5 SDK agents
- Validates batch orchestration
- Tests MCP tool flow
- Performance benchmarking

```bash
python3 tests/test_full_system_mock.py
```

#### 2. `test_tool_validation.py`
**MCP tool signature validation**
- Validates all tool contracts
- Tests tool chaining
- Platform workflow validation

```bash
python3 tests/test_tool_validation.py
```

#### 3. `test_batch_orchestrator_mock.py`
**Context learning and orchestration**
- Tests context accumulation
- Sequential vs parallel execution
- Slack metadata flow

```bash
python3 tests/test_batch_orchestrator_mock.py
```

### 💰 Cost Savings

Each mock test run saves:
- **90+ API calls** to Claude
- **~$0.18** in API costs
- **2-3 minutes** of waiting time

If you run tests 10 times per day:
- **900 API calls saved**
- **$1.80 saved daily**
- **30 minutes saved**

### When to Use What

**Use `pre_deploy_test.py`:**
- Before deploying to production
- Testing real integrations
- Verifying credentials

**Use mock tests:**
- During development
- Testing logic changes
- Running CI/CD pipelines
- Debugging workflows

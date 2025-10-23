# Client Deployment Checklist

Quick reference for deploying to new client environments.

## Pre-Deployment (5 minutes)

### 1. Get Client Credentials

Collect from client:
- [ ] Slack Bot Token (`xoxb-...`)
- [ ] Slack App Token (`xapp-...`)
- [ ] Airtable Personal Access Token (`pat...`)
- [ ] Airtable Base ID (`app...`)
- [ ] Airtable Table Name (`tbl...`)

### 2. Set Up Environment

In Replit Secrets (or `.env` file):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_DB_URL=postgresql://postgres:[password]@[host]:5432/postgres

SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

AIRTABLE_ACCESS_TOKEN=pat...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=tbl...

# Optional
OPENAI_API_KEY=sk-...
AYRSHARE_API_KEY=...
```

### 3. Verify Airtable Table Structure

Make sure client's Airtable table has these fields:

| Field | Type | Options |
|-------|------|---------|
| Body Content | Long text | - |
| Platform | Multiple select | `Linkedin`, `X/Twitter`, `Email`, `Youtube`, `Instagram` |
| Status | Single select | `Draft`, `Scheduled`, `Published` |
| Post Hook | Long text | - |
| Publish Date | Date | - |

**Critical:** Platform and Status options must match exactly (case-sensitive)!

## Deployment (2 minutes)

### 4. Deploy to Replit

```bash
cd ~/workspace
git pull origin main
npm install
npm start
```

### 5. Run Pre-Deployment Tests

**Single command to test everything:**

```bash
python tests/pre_deploy_test.py
```

This tests:
- ✅ All environment variables set correctly
- ✅ Supabase connection & database operations
- ✅ Airtable connection & record creation (LinkedIn + Instagram)
- ✅ RAG search functionality
- ✅ Slack API authentication
- ✅ Thread session management
- ✅ Content extraction

**Expected output:**
```
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

**If tests fail:**
- Read the error messages - they include specific fix instructions
- Common issues are covered in [tests/README.md](tests/README.md)
- Fix and re-run until all pass

### 6. Clean Up Test Records

After tests pass:
- [ ] Go to client's Airtable
- [ ] Delete records with "TEST - Delete Me" in Post Hook field
- [ ] There should be 2 test records (LinkedIn + Instagram)

## Post-Deployment Verification (3 minutes)

### 7. Test Live Slack Integration

In client's Slack workspace:

```
@Agent create a LinkedIn post about [topic]
```

**Verify:**
- [ ] Bot responds in thread
- [ ] Post is generated
- [ ] Quality score shown
- [ ] Airtable record created
- [ ] Supabase record created with embedding

### 8. Test Co-Writing Workflow

```
@Agent let's write a LinkedIn post together about [topic]
```

**Verify:**
- [ ] CMO asks clarifying questions
- [ ] Uses `generate_post` tool
- [ ] Offers `quality_check` and `apply_fixes`
- [ ] Can send to calendar with `send_to_calendar`

### 9. Test RAG Search

```
@Agent show me posts about content strategy from the past month
```

**Verify:**
- [ ] Searches both queue and published posts
- [ ] Shows 📅 QUEUE and ✅ PUBLISHED indicators
- [ ] Returns relevant results with quality scores

### 10. Test Platform-Specific Generation

Test each platform the client uses:

```
@Agent create a LinkedIn post about [topic]
@Agent create an Instagram caption about [topic]
@Agent create a Twitter thread about [topic]
@Agent create a YouTube description about [topic]
@Agent draft an email about [topic]
```

**Verify:**
- [ ] Correct character limits enforced
- [ ] Platform-specific formatting
- [ ] Saves to Airtable with correct Platform value

## Troubleshooting

### Bot Not Responding
- Check `npm start` logs for errors
- Verify `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are correct
- Make sure bot is invited to the channel

### Airtable Errors
- Run `python test_airtable_simple.py` for detailed diagnosis
- Check Platform field has all required options
- Verify PAT has write permissions

### Supabase Errors
- Check `SUPABASE_URL` format (should be `https://xxx.supabase.co`)
- Verify `SUPABASE_KEY` is the `anon` public key
- Run the Instagram migration: `sql/add_instagram_platform.sql`

### RAG Search Not Working
- Check if posts have embeddings (they're generated automatically)
- Wait 1-2 minutes after first post creation for embedding to process
- Verify `OPENAI_API_KEY` is set (used for embeddings)

## Complete!

✅ Client deployment is complete when:
- All pre-deployment tests pass
- Live Slack test succeeds
- Airtable record visible
- Supabase record with embedding saved
- RAG search returns results

**Estimated total time:** 10-15 minutes per client

## Quick Reference

**Run all tests:** `python tests/pre_deploy_test.py`

**Test just Airtable:** `python test_airtable_simple.py`

**View logs:** Check Replit console or `logs/` folder

**Stop bot:** `Ctrl+C` in Replit console

**Restart bot:** `npm start`

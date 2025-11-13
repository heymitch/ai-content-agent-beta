# Airtable Analytics Sync Setup Guide

Complete guide to setting up bidirectional sync between Airtable (content calendar) and Ayrshare (analytics), using Supabase as the source of truth.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│    AIRTABLE     │  Content Calendar (Posts + Analytics)
│ Content Calendar│
└────────┬────────┘
         │
         │ (2) Analytics
         │     Push Daily
         ▼
┌─────────────────┐
│    SUPABASE     │  Source of Truth for Analytics
│ generated_posts │
└────────┬────────┘
         │
         │ (1) Metrics
         │     Fetch Daily
         ▼
┌─────────────────┐
│   AYRSHARE API  │  Publishing + Engagement Metrics
│  Analytics      │
└─────────────────┘
```

**Daily Flow (6am UTC):**
1. **Ayrshare → Supabase**: Fetch latest engagement metrics from Ayrshare API
2. **Supabase → Airtable**: Push analytics to content calendar

---

## ✅ Prerequisites

### 1. Airtable Fields Setup

Your Airtable base must have these fields in the content calendar table:

**Existing Fields (Already Set Up):**
- Post Hook (Single line text)
- Body Content (Long text)
- Status (Single select)
- Platform (Multiple select)
- Publish Date (Date)
- Suggested Edits (Long text)

**New Analytics Fields (Add These):**

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| **Ayrshare Post ID** | Single line text | - | Unique ID from Ayrshare API |
| **Published URL** | URL | - | Direct link to published post |
| **Impressions** | Number | Integer, Format: 1,000 | Total views/impressions |
| **Engagements** | Number | Integer, Format: 1,000 | Total engagements (likes+comments+shares+clicks) |
| **Clicks** | Number | Integer, Format: 1,000 | Link clicks |
| **Likes** | Number | Integer, Format: 1,000 | Likes/reactions |
| **Comments** | Number | Integer, Format: 1,000 | Comment count |
| **Shares** | Number | Integer, Format: 1,000 | Shares/retweets |
| **Engagement Rate** | Percent | Precision: 2 decimal places | Engagements / Impressions * 100 |
| **Last Synced** | Date & time | Include time | Last analytics sync timestamp |

**How to Add Fields in Airtable:**
1. Open your content calendar table
2. Click "+ Add field" button (far right column)
3. Select field type from dropdown
4. Name the field exactly as shown above (case-sensitive)
5. Configure options as specified
6. Click "Create field"

### 2. Environment Variables

Add to your `.env` file:

```bash
# Analytics Sync Configuration
SYNC_ANALYTICS_TO_AIRTABLE=true
API_BASE_URL=https://your-api-url.com  # For n8n workflows
SLACK_ANALYTICS_CHANNEL=content-analytics  # Optional: Slack notifications
SLACK_ALERTS_CHANNEL=alerts  # Optional: Error notifications
```

### 3. API Access

Ensure you have:
- ✅ Airtable Access Token with read/write permissions
- ✅ Ayrshare API key (Premium or Business plan for analytics)
- ✅ Supabase URL and key
- ✅ (Optional) Slack Bot Token for notifications

---

## 📦 Installation Steps

### Step 1: Verify Code Files Exist

Check that these files were created:

```bash
# Python sync modules
ls -la integrations/supabase_to_airtable_sync.py
ls -la integrations/airtable_client.py  # Should have update_analytics() method

# API endpoints
ls -la api/sync_endpoints.py

# n8n workflow
ls -la n8n_workflows/ayrshare_to_airtable_analytics.json
```

### Step 2: Register Sync Endpoints

The sync endpoints need to be added to your FastAPI app in `main_slack.py`:

```python
# In main_slack.py

from api.sync_endpoints import router as sync_router

# Add this line with other router registrations
app.include_router(sync_router)
```

### Step 3: Test Python Modules Locally

```bash
# Test sync module
python3 -c "from integrations.supabase_to_airtable_sync import get_sync_status; print(get_sync_status())"

# Test Airtable client
python3 -c "from integrations.airtable_client import get_airtable_client; client = get_airtable_client(); print('Airtable client ready')"
```

### Step 4: Import n8n Workflow

1. **Open n8n**
   - Go to your n8n instance (https://your-n8n-instance.com)

2. **Import Workflow**
   - Click "Add Workflow" → "Import from File"
   - Select `n8n_workflows/ayrshare_to_airtable_analytics.json`
   - Click "Import"

3. **Configure Environment Variables in n8n**
   - Click "Settings" in the workflow
   - Add these variables:
     - `API_BASE_URL`: Your API URL (e.g., `https://your-api.replit.dev`)
     - `SLACK_ANALYTICS_CHANNEL`: Slack channel for success notifications (optional)
     - `SLACK_ALERTS_CHANNEL`: Slack channel for error alerts (optional)

4. **Set Up Slack Credentials (Optional)**
   - Click on "Success Notification (Slack)" node
   - Add Slack credentials if not already configured
   - Same for "Error Notification (Slack)" node
   - Or delete these nodes if you don't want Slack notifications

5. **Activate Workflow**
   - Toggle "Active" switch in top right
   - Workflow will run daily at 6:00 AM UTC

---

## 🧪 Testing

### Manual Test: Sync Analytics

#### Option 1: Via API Endpoint

```bash
# Trigger Airtable sync
curl -X POST "https://your-api.com/api/sync/analytics-to-airtable" \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 7,
    "force_resync": false
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "synced": 15,
  "errors": 0,
  "total_posts": 15,
  "total_impressions": 45000,
  "total_engagements": 3200
}
```

#### Option 2: Via Python Script

```python
import asyncio
from integrations.supabase_to_airtable_sync import bulk_sync_analytics_to_airtable

async def test():
    result = await bulk_sync_analytics_to_airtable(days_back=7)
    print(result)

asyncio.run(test())
```

#### Option 3: Via n8n

1. Open the imported workflow in n8n
2. Click "Execute Workflow" button (top right)
3. Watch nodes execute in sequence
4. Check "Step 2: Supabase → Airtable" node output

### Verify in Airtable

1. Open your Airtable content calendar
2. Find a recently published post (Status = "Published")
3. Check the analytics fields:
   - ✅ Impressions should have a number
   - ✅ Engagements should have a number
   - ✅ Last Synced should have today's timestamp

### Check Sync Status

```bash
# Get sync health status
curl "https://your-api.com/api/sync/status"
```

**Expected Response:**
```json
{
  "last_sync": "2025-11-13T06:00:15Z",
  "posts_with_analytics": 145,
  "posts_pending_sync": 3,
  "status": "healthy"
}
```

---

## 🔄 Daily Workflow

### Automated Schedule (6am UTC)

1. **6:00 AM**: n8n Schedule Trigger fires
2. **6:00 AM**: Ayrshare → Supabase sync runs
   - Fetches latest metrics from Ayrshare API
   - Updates `generated_posts` table in Supabase
3. **6:02 AM**: Supabase → Airtable sync runs
   - Reads analytics from `generated_posts`
   - Updates Airtable content calendar records
4. **6:05 AM**: Slack notification sent (optional)

### Manual Sync (On-Demand)

If you need to sync immediately:

```bash
# Trigger both syncs
curl -X POST "https://your-api.com/api/sync-ayrshare-metrics" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 30, "force_resync": false}'

curl -X POST "https://your-api.com/api/sync/analytics-to-airtable" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "force_resync": true}'
```

---

## 🐛 Troubleshooting

### Issue 1: "No posts found to sync"

**Cause:** Posts don't have `airtable_record_id` in Supabase

**Solution:**
1. Check Supabase `generated_posts` table
2. Verify records have `airtable_record_id` populated
3. If missing, content was created before Airtable integration

**Fix:**
```sql
-- Check posts without Airtable link
SELECT id, content_preview, created_at
FROM generated_posts
WHERE status = 'published'
  AND airtable_record_id IS NULL
LIMIT 10;
```

### Issue 2: Airtable Update Fails (403 Permission Error)

**Cause:** Airtable Access Token doesn't have write permissions

**Solution:**
1. Go to https://airtable.com/create/tokens
2. Edit your Access Token
3. Ensure these scopes are enabled:
   - ✅ `data.records:read`
   - ✅ `data.records:write`
4. Regenerate token and update `.env` file

### Issue 3: Analytics Show as 0

**Possible Causes:**
1. **Post Too Recent**: Analytics take 24-48 hours to populate on Twitter/LinkedIn
2. **Ayrshare Plan**: Premium plan may not include detailed analytics
3. **Post Deleted**: Post was deleted from social platform

**Check:**
```bash
# Verify Ayrshare has analytics
curl "https://your-api.com/api/sync-ayrshare-metrics" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"days_back": 30}'
```

**Test Specific Post:**
```python
from integrations.ayrshare_client import AyrshareClient

client = AyrshareClient()
analytics = client.get_post_analytics("ayrshare_post_id_here")
print(analytics)
```

### Issue 4: "Field 'Impressions' does not exist"

**Cause:** Analytics fields not created in Airtable

**Solution:**
1. Go back to "Prerequisites" section above
2. Add all analytics fields listed in the table
3. Field names must match exactly (case-sensitive)

### Issue 5: Engagement Rate Shows as 0.00%

**Cause:** Airtable percent field expects value between 0-1, not 0-100

**Check Code:**
In `integrations/airtable_client.py`, the `update_analytics()` method should have:
```python
# Convert percentage to decimal (0-100 → 0-1)
fields['Engagement Rate'] = rate / 100 if rate > 1 else rate
```

This is already implemented correctly.

---

## 📊 Monitoring

### Check Sync Health

```bash
# Daily health check
curl "https://your-api.com/api/sync/status"
```

**Status Values:**
- `healthy`: Everything working normally
- `warning`: Never synced OR >10 posts pending
- `error`: System error occurred

### View Recent Syncs in Airtable

1. Open content calendar
2. Sort by "Last Synced" (descending)
3. Top posts should show today's date if sync is working

### Supabase Dashboard

1. Open Supabase project
2. Go to Table Editor → `generated_posts`
3. Filter: `status = 'published' AND last_analytics_sync IS NOT NULL`
4. Check `last_analytics_sync` column for recent timestamps

---

## 🔐 Security Notes

### API Endpoints

The sync endpoints are unauthenticated by default. For production:

**Option 1: Add API Key Authentication**
```python
# In api/sync_endpoints.py
from fastapi import Header, HTTPException

@router.post("/analytics-to-airtable")
async def sync_analytics_to_airtable_endpoint(
    request: SyncAnalyticsRequest,
    x_api_key: str = Header(...)
):
    if x_api_key != os.getenv('SYNC_API_KEY'):
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ... rest of code
```

**Option 2: Use n8n Webhook Authentication**
- n8n webhooks can have built-in authentication
- Set `Authentication` in HTTP Request node settings

### Airtable Token Security

- Never commit `.env` file to Git
- Rotate Airtable tokens every 90 days
- Use separate tokens for dev/prod environments

---

## 📈 Next Steps

### Optional Enhancements

1. **Add More Platforms**
   - Instagram analytics
   - TikTok analytics
   - YouTube analytics

2. **Custom Dashboards**
   - Build Airtable views sorted by Engagement Rate
   - Create charts showing performance trends
   - Filter by Platform to compare channels

3. **Automated Insights**
   - Add AI analysis of top-performing posts
   - Generate weekly reports
   - Identify best posting times

4. **Bidirectional Publishing**
   - Airtable Status = "Publish It!" → Auto-publish via Ayrshare
   - Update Airtable with Ayrshare Post ID after publish

---

## 📞 Support

If you encounter issues:

1. Check logs in your API server
2. Verify n8n workflow execution history
3. Test endpoints with curl commands above
4. Review Airtable field names (case-sensitive)

**Common Log Locations:**
- FastAPI: `main_slack.py` console output
- n8n: Workflow execution history
- Supabase: Dashboard → Logs

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0

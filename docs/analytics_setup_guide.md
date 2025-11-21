# Analytics Setup Guide

Complete guide to enabling and using the analytics system in your AI content agent.

## 📊 What's Already Built

### ✅ Infrastructure
- **Database**: `performance_analytics` table in Supabase (created by bootstrap)
- **Config**: `config/analytics_config.py` with environment-based settings
- **Handlers**:
  - `slack_bot/analytics_handler.py` - Analyzes post performance using Claude
  - `slack_bot/briefing_handler.py` - Generates weekly intelligence briefings
- **Endpoints**:
  - `POST /api/analyze-performance` - Analyze specific posts
  - `POST /api/generate-briefing` - Generate weekly briefing
- **Integrations**:
  - Airtable (for post data)
  - Ayrshare (for social media engagement metrics)
  - Mock data support (for testing)

### ✅ Database Schema
```sql
performance_analytics
├── id (UUID)
├── content_id (UUID) - Links to content_examples
├── platform (TEXT) - twitter, linkedin, etc.
├── content (TEXT) - The post content
├── quality_score (INTEGER) - 0-25 from quality_check
├── quality_breakdown (JSONB) - Detailed scoring
├── published (BOOLEAN)
├── published_at (TIMESTAMP)
├── impressions, clicks, likes, comments, shares (INTEGER)
├── engagement_rate (DECIMAL)
└── user_id, thread_ts, created_at, etc.
```

---

## 🚀 What's Needed to Make It Functional

### 1. Enable Analytics in Environment

Add to your `.env` or Replit Secrets:

```bash
# Core settings
ANALYTICS_ENABLED=true
ANALYTICS_AUTO_BRIEFING=false  # Optional: weekly auto-reports
ANALYTICS_BRIEFING_DAY=monday
ANALYTICS_BRIEFING_TIME=09:00
ANALYTICS_BRIEFING_CHANNEL=content-strategy

# Data sources
ANALYTICS_USE_AIRTABLE=true
ANALYTICS_USE_AYRSHARE=false  # Optional: real social metrics
ANALYTICS_USE_MOCK_DATA=true  # Fallback when no real data

# Analysis params
ANALYTICS_MIN_POSTS=5
ANALYTICS_DAYS_LOOKBACK=7
ANALYTICS_INCLUDE_TRENDING=true

# Performance thresholds
ANALYTICS_HIGH_ENGAGEMENT=8.0
ANALYTICS_LOW_ENGAGEMENT=3.0
```

### 2. Set Up Data Collection Pipeline

**Option A: Manual Data Entry**
- After publishing posts, manually add performance data to Supabase `performance_analytics` table
- Include: platform, content, impressions, engagement_rate, published_at

**Option B: Airtable Integration (Recommended)**
- Already integrated! Your Airtable setup includes performance fields
- Ensure Airtable has these columns:
  - `Platform` (twitter, linkedin, etc.)
  - `Content` (the post text)
  - `Quality Score` (0-25)
  - `Impressions`, `Likes`, `Comments`, `Shares`
  - `Engagement Rate` (calculated or manual)
  - `Published Date`
- Analytics will pull from Airtable automatically

**Option C: Ayrshare API (Best for Real-Time)**
- Get an Ayrshare API key: https://www.ayrshare.com/
- Add to environment: `AYRSHARE_API_KEY=your_key_here`
- Set `ANALYTICS_USE_AYRSHARE=true`
- Ayrshare provides real-time social media metrics

### 3. Create Analytics Tools for Agent

Add these tools so your agent can record and query analytics:

#### Tool: `record_performance`
```python
async def record_performance(
    platform: str,
    content: str,
    quality_score: int,
    impressions: Optional[int] = None,
    engagement_rate: Optional[float] = None,
    published_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record performance data for a published post.

    Args:
        platform: twitter, linkedin, etc.
        content: The post text
        quality_score: 0-25 from quality_check
        impressions: View count
        engagement_rate: (likes + comments + shares) / impressions * 100
        published_url: URL to the published post

    Returns:
        Confirmation with record ID
    """
    # Insert into performance_analytics table
    # Return success message
```

#### Tool: `get_top_performers`
```python
async def get_top_performers(
    platform: Optional[str] = None,
    days_back: int = 7,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get top performing posts by engagement rate.

    Useful for identifying what content resonates with audience.
    """
    # Query performance_analytics
    # ORDER BY engagement_rate DESC
    # Return top posts with metrics
```

#### Tool: `analyze_performance_trends`
```python
async def analyze_performance_trends(
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Get strategic insights on post performance.

    Uses Claude to analyze patterns and provide recommendations.
    Calls /api/analyze-performance endpoint.
    """
    # Fetch posts from last N days
    # Call analytics_handler.analyze_performance()
    # Return insights
```

### 4. Wire Up Slack Commands

Add slash command or message handler:

```python
# In main_slack.py or claude_agent_handler.py

@app.message(regexp="^(show|analyze) analytics")
async def handle_analytics_request(message, say, client):
    """Handle "show analytics" or "analyze analytics" messages."""

    # Check if analytics enabled
    if not is_analytics_enabled():
        await say("Analytics is not enabled. Set ANALYTICS_ENABLED=true")
        return

    # Fetch recent posts
    posts = await fetch_posts_from_airtable(days_back=7)

    # Analyze
    from slack_bot.analytics_handler import analyze_performance
    analysis = await analyze_performance(
        posts=posts,
        date_range={"start": "...", "end": "..."}
    )

    # Format and send
    formatted = format_analytics_report(analysis)
    await say(formatted)
```

**Example Slack Usage:**
```
User: show analytics
Bot: 📊 Analytics for Jan 20-27 (7 days)

📈 Top Performers:
1. "I replaced 3 workflows..." (8.2% engagement, 1.2K likes)
2. "Here's why AI agents..." (7.5% engagement, 980 likes)

📉 Needs Improvement:
1. "5 tips for..." (2.1% engagement)

💡 Recommendations:
- Your "I replaced X with Y" hooks perform 3x better
- LinkedIn posts outperform Twitter by 40%
- Posts published 9-11am get 2x more engagement
```

### 5. Set Up Weekly Briefings (Optional)

**Option A: n8n Automation**
1. Create n8n workflow with Schedule Trigger (every Monday 9am)
2. Add HTTP Request node:
   ```
   POST https://your-domain.com/api/generate-briefing
   Headers: Authorization: Bearer YOUR_SECRET (if using N8N_WEBHOOK_SECRET)
   Body: {
     "days_back": 7,
     "slack_channel": "content-strategy",
     "include_ayrshare": true
   }
   ```

**Option B: Cron Job**
```bash
# Add to server crontab
0 9 * * 1 curl -X POST https://your-domain.com/api/generate-briefing
```

**Option C: Enable Auto-Briefing**
```bash
# In .env
ANALYTICS_AUTO_BRIEFING=true
ANALYTICS_BRIEFING_DAY=monday
ANALYTICS_BRIEFING_TIME=09:00
```

---

## 📝 Implementation Checklist

### Phase 1: Basic Analytics (Manual)
- [ ] Enable `ANALYTICS_ENABLED=true`
- [ ] Manually record 5-10 posts in `performance_analytics` table
- [ ] Test `/api/analyze-performance` endpoint with curl/Postman
- [ ] Verify Claude returns insights

### Phase 2: Automated Data Collection
- [ ] Choose data source: Airtable, Ayrshare, or both
- [ ] Set up API keys and enable in config
- [ ] Test data fetching works
- [ ] Verify engagement_rate calculations

### Phase 3: Agent Integration
- [ ] Add `record_performance` tool
- [ ] Add `get_top_performers` tool
- [ ] Add `analyze_performance_trends` tool
- [ ] Update agent system prompt to mention analytics
- [ ] Test: "What were my top posts this week?"

### Phase 4: Slack Interface
- [ ] Add "show analytics" message handler
- [ ] Format analytics output nicely with emojis
- [ ] Add "weekly briefing" slash command
- [ ] Test in Slack

### Phase 5: Automation (Optional)
- [ ] Set up weekly briefing automation (n8n or cron)
- [ ] Test automatic delivery to Slack
- [ ] Monitor and tune thresholds

---

## 🧪 Testing the System

### Test 1: Manual Data
```bash
# Insert test data
psql $DATABASE_URL -c "
INSERT INTO performance_analytics (platform, content, quality_score, impressions, engagement_rate, published, published_at, user_id)
VALUES
  ('twitter', 'Test post 1', 22, 10000, 8.5, true, NOW() - INTERVAL '2 days', 'test_user'),
  ('linkedin', 'Test post 2', 24, 15000, 9.2, true, NOW() - INTERVAL '3 days', 'test_user'),
  ('twitter', 'Test post 3', 18, 5000, 3.1, true, NOW() - INTERVAL '5 days', 'test_user');
"
```

### Test 2: API Call
```bash
curl -X POST https://your-domain.com/api/analyze-performance \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {
        "hook": "I replaced 3 workflows...",
        "platform": "linkedin",
        "quality_score": 24,
        "impressions": 15000,
        "engagements": 1230,
        "engagement_rate": 8.2,
        "published_at": "2025-01-20"
      }
    ],
    "date_range": {
      "start": "2025-01-20",
      "end": "2025-01-27"
    }
  }'
```

### Test 3: Slack Command
```
User in Slack: show analytics for last week
```

---

## 🔧 Troubleshooting

### Issue: "No posts to analyze"
- **Cause**: No data in `performance_analytics` table
- **Fix**: Add test data or check Airtable integration

### Issue: "Analytics disabled"
- **Cause**: `ANALYTICS_ENABLED` not set to `true`
- **Fix**: Update environment variables and restart

### Issue: Mock data showing
- **Cause**: `ANALYTICS_USE_MOCK_DATA=true` and no real data available
- **Fix**: Add real performance data or integrate Ayrshare

### Issue: Briefing not generating
- **Cause**: Missing posts or analytics data
- **Fix**: Ensure `ANALYTICS_MIN_POSTS` threshold is met (default: 5)

---

## 📈 Next Steps

Once analytics is functional, you can:
1. **Identify winning patterns**: Which hooks, platforms, times work best
2. **A/B test content**: Compare variations and measure impact
3. **Optimize strategy**: Focus on what's proven to work
4. **Track ROI**: Measure conversions and revenue from posts
5. **Auto-optimize**: Feed insights back into content generation prompts

The system is designed to create a **feedback loop**: Better data → Better insights → Better content → Better data.

# Analytics & Intelligence System - Testing Guide

## Phase 1-4 Complete ✅

This guide shows how to test each endpoint independently and end-to-end.

---

## Prerequisites

```bash
# Ensure environment variables are set
ANTHROPIC_API_KEY=sk-ant-xxx
SLACK_BOT_TOKEN=xoxb-xxx
TAVILY_API_KEY=tvly-xxx  # For agent's web_search tool

# Start the agent
python main_slack.py
```

---

## Phase 1: Analytics Analysis

**Test with sample data:**

```bash
curl -X POST http://localhost:8000/api/analyze-performance \
  -H "Content-Type: application/json" \
  -d @test_analytics_payload.json
```

**Expected Response:**
```json
{
  "summary": "Your engagement is up 15% this week...",
  "top_performers": [
    {
      "hook": "I replaced 3 workflows...",
      "engagement_rate": 8.2,
      "why_it_worked": "Specific Number Hook with concrete outcome..."
    }
  ],
  "worst_performers": [...],
  "patterns": {
    "best_hook_style": "Specific Number Hook (8.2% avg engagement)",
    "best_platform": "LinkedIn (6.1% avg engagement)",
    "best_time": "Tuesday mornings (2.3x avg)",
    "avg_engagement_rate": 5.3
  },
  "recommendations": [
    "Use more Specific Number Hooks - they averaged 8.2% engagement vs 4.1% for Generic hooks",
    ...
  ]
}
```

**What it tests:**
- Claude Sonnet 4.5 performance analysis
- Hook style classification
- Pattern detection
- Data-driven recommendations

---

## Phase 3: Briefing Generation

**Test with sample data:**

```bash
curl -X POST http://localhost:8000/api/generate-briefing \
  -H "Content-Type: application/json" \
  -d @test_briefing_payload.json
```

**Expected Response:**
```json
{
  "briefing_markdown": "# 📊 Weekly Content Intelligence - January 27, 2025\n\n## Performance Highlights\n\n**Your best post this week:**\n...",
  "suggested_topics": [
    "3 ways OpenAI's new API changes enterprise workflows",
    "I analyzed 50 AI adoption failures—here's what worked",
    ...
  ],
  "priority_actions": [
    "Create 5 posts using 'Specific Number Hook' pattern",
    "Write about OpenAI API announcement (trending, relevance: 9)",
    ...
  ]
}
```

**What it tests:**
- Claude Sonnet 4.5 briefing synthesis
- Markdown formatting for Slack
- Strategic recommendations
- Topic suggestions

---

## Phase 4: Slack Posting

**Test posting to Slack:**

```bash
# Replace C12345 with your actual Slack channel ID
curl -X POST http://localhost:8000/api/slack/post-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "message": "# 📊 Test Briefing\n\nThis is a test message from the analytics system."
  }'
```

**Expected Response:**
```json
{
  "thread_ts": "1234567890.123456",
  "channel_id": "C12345",
  "message_url": "https://yourworkspace.slack.com/archives/C12345/p1234567890123456"
}
```

**What it tests:**
- Slack API integration
- Message posting
- Markdown rendering in Slack

---

## End-to-End Test: Option B.2 (Direct API)

**Simulate full n8n workflow:**

```bash
# Step 1: Analyze performance
ANALYTICS=$(curl -s -X POST http://localhost:8000/api/analyze-performance \
  -H "Content-Type: application/json" \
  -d @test_analytics_payload.json)

# Step 2: Generate briefing (using analytics from step 1)
BRIEFING=$(curl -s -X POST http://localhost:8000/api/generate-briefing \
  -H "Content-Type: application/json" \
  -d @test_briefing_payload.json)

# Step 3: Extract briefing_markdown
BRIEFING_TEXT=$(echo "$BRIEFING" | jq -r '.briefing_markdown')

# Step 4: Post to Slack
curl -X POST http://localhost:8000/api/slack/post-message \
  -H "Content-Type: application/json" \
  -d "{
    \"channel_id\": \"C12345\",
    \"message\": $(echo "$BRIEFING_TEXT" | jq -Rs .)
  }"
```

**What it tests:**
- Complete workflow from analytics → briefing → Slack
- Data flow between endpoints
- JSON parsing and formatting

---

## End-to-End Test: Option B.1 (Conversational)

**Simulate n8n triggering agent:**

1. **n8n fetches analytics and calls analyze endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/analyze-performance \
     -H "Content-Type: application/json" \
     -d @test_analytics_payload.json > analytics_result.json
   ```

2. **n8n posts to Slack as user (using Slack API or webhook):**
   ```
   @agent @user here's today's content intelligence report for AI automation and enterprise AI

   Analytics summary: Engagement up 15% this week. Best performer: 'I replaced 3 workflows' (8.2% engagement).

   Can you research trending news in these areas and give me a strategic briefing?
   ```

3. **Agent responds:**
   - Agent sees mention via `/slack/events` webhook
   - Agent uses `web_search` tool to research "AI automation news" and "enterprise AI trends"
   - Agent synthesizes analytics + research
   - Agent replies in thread with full briefing

**What it tests:**
- Conversational workflow
- Agent's web_search tool integration
- Natural language interaction
- Thread continuity

---

## Troubleshooting

**Issue: "ANTHROPIC_API_KEY not found"**
- Ensure `.env` file has `ANTHROPIC_API_KEY=sk-ant-xxx`
- Restart the agent after adding env vars

**Issue: "Failed to parse Claude response as JSON"**
- Check Claude API is responding correctly
- Review logs for full error message
- Claude may have returned markdown code blocks (handler strips these)

**Issue: "Slack API error: invalid_auth"**
- Ensure `SLACK_BOT_TOKEN` is set and valid
- Check bot has permissions: `chat:write`, `chat:write.public`

**Issue: Briefing markdown not rendering in Slack**
- Ensure `mrkdwn: True` is set in Slack API call
- Slack has limited markdown support (no tables, limited formatting)
- Use emoji headers and simple formatting

---

## Performance Benchmarks

**Phase 1 - Analytics Analysis:**
- Input: 6 posts with metrics
- Processing time: 3-5 seconds
- Output: ~500 tokens (JSON)

**Phase 3 - Briefing Generation:**
- Input: Analytics + 3 research articles
- Processing time: 5-8 seconds
- Output: ~1500 tokens (Markdown + JSON)

**Phase 4 - Slack Posting:**
- Processing time: <1 second
- Rate limits: Slack allows ~1 message/second

**End-to-End (Option B.2):**
- Total time: 10-15 seconds
- Rate limits: 3 API calls (analytics, briefing, Slack)

---

## Next Steps: Phase 5 (n8n Integration)

1. **Create n8n workflow:**
   - Schedule node: Monday 9am cron
   - HTTP Request node: Fetch Ayrshare analytics
   - HTTP Request node: POST to `/api/analyze-performance`
   - HTTP Request node: POST to `/api/generate-briefing`
   - Slack node: Post briefing to channel

2. **Add claude.md reader:**
   - File node: Read `claude.md`
   - Code node: Extract user_context (company niche, industry, research topics)
   - Pass to `/api/generate-briefing` as `user_context` field

3. **Test n8n workflow:**
   - Run manually first (don't wait for Monday)
   - Check logs in each node
   - Verify Slack message formatting

4. **Deploy n8n workflow:**
   - Enable cron schedule
   - Monitor for first week
   - Adjust timing/topics based on feedback

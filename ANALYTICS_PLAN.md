# Analytics & Intelligence System Implementation Plan

## Overview

Build REST API endpoints for the agent to:
1. **Analyze performance data** → strategic insights
2. **Research industry trends** → trending topics with relevance
3. **Generate weekly briefings** → Markdown for Slack
4. **Post proactively to Slack** → Monday morning intelligence

**n8n handles:** Scheduling, Ayrshare fetching, data aggregation
**Agent handles:** Analysis, research, strategy generation

---

## Branch: `analytics`

**Base:** `main` (merged from fix/content-extraction-and-empty-messages)
**Goal:** 4-week implementation → automated Monday briefings
**Status:** Phase 0 starting

---

## Phase 0: Async/Reliability Fixes (Week 1)

**PREREQUISITE - Must be stable before adding features**

### 1. Streaming Timeouts & Reconnection

**File:** `agents/linkedin_sdk_agent.py`

**Problem:** Agent silently hangs for 60+ seconds when Claude streaming stalls

**Solution:**
- Add idle timeout (45-60s) - triggers if no message received
- Add overall deadline (180-240s) - max total time per request
- Implement automatic reconnection on timeout (max 1-2 retries)
- Handle `StopAsyncIteration` cleanly

**Implementation Example:**
```python
aiter = client.receive_response().__aiter__()
start = asyncio.get_event_loop().time()
attempt = 0
idle_timeout = 60  # seconds
overall_deadline = 240  # seconds
max_stream_retries = 2

while True:
    # Check overall deadline
    if asyncio.get_event_loop().time() - start > overall_deadline:
        raise TimeoutError("stream deadline exceeded")

    try:
        # Wait for next message with idle timeout
        msg = await asyncio.wait_for(aiter.__anext__(), timeout=idle_timeout)
        handle_msg(msg)

    except asyncio.TimeoutError:
        # Idle timeout - reconnect and retry
        attempt += 1
        logger.warning(f"Stream idle timeout (attempt {attempt}/{max_stream_retries})")

        if attempt > max_stream_retries:
            raise TimeoutError("Max stream retries exceeded")

        # Recreate session and reconnect
        client = self.get_or_create_session(new_session_id)
        await client.connect()
        await client.query(creation_prompt + "\n[Resume from timeout]")
        aiter = client.receive_response().__aiter__()

    except StopAsyncIteration:
        # Normal completion
        break
```

---

### 2. Background Task Supervision

**File:** `main_slack.py`

**Problem:** Background tasks crash silently, no logging

**Solution:**
- Add `task.add_done_callback` for exception logging
- Create `supervise()` wrapper with auto-restart logic
- Wrap FastAPI BackgroundTasks with try/except

**Implementation Example:**
```python
def supervise(coro, *, name: str, max_restarts: int = 1):
    """Supervise async coroutine with exception logging and optional restart"""
    attempts = 0

    async def runner():
        nonlocal attempts
        while True:
            try:
                return await coro()
            except Exception as e:
                attempts += 1
                logger.exception(
                    f"Background task {name} failed (attempt {attempts})",
                    exc_info=e
                )
                if attempts > max_restarts:
                    logger.error(f"Task {name} exceeded max restarts, giving up")
                    break
                await asyncio.sleep(1.0 * attempts)  # Exponential backoff

    task = asyncio.create_task(runner(), name=name)
    task.add_done_callback(
        lambda t: t.exception() and logger.error(f"Task {name} crashed: {t.exception()}")
    )
    return task

# Usage:
# Replace: asyncio.create_task(queue_manager.wait_for_completion())
# With: supervise(queue_manager.wait_for_completion, name="queue_manager")
```

---

### 3. Health Endpoints

**File:** `main_slack.py`

**Problem:** No way to monitor agent health, Replit suspends due to inactivity

**Solution:**
- Add `/healthz` endpoint (quick 200)
- Add `/readyz` endpoint (checks Anthropic key)
- Optional self-ping loop (opt-in via env var)

**Implementation Example:**
```python
@app.get("/healthz")
async def healthz():
    """Basic health check - always returns 200 if server is up"""
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    """Readiness check - verifies agent can function"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    return {
        "ready": bool(anthropic_key),
        "checks": {
            "anthropic_key": "present" if anthropic_key else "missing"
        }
    }

# Optional self-ping (prevent Replit suspension)
async def self_ping_loop(base_url: str, interval: int = 60):
    """Ping /healthz every N seconds to prevent suspension"""
    if not os.getenv("ENABLE_SELF_PING", "false").lower() == "true":
        return  # Disabled by default

    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                await client.get(f"{base_url}/healthz")
                logger.debug("Self-ping successful")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")
            await asyncio.sleep(interval)

# Start self-ping on app startup
@app.on_event("startup")
async def startup():
    if os.getenv("ENABLE_SELF_PING") == "true":
        asyncio.create_task(self_ping_loop("http://localhost:8000"))
```

---

### Deliverable: Phase 0

- ✅ No silent hangs (all requests timeout within 240s)
- ✅ All background task failures logged
- ✅ `/healthz` and `/readyz` endpoints working
- ✅ Optional self-ping prevents Replit suspension

**Test:**
```bash
# Test health endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz

# Test LinkedIn post (should timeout gracefully if streaming stalls)
# Logs should show "Stream idle timeout" and reconnection attempt
```

---

## Phase 1: Analytics Analysis Endpoint (Week 2)

### Goal
Agent analyzes raw performance data and returns strategic insights

### New Files
- `slack_bot/analytics_handler.py`
- `prompts/analytics_analysis_prompt.py`

### API Endpoint

```python
POST /api/analyze-performance
Content-Type: application/json

Body:
{
  "posts": [
    {
      "hook": "I replaced 3 workflows...",
      "platform": "linkedin",
      "quality_score": 24,
      "impressions": 15000,
      "engagements": 1230,
      "engagement_rate": 8.2,
      "published_at": "2025-01-20"
    },
    {
      "hook": "Most AI agents fail because...",
      "platform": "linkedin",
      "quality_score": 23,
      "impressions": 12000,
      "engagements": 900,
      "engagement_rate": 7.5,
      "published_at": "2025-01-21"
    }
  ],
  "date_range": {
    "start": "2025-01-20",
    "end": "2025-01-27"
  }
}

Response:
{
  "summary": "Your engagement is up 15% this week. Best performer: 'I replaced 3 workflows' (8.2% engagement vs 5.3% avg)",
  "top_performers": [
    {
      "hook": "I replaced 3 workflows...",
      "engagement_rate": 8.2,
      "why_it_worked": "Specific Number Hook with concrete outcome (3 workflows, 15 hours/week)"
    }
  ],
  "worst_performers": [
    {
      "hook": "AI trends for 2025",
      "engagement_rate": 3.1,
      "why_it_failed": "Generic topic, no personal angle or specificity"
    }
  ],
  "patterns": {
    "best_hook_style": "Specific Number Hook",
    "best_platform": "LinkedIn",
    "best_time": "Tuesday 9am",
    "avg_engagement_rate": 5.3
  },
  "recommendations": [
    "Create more 'Specific Number Hook' posts (8.2% engagement vs 5.3% avg)",
    "Avoid generic AI trends posts (3.1% engagement, -40% vs avg)",
    "Post on Tuesday mornings for best engagement"
  ]
}
```

### Implementation

**File:** `slack_bot/analytics_handler.py`

```python
import os
from anthropic import Anthropic
from typing import List, Dict, Any

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def analyze_performance(posts: List[Dict[str, Any]], date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze post performance data and return strategic insights.

    Uses Claude Sonnet 4.5 to:
    - Identify top/worst performers
    - Detect patterns (hook styles, timing, platforms)
    - Generate actionable recommendations

    Args:
        posts: List of posts with metrics (impressions, engagement, quality_score)
        date_range: Start/end dates for analysis

    Returns:
        Dict with summary, patterns, and recommendations
    """
    from prompts.analytics_analysis_prompt import ANALYTICS_ANALYSIS_PROMPT

    # Format posts as JSON for Claude
    posts_json = json.dumps(posts, indent=2)

    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=ANALYTICS_ANALYSIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Analyze these posts from {date_range['start']} to {date_range['end']}:

{posts_json}

Return JSON with:
- summary (1-2 sentences)
- top_performers (top 3 with why_it_worked)
- worst_performers (bottom 3 with why_it_failed)
- patterns (best_hook_style, best_platform, best_time, avg_engagement_rate)
- recommendations (3-5 actionable items)"""
        }]
    )

    # Parse JSON response
    analysis = json.loads(response.content[0].text)
    return analysis
```

**File:** `prompts/analytics_analysis_prompt.py`

```python
ANALYTICS_ANALYSIS_PROMPT = """You are a content performance analyst. Analyze post metrics and identify patterns.

Your job:
1. Identify top performers (high engagement_rate) and explain WHY they worked
2. Identify worst performers (low engagement_rate) and explain WHY they failed
3. Detect patterns:
   - Hook styles (Specific Number, Contrarian, Bold Outcome, etc.)
   - Best platforms (LinkedIn, Twitter, etc.)
   - Best posting times
   - Average engagement rate
4. Generate actionable recommendations based on data

Focus on:
- Specificity: Posts with numbers/names perform better
- Hook quality: Certain patterns consistently work
- Content angles: Personal stories > generic advice
- Timing: Day of week and time of day matter

Output format: JSON with keys: summary, top_performers, worst_performers, patterns, recommendations

Be concrete and specific. Use actual numbers from the data.
"""
```

**File:** `main.py` (add endpoint)

```python
from slack_bot import analytics_handler

@app.post("/api/analyze-performance")
async def analyze_performance(request: Request):
    """Analyze post performance data and return strategic insights"""
    data = await request.json()

    posts = data.get("posts", [])
    date_range = data.get("date_range", {})

    if not posts:
        return {"error": "No posts provided"}

    analysis = await analytics_handler.analyze_performance(posts, date_range)
    return analysis
```

### Test

```bash
curl -X POST http://localhost:8000/api/analyze-performance \
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
    "date_range": {"start": "2025-01-20", "end": "2025-01-27"}
  }'
```

### Deliverable: Phase 1

- ✅ `/api/analyze-performance` endpoint working
- ✅ Returns JSON with summary, patterns, recommendations
- ✅ Response time < 10 seconds
- ✅ Testable via curl with mock data

---

## Phase 2: Research Trends Endpoint (Week 2)

### Goal
Agent searches industry news and returns relevant insights with content angles

### New Files
- `slack_bot/research_handler.py`

### API Endpoint

```python
POST /api/research-trends
Content-Type: application/json

Body:
{
  "topics": ["AI automation", "enterprise AI", "marketing automation"],
  "days_back": 7,
  "max_results": 10
}

Response:
{
  "trending_topics": [
    {
      "title": "OpenAI launches new API features",
      "url": "https://techcrunch.com/...",
      "summary": "OpenAI released GPT-4.5 Turbo with faster response times and lower costs...",
      "relevance": 9,
      "why_relevant": "Your audience cares about API integrations and cost optimization",
      "content_angle": "How these new features change enterprise workflows (specific examples with before/after)"
    },
    {
      "title": "Enterprise AI adoption doubles in 2025",
      "url": "https://venturebeat.com/...",
      "summary": "New study shows enterprise AI adoption grew 2x year-over-year...",
      "relevance": 8,
      "why_relevant": "Validates the market opportunity for your audience",
      "content_angle": "What's driving the surge? Interview insights from decision makers"
    }
  ],
  "search_queries_used": ["AI automation news 2025", "enterprise AI trends"],
  "sources": ["TechCrunch", "VentureBeat", "Forbes"]
}
```

### Implementation

**File:** `slack_bot/research_handler.py`

```python
import os
from anthropic import Anthropic
from tools.search_tools import tavily_client

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def research_industry_trends(topics: List[str], days_back: int = 7, max_results: int = 10) -> Dict[str, Any]:
    """
    Search industry news via Tavily and synthesize relevant insights.

    Uses:
    - Tavily API for real-time web search
    - Claude to add relevance scores and content angles

    Args:
        topics: List of topics to search (e.g. ["AI automation", "enterprise AI"])
        days_back: How many days to look back
        max_results: Max results to return

    Returns:
        Dict with trending_topics (with relevance, why_relevant, content_angle)
    """
    # Search each topic via Tavily
    all_results = []
    search_queries = []

    for topic in topics:
        query = f"{topic} news {days_back} days"
        search_queries.append(query)

        # Tavily search
        results = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_raw_content=False
        )

        all_results.extend(results.get("results", []))

    # Remove duplicates
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result["url"] not in seen_urls:
            unique_results.append(result)
            seen_urls.add(result["url"])

    # Use Claude to add relevance scores and content angles
    results_json = json.dumps(unique_results[:max_results], indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system="""You are a content strategist analyzing industry news.

For each article:
1. Assign relevance score (0-10) based on how valuable it is for content creators
2. Explain WHY it's relevant to the audience
3. Suggest a SPECIFIC content angle (not generic - include examples, before/after, etc.)

High relevance (8-10): Breaking news, major product launches, paradigm shifts
Medium relevance (5-7): Industry trends, studies, expert insights
Low relevance (1-4): Generic advice, old news, niche topics

Output JSON array with: title, url, summary, relevance, why_relevant, content_angle""",
        messages=[{
            "role": "user",
            "content": f"Analyze these news results and add relevance scores + content angles:\n\n{results_json}"
        }]
    )

    trending_topics = json.loads(response.content[0].text)

    # Sort by relevance (highest first)
    trending_topics.sort(key=lambda x: x["relevance"], reverse=True)

    # Extract unique sources
    sources = list(set([
        urlparse(topic["url"]).netloc.replace("www.", "").split(".")[0].title()
        for topic in trending_topics
    ]))

    return {
        "trending_topics": trending_topics,
        "search_queries_used": search_queries,
        "sources": sources
    }
```

**File:** `main.py` (add endpoint)

```python
from slack_bot import research_handler

@app.post("/api/research-trends")
async def research_trends(request: Request):
    """Search industry news and return relevant insights"""
    data = await request.json()

    topics = data.get("topics", [])
    days_back = data.get("days_back", 7)
    max_results = data.get("max_results", 10)

    if not topics:
        return {"error": "No topics provided"}

    research = await research_handler.research_industry_trends(
        topics=topics,
        days_back=days_back,
        max_results=max_results
    )
    return research
```

### Test

```bash
curl -X POST http://localhost:8000/api/research-trends \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["AI automation", "enterprise AI"],
    "days_back": 7,
    "max_results": 10
  }'
```

### Deliverable: Phase 2

- ✅ `/api/research-trends` endpoint working
- ✅ Returns 5-10 trending topics with relevance scores
- ✅ Each topic has why_relevant and content_angle
- ✅ Response time < 15 seconds

---

## Phase 3: Briefing Generator (Week 3)

### Goal
Combine analytics + research into cohesive Markdown briefing

### New Files
- `slack_bot/briefing_handler.py`
- `prompts/briefing_generator_prompt.py`

### API Endpoint

```python
POST /api/generate-briefing
Content-Type: application/json

Body:
{
  "analytics": {
    "summary": "Engagement up 15%...",
    "patterns": {...},
    "recommendations": [...]
  },
  "research": {
    "trending_topics": [...]
  },
  "user_context": {
    "recent_topics": ["AI agents", "automation"],
    "content_goals": "thought leadership",
    "audience": "enterprise decision makers"
  }
}

Response:
{
  "briefing_markdown": "# 📊 Weekly Content Intelligence - Jan 27, 2025\n\n## Performance Highlights...",
  "suggested_topics": [
    "3 ways OpenAI's new API changes enterprise workflows",
    "I analyzed 50 AI adoption failures—here's what worked"
  ],
  "priority_actions": [
    "Create 5 posts using 'Specific Number Hook' pattern",
    "Write about OpenAI API announcement (trending, relevance: 9)"
  ]
}
```

### Implementation

**File:** `slack_bot/briefing_handler.py`

```python
import os
from anthropic import Anthropic
from typing import Dict, Any

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def generate_briefing(
    analytics: Dict[str, Any],
    research: Dict[str, Any],
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate weekly content intelligence briefing.

    Combines:
    - Analytics insights (what's working)
    - Industry research (what's trending)
    - User context (goals, audience, recent topics)

    Returns:
    - briefing_markdown: Full Markdown briefing for Slack
    - suggested_topics: 5-7 specific content ideas
    - priority_actions: 3-5 immediate next steps
    """
    from prompts.briefing_generator_prompt import BRIEFING_GENERATOR_PROMPT

    # Format inputs as JSON
    analytics_json = json.dumps(analytics, indent=2)
    research_json = json.dumps(research, indent=2)
    context_json = json.dumps(user_context, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=BRIEFING_GENERATOR_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Generate a weekly content intelligence briefing.

**Analytics:**
{analytics_json}

**Industry Research:**
{research_json}

**User Context:**
{context_json}

Return JSON with:
- briefing_markdown (full Markdown briefing for Slack)
- suggested_topics (5-7 specific content ideas)
- priority_actions (3-5 immediate next steps)"""
        }]
    )

    briefing = json.loads(response.content[0].text)
    return briefing
```

**File:** `prompts/briefing_generator_prompt.py`

```python
BRIEFING_GENERATOR_PROMPT = """You are a content strategist generating weekly intelligence briefings.

Your briefing should:

1. **Performance Highlights** (2-3 bullet points)
   - Top post with specific metrics
   - Engagement trend (up/down, percentage)
   - Best hook style with avg engagement

2. **Industry News** (3-5 items)
   - Title + link
   - Why it matters (1 sentence)
   - Content opportunity (specific angle)

3. **Strategic Recommendations** (3-5 items)
   - Data-driven (reference actual metrics)
   - Actionable (specific hook styles, topics, formats)
   - Avoid generic advice

4. **Suggested Topics** (5-7 items)
   - Specific and concrete
   - Mix of: data insights + trending news + user's recent topics
   - Include hook type in parentheses

Tone:
- Direct and actionable
- Use numbers and specifics
- No fluff or generic advice

Format: Clean Markdown with emoji headers (📊, 📰, 💡, 🎯)

Output: JSON with briefing_markdown, suggested_topics, priority_actions
"""
```

**File:** `main.py` (add endpoint)

```python
from slack_bot import briefing_handler

@app.post("/api/generate-briefing")
async def generate_briefing(request: Request):
    """Generate weekly content intelligence briefing"""
    data = await request.json()

    analytics = data.get("analytics", {})
    research = data.get("research", {})
    user_context = data.get("user_context", {})

    if not analytics or not research:
        return {"error": "Missing analytics or research data"}

    briefing = await briefing_handler.generate_briefing(
        analytics=analytics,
        research=research,
        user_context=user_context
    )
    return briefing
```

### Test

```bash
curl -X POST http://localhost:8000/api/generate-briefing \
  -H "Content-Type: application/json" \
  -d '{
    "analytics": {
      "summary": "Engagement up 15%",
      "patterns": {"best_hook_style": "Specific Number Hook"},
      "recommendations": ["Create more Specific Number Hook posts"]
    },
    "research": {
      "trending_topics": [
        {
          "title": "OpenAI launches API",
          "relevance": 9,
          "content_angle": "How this changes workflows"
        }
      ]
    },
    "user_context": {
      "recent_topics": ["AI agents"],
      "content_goals": "thought leadership"
    }
  }'
```

### Deliverable: Phase 3

- ✅ `/api/generate-briefing` endpoint working
- ✅ Returns Markdown formatted for Slack
- ✅ Includes 5-7 suggested topics and 3-5 priority actions
- ✅ Response time < 15 seconds

---

## Phase 4: Proactive Slack Posting (Week 3)

### Goal
Agent can post messages to Slack without user prompt (triggered by n8n)

### Modified Files
- `slack_bot/claude_agent_handler.py`

### API Endpoint

```python
POST /api/slack/post-message
Content-Type: application/json

Body:
{
  "channel_id": "C12345",
  "message": "# 📊 Weekly Content Intelligence\n\n...",
  "thread_ts": null,
  "user_id": "U12345"
}

Response:
{
  "thread_ts": "1234567890.123456",
  "message_url": "https://workspace.slack.com/archives/C12345/p1234567890123456"
}
```

### Implementation

**File:** `slack_bot/claude_agent_handler.py` (add method)

```python
class ClaudeAgentHandler:
    # ... existing code ...

    def post_proactive_message(
        self,
        channel_id: str,
        message: str,
        thread_ts: str = None,
        user_id: str = None
    ) -> Dict[str, str]:
        """
        Post a message to Slack proactively (not replying to user).

        Used by n8n workflows to deliver briefings, alerts, etc.

        Args:
            channel_id: Slack channel ID
            message: Markdown text to post
            thread_ts: Optional thread ID to reply in
            user_id: Optional user ID for attribution/context

        Returns:
            Dict with thread_ts and message_url
        """
        if not self.slack_client:
            raise ValueError("Slack client not initialized")

        result = self.slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            thread_ts=thread_ts,
            mrkdwn=True
        )

        # Store thread_ts for agent context (optional)
        if user_id and result["ts"]:
            # Agent can now respond to messages in this thread
            pass

        return {
            "thread_ts": result["ts"],
            "message_url": f"https://workspace.slack.com/archives/{channel_id}/p{result['ts'].replace('.', '')}"
        }
```

**File:** `main.py` (add endpoint)

```python
from slack_bot.claude_agent_handler import ClaudeAgentHandler

# Initialize handler
handler = ClaudeAgentHandler(
    memory_handler=memory,
    slack_client=slack_client
)

@app.post("/api/slack/post-message")
async def post_slack_message(request: Request):
    """Post message to Slack proactively (triggered by n8n)"""
    data = await request.json()

    channel_id = data.get("channel_id")
    message = data.get("message")
    thread_ts = data.get("thread_ts")
    user_id = data.get("user_id")

    if not channel_id or not message:
        return {"error": "Missing channel_id or message"}

    result = handler.post_proactive_message(
        channel_id=channel_id,
        message=message,
        thread_ts=thread_ts,
        user_id=user_id
    )
    return result
```

### Test

```bash
# Test posting to Slack
curl -X POST http://localhost:8000/api/slack/post-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "message": "# 📊 Test Briefing\n\nThis is a test message from the analytics system.",
    "user_id": "U12345"
  }'

# Verify in Slack:
# 1. Message appears in channel
# 2. Response includes thread_ts
# 3. Agent can respond to messages in that thread
```

### Deliverable: Phase 4

- ✅ `/api/slack/post-message` endpoint working
- ✅ Returns thread_ts for n8n to track
- ✅ Message appears in Slack with correct formatting
- ✅ Agent can respond to messages in that thread

---

## Phase 5: n8n Workflow Integration (Week 4)

### Goal
Automated Monday morning briefings via n8n orchestration

### n8n Workflow Structure

**Workflow Name:** "Weekly Content Intelligence Briefing"

**Trigger:** Schedule - Every Monday at 9:00 AM (user configurable)

**Nodes:**

1. **Schedule Trigger**
   - Cron: `0 9 * * MON`
   - Timezone: User's timezone

2. **Ayrshare: Get History**
   - API call: `GET /history?lastDays=7`
   - Filters: User's platforms
   - Returns: posts with impressions, engagements, etc.

3. **Supabase: Get Quality Scores**
   - Query: `SELECT * FROM generated_posts WHERE published_at >= NOW() - INTERVAL '7 days'`
   - Join with Ayrshare data on post_id
   - Enriches posts with quality_score data

4. **HTTP Request: Analyze Performance**
   - Method: POST
   - URL: `http://your-agent.com/api/analyze-performance`
   - Body: `{"posts": [...], "date_range": {...}}`
   - Returns: analytics insights

5. **HTTP Request: Research Trends**
   - Method: POST
   - URL: `http://your-agent.com/api/research-trends`
   - Body: `{"topics": ["AI automation", "enterprise AI"], "days_back": 7}`
   - Returns: trending topics with relevance

6. **HTTP Request: Generate Briefing**
   - Method: POST
   - URL: `http://your-agent.com/api/generate-briefing`
   - Body: `{"analytics": {...}, "research": {...}, "user_context": {...}}`
   - Returns: briefing_markdown + suggested topics

7. **HTTP Request: Post to Slack**
   - Method: POST
   - URL: `http://your-agent.com/api/slack/post-message`
   - Body: `{"channel_id": "C12345", "message": "{{briefing_markdown}}"}`
   - Returns: thread_ts

8. **Supabase: Save Thread ID** (Optional)
   - INSERT INTO briefing_threads (date, thread_ts, channel_id)
   - For tracking/analytics

### User Customizations

**Easy (Drag-and-Drop):**
- Change schedule (daily, weekly, custom cron)
- Add RSS feeds (industry news sources)
- Add Twitter monitoring (track hashtags, competitors)
- Add email delivery (send briefing as PDF via email node)
- Change Slack channel or DM recipient
- Filter by platform (LinkedIn only, Twitter only)
- Adjust lookback period (7 days, 30 days, 90 days)

**Advanced (with n8n Logic):**
- Conditional briefings (only if metrics drop)
- A/B test briefings (send to test channel first)
- Multi-user support (separate briefings per team member)
- Competitor alerts (notify if competitor posts about X)
- Content calendar integration (sync to Google Calendar)

### Example User Flow

**Monday 9:00 AM:**
```
n8n → Fetch Ayrshare analytics (last 7 days)
   → Get quality scores from Supabase
   → Call agent: /api/analyze-performance
   → Call agent: /api/research-trends
   → Call agent: /api/generate-briefing
   → Call agent: /api/slack/post-message
```

**Agent posts to Slack:**
```markdown
# 📊 Weekly Content Intelligence - Jan 27, 2025

## Performance Highlights
- **Top Post:** "I replaced 3 workflows..." (24/25, 15K impressions, 8.2% engagement)
- **Engagement Trend:** ↑ 15% vs last week
- **Best Hook Style:** Specific Number Hook (avg 7.8% engagement)

## Industry News
1. [OpenAI launches new API features](https://...) - High relevance for your audience
2. [Enterprise AI adoption doubles](https://...) - Opportunity for thought leadership

## Strategic Recommendations
Based on your data, focus on:
- ✅ More "Specific Number Hook" posts (8.2% engagement vs 5.3% avg)
- ✅ Workflow automation stories (proven 8.2% engagement)
- ⚠️ Avoid generic "AI trends" posts (3.1% engagement, -40% vs avg)

## Suggested Topics This Week
1. "3 ways OpenAI's new API changes enterprise workflows"
2. "I analyzed 50 AI adoption failures—here's what worked"
3. Personal story: Your experience with [specific automation win]

Ready to create content? Just say "create 5 posts" and I'll use these insights.
```

**User responds in thread:**
> "Create 7 LinkedIn posts based on these recommendations"

**Agent sees thread context:**
- Original briefing message
- User's command
- Responds using existing batch mode workflow:
  1. `search_company_documents` for proof points
  2. `plan_content_batch` with 7 posts aligned to suggested topics
  3. `execute_post_from_plan` for each post
  4. Posts auto-save to Airtable

### Deliverable: Phase 5

- ✅ n8n workflow running on schedule
- ✅ Briefing posted every Monday 9am (zero manual intervention)
- ✅ User can respond in thread → agent executes batch
- ✅ End-to-end automation working

---

## Success Metrics

### Week 1 (Phase 0): Stability
- ✅ No silent hangs (< 240s timeout for all requests)
- ✅ All background task failures logged with stack traces
- ✅ `/healthz` and `/readyz` return 200
- ✅ Optional self-ping keeps Replit alive

### Week 2 (Phases 1-2): Endpoints
- ✅ Analytics endpoint returns insights in < 10s
- ✅ Research endpoint finds 5-10 relevant articles in < 15s
- ✅ Both endpoints testable via curl with mock data
- ✅ JSON responses match expected schema

### Week 3 (Phases 3-4): Briefing & Slack
- ✅ Briefing endpoint generates Markdown in < 15s
- ✅ Slack posting works, thread_ts returned
- ✅ User can respond in thread, agent sees context
- ✅ Briefing format is clear and actionable

### Week 4 (Phase 5): Full Automation
- ✅ n8n workflow runs on schedule (Monday 9am)
- ✅ Briefing posted every week without manual intervention
- ✅ User responds with content request → batch executes
- ✅ Analytics reflect learning from batch execution
- ✅ Zero errors or missing data in briefings

---

## Dependencies

### Python Packages (Already in requirements.txt)
- `anthropic` - Claude API
- `slack-sdk` - Slack posting
- `fastapi` - REST endpoints
- `httpx` - Async HTTP (for self-ping)
- `tavily-python` - News search

### External Services
- **Anthropic API** - Claude Sonnet 4.5 for analysis
- **Tavily API** - Web search for news
- **Slack API** - Message posting
- **Supabase** - Database for quality scores
- **Ayrshare** - Performance analytics (fetched by n8n, not agent)

### n8n Requirements (User's Environment)
- n8n instance (cloud or self-hosted)
- Ayrshare integration node
- HTTP Request node
- Supabase node (optional)
- Slack node (optional - can use agent's /post-message endpoint)

---

## Configuration

### New Environment Variables

```bash
# Optional - for self-ping in Phase 0
ENABLE_SELF_PING=false  # Set to true to prevent Replit sleep

# Optional - for analytics context
DEFAULT_ANALYTICS_LOOKBACK_DAYS=7
DEFAULT_RESEARCH_MAX_RESULTS=10

# Optional - for briefing customization
BRIEFING_SLACK_CHANNEL=C12345  # Default channel for briefings
```

### Existing Variables (No Changes)
- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `TAVILY_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## Open Questions

1. **Authentication:** Should agent APIs require auth tokens (API keys, JWT)?
   **Recommendation:** Start without auth (internal use), add later if exposing publicly

2. **Rate Limiting:** Should we add rate limits to prevent abuse?
   **Recommendation:** Add basic rate limiting (10 requests/min per IP) in Phase 3

3. **Webhook Support:** Should agent support webhooks from n8n vs polling?
   **Recommendation:** REST APIs are sufficient, webhooks optional for Phase 6

4. **Ayrshare Integration:** Build Ayrshare client in agent or let n8n handle?
   **Recommendation:** Let n8n handle (user customization), agent just analyzes data

5. **User API Keys:** Centralized Ayrshare account or user-provided keys?
   **Recommendation:** User-provided (n8n credentials), keeps agent multi-tenant

---

## Next Steps After Completion

1. Monitor briefing quality (user feedback)
2. Add A/B testing for briefing formats
3. Build Ayrshare client for direct publishing (optional)
4. Add competitor monitoring workflow (n8n + agent)
5. Expand to daily briefings or custom schedules
6. Add email delivery option (Markdown → PDF)
7. Build analytics dashboard (visualize trends over time)

---

**Last Updated:** 2025-01-27
**Branch:** `analytics`
**Status:** Phase 0 starting
**Timeline:** 4 weeks total

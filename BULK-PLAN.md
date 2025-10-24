# Bulk Content Generation Architecture Plan

**Status:** Planning & Research
**Branch:** `feature/bulk-content-generation`
**Goal:** Enable bulletproof bulk content creation (3 posts → month of content)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Current State Analysis](#current-state-analysis)
3. [Target State](#target-state)
4. [Architecture Research](#architecture-research)
5. [Implementation Phases](#implementation-phases)
6. [Month-of-Content Vortex Demo](#month-of-content-vortex-demo)
7. [Testing Strategy](#testing-strategy)
8. [Risk Mitigation](#risk-mitigation)
9. [Success Metrics](#success-metrics)

---

## Problem Statement

### The Bug (from user screenshot):

**User request:** "I want you to create 3 separate linkedin posts. The first 2 should be more motivational and thought provoking while the 3rd should be more tactical."

**What happened:**
1. ✅ Agent responded: "On it..."
2. ❌ Agent never sent follow-up response
3. ❌ Airtable: ONE record with all 3 posts in ONE field (not 3 separate rows)

**Root cause:**
- No progress updates during bulk processing
- Unclear if agent merged posts intentionally or if workflow failed
- User waited with zero feedback

### The Vision:

**User request:** "Create a month of content - mix of LinkedIn thought leadership, Twitter threads, lead magnet emails, and case study carousels. Week 1 should focus on AI ethics, week 2 on remote work productivity..."

**What should happen:**
1. Agent parses request → understands 30+ pieces of content across 4 platforms
2. Agent generates content calendar with specific topics/formats per day
3. Agent queues content in batches (5 at a time to avoid overwhelming)
4. Agent sends progress updates: "Week 1: 3/7 complete [links]"
5. Agent handles user revisions mid-generation: "Actually, change Wednesday's angle to..."
6. Agent tracks contextual post count: 30 planned, 1 revised → still 30 total
7. Final output: Airtable calendar populated with 30 high-quality posts, each in separate row
8. Agent sends summary: "30 posts complete! LinkedIn: 12, Twitter: 10, Email: 5, Carousels: 3"

**This is the magnum opus demo that sells agents.**

---

## Current State Analysis

### ✅ What Works Well

#### 1. Individual SDK Agent Workflows
**Files:** `agents/linkedin_sdk_agent.py`, `agents/twitter_sdk_agent.py`, etc.

**Flow:**
```
User request → CMO agent → delegate_to_workflow → SDK agent → 5-tool workflow → Airtable save → Supabase save → Return structured output
```

**Quality per post:**
- Generate 5 hooks (question/bold/stat/story/mistake)
- Create human draft using Editor-in-Chief standards (127-line rules)
- Inject proof points (NO fabrication)
- Quality check (5-axis rubric + Editor-in-Chief AI tell detection + Tavily fact-check)
- Apply surgical fixes (3-5 specific replacements)
- Validate with GPTZero
- Save to Airtable (separate record) + Supabase (with embedding)

**Duration:** 30-60 seconds per post
**Success rate:** 95%+ (based on testing)

#### 2. ContentQueueManager Architecture
**File:** `agents/content_queue.py`

**Capabilities:**
- AsyncIO queue with semaphore (3 concurrent posts max)
- Retry logic (2 attempts, 5s delay)
- Job status tracking (queued → processing → completed/failed)
- Progress callback mechanism (lines 59, 132, 168, 246)
- Statistics tracking (average time, success/failure counts)

**Current usage:** Called by `_delegate_bulk_workflow` in `claude_agent_handler.py` (line 881)

**Issue:** Progress callback exists but NOT wired to Slack in production

#### 3. Editor-in-Chief Quality Standards
**File:** `editor-in-chief.md` (253 lines)

**Just integrated (2025-10-24):**
- Embedded in all 5 platform quality_check prompts
- Detects AI tells: contrast framing, rule of three, formulaic headers, puffery
- Provides exact replacement text (not AI-generated paraphrases)
- Surgical issues created per violation

**Coverage:** LinkedIn, Twitter, Email, YouTube, Instagram

#### 4. Airtable Save Architecture
**File:** `integrations/airtable_client.py`

**Method:** `create_content_record(content, platform, post_hook, status, suggested_edits)`

**Behavior:**
- Each SDK agent workflow calls this ONCE per post (line 752 in linkedin_sdk_agent.py)
- Creates ONE Airtable record per call
- Platform field maps correctly: 'linkedin' → 'Linkedin', 'twitter' → 'X/Twitter'
- Status always 'Draft' for agent-generated content
- Suggested Edits field contains validation report

**Critical:** This works correctly for single posts. Issue is when CMO agent tries to handle bulk inline.

### ❌ What's Broken/Missing

#### 1. No Slack Progress Updates During Queue Processing

**Current behavior:**
```python
# claude_agent_handler.py, line 881
async def _delegate_bulk_workflow(platform, topics, context, count, style):
    queue_manager = ContentQueueManager(max_concurrent=3)

    # Queue all posts
    for topic in topics:
        await queue_manager.add_job(...)

    # Wait for completion (NO UPDATES SENT TO SLACK)
    await queue_manager.wait_for_completion()

    # Return final result
    return summary
```

**Problem:** User sees "On it..." then nothing for 2-5 minutes

**What's needed:**
- Progress callback wired to Slack client
- Send message on each job start: "⏳ Creating post 1/3..."
- Send message on each job complete: "✅ Post 1/3 done [Airtable link]"
- Send message on errors: "⚠️ Post 2/3 failed, retrying..."
- Send final summary: "🎉 3/3 complete!"

#### 2. No Per-Job Timeout Enforcement

**Current behavior:**
```python
# content_queue.py, line 161
async def _process_job(self, job: ContentJob):
    result = await create_linkedin_post_workflow(...)  # No timeout!
```

**Problem:** If SDK client hangs (network issue, Anthropic API slow), entire queue blocks

**What's needed:**
```python
result = await asyncio.wait_for(
    create_linkedin_post_workflow(...),
    timeout=120  # 2 minutes max per post
)
```

#### 3. CMO Agent Doesn't Detect Bulk Requests Properly

**Current system prompt (line 650 in claude_agent_handler.py):**
```
PHASE 2: Execution (AFTER user confirms)
When user says "yes, create it" or "let's go" or "make all 3":
- For single posts: Call delegate_to_workflow
- For campaigns: Call delegate_campaign (if exists)
```

**Problem:** No explicit handling of "create 3 posts" → agent may try to create all 3 inline

**What's needed:**
- Detect count in user message (regex/NLP: "3 posts", "5 tweets", "a week of content")
- If count > 1: MUST delegate to bulk workflow (don't create inline)
- If count = 1: Use normal delegate_to_workflow

#### 4. No Contextual Post Count Tracking

**Scenario:**
```
User: "Create a week of LinkedIn posts (7 total) - Mon: AI ethics, Tues: Remote work, Weds: Productivity, ..."
Agent: "Great! I'll create 7 posts."
User: "Actually, change Wednesday to focus on time management instead."
Agent: Creates 8 posts (7 original + 1 revised Wednesday)
```

**Problem:** Agent doesn't track "7 total planned" when user revises mid-conversation

**What's needed:**
- Track total count in thread context
- When user revises post N, REPLACE not ADD
- Confirm with user: "Got it, replacing post 3 with new angle. Still 7 total."

#### 5. No Month-of-Content Planning Capability

**Current capability:** Can queue N posts with same prompt template

**What's missing:**
- Calendar generation (30 days → assign topics per day)
- Content variety (mix motivational, tactical, case study, lead magnet)
- Platform rotation (LinkedIn Mon/Wed/Fri, Twitter Tue/Thu, Email weekly)
- Batching (process 5 at a time, not all 30 at once)
- User review checkpoints (generate week 1 → get approval → continue)

---

## Target State

### User Experience Goals

#### Scenario 1: Simple Bulk Request
```
User: "Create 3 LinkedIn posts about AI, remote work, and cybersecurity"

Agent: "On it! Creating 3 LinkedIn posts. I'll update you as each one completes."

[30 seconds later]
Agent: "✅ Post 1/3 complete - AI Ethics in Machine Learning
📊 Airtable: https://airtable.com/app.../rec123
🎯 Quality Score: 22/25"

[60 seconds later]
Agent: "✅ Post 2/3 complete - Remote Work Productivity Hacks
📊 Airtable: https://airtable.com/app.../rec456
🎯 Quality Score: 21/25"

[90 seconds later]
Agent: "✅ Post 3/3 complete - Cybersecurity for SMBs
📊 Airtable: https://airtable.com/app.../rec789
🎯 Quality Score: 20/25"

Agent: "🎉 All done! 3 LinkedIn posts created in 90 seconds.
📅 View in Airtable: [Filter: Created Today]
Average score: 21/25
All posts passed AI detection (GPTZero <30%)"
```

#### Scenario 2: Contextual Revision
```
User: "Create 7 LinkedIn posts for next week - one per day about SaaS metrics"

Agent: "Got it! Creating 7 LinkedIn posts (Mon-Sun) about SaaS metrics."

[Generates 7 posts over 3 minutes with progress updates]

Agent: "✅ 7/7 posts complete!"

User: "Actually, change Wednesday's post to focus on churn prevention instead of MRR."

Agent: "Understood. Replacing post 3 (Wednesday) with new angle on churn prevention. Still 7 total posts."

[Generates 1 revised post]

Agent: "✅ Wednesday post updated!
📊 New Airtable record: [link]
🗑️ Old version archived (marked 'Replaced')
Total: 7 posts (6 originals + 1 revised)"
```

#### Scenario 3: Month-of-Content Vortex (THE DEMO)
```
User: "Create a full month of content for January. Mix LinkedIn thought leadership, Twitter threads, email newsletters, and case study carousels. Focus on AI adoption, remote work, and productivity."

Agent: "Amazing! Let me plan a content vortex for January:
- 30 days of content
- 4 platforms (LinkedIn, Twitter, Email, Carousels)
- 3 themes (AI adoption, remote work, productivity)

I'll break this into 4 weekly batches so you can review as we go. Sound good?"

User: "Perfect, let's do it."

Agent: "🗓️ Week 1 Plan (Jan 1-7):
- Mon: LinkedIn - AI Ethics (thought leadership)
- Tue: Twitter - Remote Work Tips (thread)
- Wed: LinkedIn - Productivity Framework (tactical)
- Thu: Twitter - AI Tools Roundup (thread)
- Fri: LinkedIn - Case Study (carousel post)
- Sat: Email - Weekly Roundup (newsletter)
- Sun: LinkedIn - Motivational (short post)

Creating these 7 posts now..."

[Generates week 1 with progress updates]

Agent: "✅ Week 1 complete! 7/7 posts created.
📅 Airtable filter: [Week 1 Posts]

Ready for Week 2, or want to review/revise any from Week 1 first?"

User: "Week 1 looks great, continue."

[Agent generates weeks 2-4 with same pattern]

Agent: "🎉 MONTH OF CONTENT COMPLETE!

📊 Final Stats:
- Total Posts: 30
- LinkedIn: 15 posts (mix of thought leadership, tactical, case studies)
- Twitter: 8 threads
- Email: 4 newsletters
- Carousels: 3 carousel posts

📈 Quality Metrics:
- Average score: 21/25
- All posts passed AI detection
- 100% fact-checked with Tavily

📅 Content Calendar: https://airtable.com/app.../view123
🚀 Ready to schedule posts in Airtable!"
```

**This demo sells the agent to enterprise clients.**

---

## Architecture Research

### 1. Slack SDK Async Patterns ✅ RESEARCHED

**Research completed:** 2025-10-24

#### AsyncWebClient Support

**Finding:** Slack Python SDK provides `AsyncWebClient` for async/await operations.

```python
from slack_sdk.web.async_client import AsyncWebClient

client = AsyncWebClient(token=os.environ['SLACK_BOT_TOKEN'])

async def send_to_slack(channel, text, thread_ts):
    response = await client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )
```

**Implementation note:** Install optional `aiodns` for faster DNS resolution in async contexts.

#### Rate Limits for chat.postMessage

**Finding:** Tier-based rate limiting with special rules for `chat.postMessage`:

- **General rule:** 1 message per second per channel
- **Burst allowance:** Short bursts over limit are allowed
- **Workspace limit:** Several hundred messages per minute workspace-wide
- **Error handling:** HTTP 429 with `Retry-After` header

**Implication for bulk generation:**
- Sending 1 progress update per 30-60 seconds = well within limits
- For 30 posts, we send ~30 updates over 45 minutes = 0.67 msg/min (SAFE)
- No special handling needed

#### Rate Limit Changes (2025)

**CRITICAL FINDING:** As of May 29, 2025, new non-Marketplace apps have restricted `conversations.history` access:
- **Rate limit:** 1 request/minute (down from Tier 3)
- **Message limit:** 15 messages max per request (down from 100+)

**Impact on our agent:**
- We use `conversations.replies` to get thread context for CMO agent
- If non-Marketplace app: Only 15 messages per request, 1 req/min
- **Mitigation:** We're an internal app (not commercially distributed) → NOT AFFECTED
- **Note:** Existing installations get grace period until March 3, 2026

**Our status:** Internal customer-built application → maintains Tier 3 limits

#### Bot Messages in Context Window

**Finding:** Bot messages appear in `conversations.replies` and are visible to CMO agent.

**Identification methods:**
1. Check `bot_id` field in message
2. Check `subtype == "bot_message"` (for older bots)
3. Check `bot_profile.app_id` (for modern apps)

**Implication:** Progress updates ("✅ Post 1/3 complete") will appear in CMO agent's context unless filtered.

**Recommendation:**
- Filter bot messages when building CMO agent context
- Keep only: user messages + final summaries
- Exclude: "⏳ Creating post X/Y", "✅ Post X/Y complete"

**Implementation:**
```python
# When fetching thread history for CMO agent
thread_messages = client.conversations_replies(channel=channel, ts=thread_ts)
user_messages = [
    msg for msg in thread_messages['messages']
    if not msg.get('bot_id') and msg.get('subtype') != 'bot_message'
]
```

#### Thread Message Ordering

**Finding:** Messages ordered by `ts` (timestamp) - guaranteed chronological order.

**Implication:** Progress updates will appear in sequence, no special handling needed.

### 2. Agent SDK Concurrent Session Handling ✅ RESEARCHED

**Research completed:** 2025-10-24

#### Session Management Options

**Finding:** `ClaudeAgentOptions` provides several session control parameters:

```python
options = ClaudeAgentOptions(
    max_turns=5,                    # Limit conversation turns
    continue_conversation=True,     # Continue most recent conversation
    resume="previous_session_id",   # Resume specific session
    fork_session=True               # Create new session when resuming
)
```

**Implications:**
- `max_turns` prevents infinite loops, but NO explicit timeout parameter
- Each SDK agent workflow should use `continue_conversation=False` for independent posts
- Session IDs prevent interference between concurrent posts

#### Concurrent Client Instances

**Finding:** SDK documentation does NOT specify safe concurrency limits.

**Current implementation analysis:**
```python
# linkedin_sdk_agent.py, line 451
def __init__(self, user_id: str = "default", isolated_mode: bool = False):
    self.sessions = {}  # One client per session_id
```

**Best practices from research:**
- Multiple `ClaudeSDKClient` instances can run in parallel (asyncio tasks)
- Sessions isolated at Python object level (no process-level interference)
- No built-in connection pooling - each client has own HTTP connection

**Recommendation:**
- **Limit to 3 concurrent SDK clients** (current ContentQueueManager setting)
- Monitor memory usage in production
- For month-of-content: Process in batches of 5 to avoid memory pressure

#### Memory Management & Context Window

**Finding:** SDK provides automatic context compaction:

- **Compaction:** Summarizes older turns to preserve intent and open threads
- **CLAUDE.md scratchpad:** Maintains persistent context across sessions
- **Context overflow:** Automatic compaction when approaching token limits
- **Long-running sessions:** SDK handles multi-hour sessions via compaction

**Key insight:** "Compaction summarizes older turns to preserve intent, decisions, and open threads, allowing a Claude agent to keep its edge as the work spans hours."

**Implication for bulk generation:**
- Each post is independent (new session) → no context accumulation
- For month-of-content over 45 minutes: Individual post sessions stay small
- No manual compaction needed

**Resource management features:**
- Control computational resource usage
- Execution timeouts (not explicitly configurable)
- Concurrent operations management

**Estimated memory per active session:** ~50-100MB (not officially documented)

**Recommendation:**
- 3 concurrent clients = ~150-300MB peak memory
- Replit Reserved VM: 8GB RAM (plenty of headroom)
- Monitor with `psutil` in production

#### Timeout Handling

**CRITICAL FINDING:** No explicit timeout parameter in `ClaudeAgentOptions`.

**Implication:** We MUST add `asyncio.wait_for()` wrapper in Phase 2:

```python
# Phase 2 implementation
result = await asyncio.wait_for(
    create_linkedin_post_workflow(...),
    timeout=120  # 2 minutes max per post
)
```

**Without this:** One stuck workflow blocks entire queue.

### 3. FastAPI Background Task Handling ✅ RESEARCHED

**Research completed:** 2025-10-24

#### Background Tasks Pattern

**Finding:** FastAPI provides `BackgroundTasks` for async operations after response is sent.

**Correct pattern:**
```python
from fastapi import BackgroundTasks

@app.post('/slack/events')
async def handle_slack_event(request: Request, background_tasks: BackgroundTasks):
    # 1. Validate request (< 3 seconds)
    data = await request.json()

    # 2. Send "On it..." immediately (< 3 seconds)
    slack_client.chat_postMessage(channel=channel, text="On it...", thread_ts=thread_ts)

    # 3. Queue bulk workflow as background task
    background_tasks.add_task(process_bulk_workflow, data, slack_client, channel, thread_ts)

    # 4. Return to Slack immediately (< 3 seconds)
    return {'status': 'ok'}

async def process_bulk_workflow(data, slack_client, channel, thread_ts):
    # This runs AFTER response is sent to Slack
    # Can take 45 minutes, no problem
    queue_manager = ContentQueueManager(slack_client=slack_client, ...)
    await queue_manager.bulk_create(...)
```

**CRITICAL:** Slack expects response within 3 seconds or it retries the event.

**Current issue:** `main_slack.py:175` processes synchronously, blocking response until agent completes (can take 2+ minutes for bulk requests).

#### Async vs Sync Background Tasks

**Finding:** Important distinction between `async def` and `def` for background tasks:

- **`async def task()`:** Runs in asyncio event loop (blocks loop during CPU work)
- **`def task()`:** Runs in separate thread pool (doesn't block event loop)

**Implication:** Our SDK agent workflows are async, so use `async def`.

**Thread pool size:** Default 40 threads (can cause memory issues if not limited).

**Recommendation:**
- Use `async def` for SDK agent workflows (already async)
- Monitor thread pool usage with large batches
- Consider reducing AnyIO thread limit if memory issues arise

#### Memory Leak Prevention

**CRITICAL FINDING:** FastAPI `run_in_threadpool` can cause memory leaks with default 40 threads.

**Symptoms:**
- High memory usage during background tasks
- Memory not released after task completion
- Server crashes with large batches

**Mitigation:**
```python
# Limit thread pool size
import anyio
anyio.to_thread.current_default_thread_limiter().total_tokens = 10

# Or: Use async background tasks (our approach)
background_tasks.add_task(async_process_workflow, ...)  # async def
```

**Our approach:** All SDK workflows are already async → no thread pool needed → no memory leak risk.

#### Alternative: Celery for Long-Running Tasks

**Finding:** For very long tasks (>10 minutes), Celery is recommended over FastAPI background tasks.

**Celery benefits:**
- Separate worker process (survives server restart)
- Task monitoring and retries
- Distributed processing

**Our decision:** Stick with FastAPI BackgroundTasks because:
- Month-of-content takes <45 minutes (acceptable)
- Simpler architecture (no Redis/RabbitMQ dependency)
- Progress updates via Slack are sufficient
- Replit deployment is single-server (no distribution needed)

**Future consideration:** If we need multi-hour batch jobs, migrate to Celery.
### 4. Replit Deployment Constraints ✅ RESEARCHED

**Research completed:** 2025-10-24

#### Reserved VM Specifications

**Finding:** Replit Reserved VM deployments offer scalable configurations:

**Available tiers:**
- Starting tier: $20/month
- Scalable up to: 16 vCPUs, 32 GiB RAM
- Core plan (dev): 4 vCPUs, 8 GiB RAM, 50 GiB storage

**Pricing:** Fixed hourly rate per tier (varies by CPU/RAM selection)

**Use case match:** Reserved VM is perfect for "long-running or compute-intensive applications" → bulk content generation fits this category.

#### Memory Budget for Bulk Generation

**Assumptions:**
- Base FastAPI app: ~500MB
- 3 concurrent SDK clients: ~300MB (100MB each)
- Queue manager overhead: ~100MB
- Buffer for spikes: ~1GB

**Total estimated peak:** ~2GB for 3 concurrent posts

**Replit Reserved VM capacity:** 8GB RAM (Core plan)

**Headroom:** 6GB available (plenty for month-of-content)

**Recommendation:**
- Start with $20/month Reserved VM (8GB RAM)
- Monitor memory with `psutil` in production
- Upgrade to higher tier if processing >10 concurrent posts

#### Deployment Considerations

**Finding:** Reserved VMs run exactly one copy of the application on a single VM.

**Implications:**
- No load balancing across multiple instances
- Single point of failure (acceptable for internal tool)
- All concurrent operations share same VM resources
- FastAPI background tasks run in same process

**Scaling strategy:**
- Vertical scaling: Upgrade to larger VM if needed
- No horizontal scaling (single VM by design)
- For enterprise: Consider multiple deployments or migrate to Kubernetes

#### Python Environment

**Finding:** Replit fully supports Python with pip package management.

**Dependencies to verify:**
- FastAPI + Uvicorn (async server)
- Slack SDK (with AsyncWebClient)
- Claude Agent SDK
- Anthropic API client
- Tavily (for fact-checking)
- All standard dependencies

**No compatibility issues expected.**

---

## Implementation Phases

### Phase 0: Branch Setup & Research ✅

**Tasks:**
- [x] Create `BULK-PLAN.md` (this document)
- [ ] Create `feature/bulk-content-generation` branch
- [ ] Research Slack SDK async patterns (document findings above)
- [ ] Research Agent SDK concurrent sessions (document findings above)
- [ ] Add research findings to this document

**Duration:** 1-2 hours
**Risk:** Zero (research only)

### Phase 1: Slack Progress Updates (CRITICAL)

**Goal:** Eliminate "On it..." silence - user sees real-time progress

**Files to modify:**
1. `agents/content_queue.py`
2. `slack_bot/claude_agent_handler.py`

**Changes:**

#### 1. Wire ContentQueueManager to Slack

```python
# agents/content_queue.py, line 54
def __init__(
    self,
    max_concurrent: int = 3,
    progress_callback: Optional[callable] = None,
    slack_client = None,  # NEW
    slack_channel: str = None,  # NEW
    slack_thread_ts: str = None  # NEW
):
    # ... existing code ...
    self.slack_client = slack_client
    self.slack_channel = slack_channel
    self.slack_thread_ts = slack_thread_ts
```

#### 2. Send Slack messages on progress events

```python
# agents/content_queue.py, line 168
async def _process_job(self, job: ContentJob):
    # Before processing
    if self.slack_client:
        self.slack_client.chat_postMessage(
            channel=self.slack_channel,
            thread_ts=self.slack_thread_ts,
            text=f"⏳ Creating post {self.stats['total_completed'] + 1}/{self.stats['total_queued']}...\n"
                 f"Topic: {job.topic[:100]}"
        )

    # ... process job ...

    # After success
    if self.slack_client and result:
        airtable_url = extract_airtable_url(result)
        self.slack_client.chat_postMessage(
            channel=self.slack_channel,
            thread_ts=self.slack_thread_ts,
            text=f"✅ Post {self.stats['total_completed']}/{self.stats['total_queued']} complete!\n"
                 f"📊 Airtable: {airtable_url}\n"
                 f"🎯 Quality Score: {extract_score(result)}/100"
        )
```

#### 3. Update `_delegate_bulk_workflow` to pass Slack client

```python
# slack_bot/claude_agent_handler.py, line 881
async def _delegate_bulk_workflow(platform, topics, context, count, style, slack_client, channel, thread_ts):
    queue_manager = ContentQueueManager(
        max_concurrent=3,
        slack_client=slack_client,  # NEW
        slack_channel=channel,
        slack_thread_ts=thread_ts
    )

    # ... rest of function ...
```

**Testing:**
- Create 3 LinkedIn posts
- Verify Slack receives 4 messages: "On it...", "Post 1/3", "Post 2/3", "Post 3/3"
- Verify each message has Airtable link

**Duration:** 2-3 hours
**Risk:** Low (adding logging, no logic changes)

### Phase 2: Per-Job Timeout (CRITICAL)

**Goal:** Prevent one stuck post from blocking entire queue

**Files to modify:**
1. `agents/content_queue.py`

**Changes:**

```python
# agents/content_queue.py, line 177
async def _process_job(self, job: ContentJob):
    try:
        # Wrap workflow in timeout
        result = await asyncio.wait_for(
            self._execute_workflow(job),
            timeout=120  # 2 minutes max per post
        )
    except asyncio.TimeoutError:
        # Handle timeout as failure
        await self._handle_job_failure(job, Exception("Timeout: Post took >2 minutes"))
        return
    except Exception as e:
        await self._handle_job_failure(job, e)
        return
```

**Testing:**
- Mock a workflow that takes 3 minutes
- Verify queue doesn't block
- Verify timeout error sent to Slack
- Verify retry logic kicks in

**Duration:** 1-2 hours
**Risk:** Low (standard asyncio pattern)

### Phase 3: CMO Agent Bulk Detection (CRITICAL)

**Goal:** Prevent "3 posts in one column" bug

**Files to modify:**
1. `slack_bot/claude_agent_handler.py` (system prompt)

**Changes:**

```markdown
# slack_bot/claude_agent_handler.py, line 650

**BULK REQUEST DETECTION:**

STEP 1: Parse user request for count indicators
- "3 posts" → count=3
- "5 tweets" → count=5
- "a week of content" → count=7
- "a month" → count=30

STEP 2: If count > 1, use bulk workflow
- Extract: count, platform(s), topics[], style, context
- Call delegate_bulk_workflow tool (you have access to this)
- Send acknowledgement: "On it! Creating [count] [platform] posts. I'll update you as each one completes."
- DO NOT create posts inline - you will accidentally merge them into one Airtable column

STEP 3: If count == 1, use normal workflow
- Call delegate_to_workflow as usual

CRITICAL RULE: NEVER concatenate multiple posts and save as one Airtable record.
Each post MUST be created separately via the workflow.
```

**Add new tool:**

```python
# slack_bot/claude_agent_handler.py

@tool(
    "delegate_bulk_workflow",
    "Queue multiple posts for batch generation. Use when user requests 2+ posts. Returns progress updates via Slack.",
    {
        "count": int,
        "platform": str,
        "topics": list,
        "style": str,
        "context": str
    }
)
async def delegate_bulk_workflow(args):
    # Implementation here
    pass
```

**Testing:**
- Request "create 3 LinkedIn posts"
- Verify CMO agent calls `delegate_bulk_workflow` (not `delegate_to_workflow` 3 times)
- Verify 3 separate Airtable rows created

**Duration:** 2-3 hours
**Risk:** Medium (changes agent prompt, need thorough testing)

### Phase 4: Contextual Post Count Tracking

**Goal:** Handle user revisions without creating duplicate posts

**Files to create:**
1. `agents/conversation_tracker.py` (NEW)

**Architecture:**

```python
class ConversationTracker:
    """Track post counts and revisions across conversation"""

    def __init__(self, thread_ts: str):
        self.thread_ts = thread_ts
        self.total_planned = 0
        self.posts_created = []  # [{topic, airtable_id, status}]
        self.posts_replaced = []  # [{old_id, new_id, reason}]

    def plan_posts(self, count: int, topics: list):
        """User requested N posts"""
        self.total_planned = count
        self.posts_created = [{"topic": t, "status": "planned"} for t in topics]

    def mark_complete(self, topic: str, airtable_id: str):
        """Post was created"""
        for post in self.posts_created:
            if post["topic"] == topic:
                post["airtable_id"] = airtable_id
                post["status"] = "completed"

    def replace_post(self, index: int, new_topic: str, reason: str):
        """User wants to revise post N"""
        old_post = self.posts_created[index]
        old_post["status"] = "replaced"
        self.posts_replaced.append({
            "old_id": old_post.get("airtable_id"),
            "old_topic": old_post["topic"],
            "new_topic": new_topic,
            "reason": reason
        })
        # Update planned post
        self.posts_created[index] = {"topic": new_topic, "status": "planned"}

    def get_summary(self):
        """Return conversation summary"""
        return {
            "total_planned": self.total_planned,
            "completed": len([p for p in self.posts_created if p["status"] == "completed"]),
            "pending": len([p for p in self.posts_created if p["status"] == "planned"]),
            "replaced": len(self.posts_replaced)
        }
```

**Integration:**

```python
# slack_bot/claude_agent_handler.py

# Store tracker in thread sessions
self._conversation_trackers = {}  # thread_ts -> ConversationTracker

# When user requests bulk:
tracker = ConversationTracker(thread_ts)
tracker.plan_posts(count=7, topics=["AI ethics", "Remote work", ...])
self._conversation_trackers[thread_ts] = tracker

# When user revises:
tracker.replace_post(index=2, new_topic="Time management", reason="User requested change")

# When agent creates post:
tracker.mark_complete(topic="AI ethics", airtable_id="rec123")
```

**Testing:**
- Request 7 posts
- Revise post 3
- Verify only 7 total Airtable records created (not 8)
- Verify old record marked "Replaced" in Airtable

**Duration:** 3-4 hours
**Risk:** Medium (new state management, potential for bugs)

### Phase 5: Month-of-Content Vortex (MAGNUM OPUS)

**Goal:** Full demo - 30 posts across 4 platforms with content calendar

**Files to create:**
1. `agents/content_planner.py` (NEW)
2. `agents/content_calendar.py` (NEW)

**Architecture:**

#### Step 1: Content Calendar Generation

```python
# agents/content_planner.py

class ContentPlanner:
    """Generate structured content plans for weeks/months"""

    def plan_month(
        self,
        themes: list,  # ["AI adoption", "Remote work", "Productivity"]
        platforms: list,  # ["linkedin", "twitter", "email"]
        post_types: list,  # ["thought_leadership", "tactical", "case_study"]
        start_date: str,  # "2025-01-01"
        days: int = 30
    ) -> ContentCalendar:
        """
        Generate 30-day content calendar with variety

        Returns: ContentCalendar with day-by-day schedule
        """
        calendar = ContentCalendar()

        # Week 1: Establish themes
        # Week 2: Deep dives
        # Week 3: Case studies
        # Week 4: Lead magnets

        # Rotate platforms: LinkedIn M/W/F, Twitter T/Th, Email weekly
        # Rotate themes: Equal distribution across days
        # Rotate formats: Mix motivational, tactical, case studies

        return calendar
```

#### Step 2: Batched Execution

```python
# agents/content_calendar.py

class ContentCalendar:
    """Execute content plan in batches with user checkpoints"""

    def __init__(self, plan: ContentPlan):
        self.plan = plan
        self.weeks = self._split_into_weeks(plan)

    async def execute_week(
        self,
        week_num: int,
        queue_manager: ContentQueueManager,
        slack_client,
        channel: str,
        thread_ts: str
    ):
        """Generate one week of content (5-7 posts)"""

        week_plan = self.weeks[week_num]

        # Queue all posts for the week
        for day_plan in week_plan:
            queue_manager.add_job(ContentJob(
                platform=day_plan.platform,
                topic=day_plan.topic,
                context=day_plan.context,
                style=day_plan.style
            ))

        # Wait for completion
        await queue_manager.wait_for_completion()

        # Send week summary
        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"✅ Week {week_num + 1} complete! {len(week_plan)} posts created.\n"
                 f"📅 Airtable filter: [link]\n\n"
                 f"Ready for Week {week_num + 2}?"
        )
```

#### Step 3: CMO Agent Integration

```python
# slack_bot/claude_agent_handler.py

@tool(
    "plan_month_of_content",
    "Generate a full month content calendar. Use for 'month of content' or '30 days' requests.",
    {
        "themes": list,
        "platforms": list,
        "start_date": str
    }
)
async def plan_month_of_content(args):
    planner = ContentPlanner()
    calendar = planner.plan_month(
        themes=args["themes"],
        platforms=args["platforms"],
        start_date=args["start_date"]
    )

    # Show plan to user for approval
    return {
        "content": [{
            "type": "text",
            "text": calendar.format_for_slack()
        }]
    }

@tool(
    "execute_content_calendar",
    "Execute approved content calendar week by week. Returns after each week for user review.",
    {
        "calendar_id": str,
        "week_num": int
    }
)
async def execute_content_calendar(args):
    # Execute one week, send updates, wait for approval
    pass
```

**Demo Flow:**

```
User: "Create a month of content for January"

Agent: Calls plan_month_of_content()
Agent: "Here's your January content calendar:
       Week 1: 7 posts (LinkedIn: 3, Twitter: 2, Email: 1, Carousel: 1)
       Week 2: 7 posts (...)
       Week 3: 7 posts (...)
       Week 4: 9 posts (includes lead magnets)

       Total: 30 posts across 4 platforms
       Themes: AI adoption, remote work, productivity

       Sound good? Say 'start week 1' to begin."

User: "Start week 1"

Agent: Calls execute_content_calendar(week_num=0)
Agent: [Progress updates as posts are created]
Agent: "✅ Week 1 complete! 7/7 posts created. Ready for week 2?"

User: "Yes, continue"

[Repeat for weeks 2-4]

Agent: "🎉 Month of content complete! 30 posts in Airtable, ready to schedule."
```

**Testing:**
- Request "month of content"
- Verify 30 posts created
- Verify variety (not all same format)
- Verify user can pause/review after each week
- Verify contextual revisions work mid-month

**Duration:** 1-2 days
**Risk:** High (complex state management, lots of moving parts)
**Reward:** **MASSIVE - this is the flagship demo**

### Phase 6: Error Recovery & Resilience

**Goal:** Graceful degradation, no data loss

**Enhancements:**

1. **Partial success handling:**
   - If 2/3 posts succeed, show user the 2 links + error for post 3
   - Don't block on failures

2. **Airtable quota handling:**
   - If Airtable quota exceeded, save to Supabase only
   - Notify user, continue with remaining posts

3. **Network retry logic:**
   - Exponential backoff on Anthropic API errors
   - Max 3 retries per post

4. **Progress persistence:**
   - Save queue state to Supabase every 30s
   - If server restarts mid-batch, resume from last checkpoint

5. **User cancellation:**
   - Add `/cancel` Slack command
   - Marks pending jobs as cancelled
   - Completes in-progress jobs gracefully

**Duration:** 1 day
**Risk:** Low (safety net for production)

---

## Month-of-Content Vortex Demo

### The Pitch

**What we're selling:** An AI agent that can generate a FULL MONTH of high-quality, multi-platform content in under an hour, with:
- ✅ Content calendar planning
- ✅ Platform variety (LinkedIn, Twitter, Email, Carousels)
- ✅ Format variety (thought leadership, tactical, case studies, lead magnets)
- ✅ Theme rotation (3 themes distributed evenly)
- ✅ Quality checks (Editor-in-Chief standards + GPTZero validation)
- ✅ Fact-checking (Tavily web search)
- ✅ Progress tracking (user sees every post as it's created)
- ✅ User revisions (can change angles mid-month without duplicates)

**Target audience:** Enterprise marketing teams, agencies, content creators

**Value prop:** "What takes your team 40 hours, our agent does in 45 minutes. And it's better quality."

### Demo Script

**Setup:** Clean Airtable base, fresh Slack thread

**Step 1: The Ask**
```
User: "I need a month of content for January to promote our new SaaS product. Mix LinkedIn thought leadership, Twitter threads, and weekly email newsletters. Focus on three themes: AI adoption challenges, remote work productivity, and time management."
```

**Step 2: Agent Plans**
```
Agent: "Perfect! Let me create a comprehensive content vortex for January.

🗓️ CONTENT CALENDAR PREVIEW:

Week 1 (Jan 1-7):
- Mon: LinkedIn - AI Adoption Myths (thought leadership)
- Tue: Twitter - Remote Work Setup Tips (thread)
- Wed: LinkedIn - Time Management Framework (tactical)
- Thu: Twitter - AI Tools Roundup (thread)
- Fri: LinkedIn - Customer Case Study (carousel)
- Sat: Email - Week 1 Roundup (newsletter)
- Sun: LinkedIn - Weekend Motivation (short post)

[Weeks 2-4 shown similarly]

📊 TOTALS:
- 30 posts across 4 platforms
- LinkedIn: 15 posts
- Twitter: 8 threads
- Email: 4 newsletters
- Carousels: 3 case studies

⏱️ Estimated time: 45 minutes
🎯 All posts quality-checked + fact-checked

Sound good? Say 'start' to begin, or 'revise' to adjust the plan."
```

**Step 3: User Approves**
```
User: "Looks great, start!"
```

**Step 4: Agent Executes Week 1**
```
Agent: "🚀 Starting Week 1 (7 posts)..."

[30 seconds]
Agent: "✅ Post 1/7 complete - AI Adoption Myths
📊 Airtable: [link]
🎯 Quality: 22/25
🤖 GPTZero: 18% AI (PASS)"

[60 seconds]
Agent: "✅ Post 2/7 complete - Remote Work Setup Tips
📊 Airtable: [link]
🎯 Quality: 21/25
🤖 GPTZero: 22% AI (PASS)"

[Continue for 7 posts]

Agent: "✅ Week 1 complete! 7/7 posts created in 3 minutes.
📅 View in Airtable: [filter link]

Ready for Week 2? Or want to review/revise Week 1 first?"
```

**Step 5: User Reviews & Revises**
```
User: "Week 1 looks good, but change Wednesday's post to focus on async communication instead of time management."

Agent: "Got it! Replacing post 3 (Wednesday) with async communication angle. Still 7 total posts for Week 1.

⏳ Creating revised post..."

[30 seconds]

Agent: "✅ Wednesday post updated!
📊 New Airtable record: [link]
🗑️ Old version archived (status: 'Replaced')

Week 1 finalized. Ready for Week 2?"
```

**Step 6: Continue Through Month**
```
User: "Yes, continue with weeks 2-4."

Agent: [Executes weeks 2-4 with progress updates]

Agent: "🎉 JANUARY CONTENT COMPLETE!

📊 FINAL STATS:
- Total Posts: 30
- LinkedIn: 15 posts (avg score 21/25)
- Twitter: 8 threads (avg score 20/25)
- Email: 4 newsletters (avg score 22/25)
- Carousels: 3 case studies (avg score 23/25)

✅ All posts passed AI detection
✅ All facts verified with Tavily
✅ Total time: 42 minutes

📅 Content Calendar: [Airtable link]
📈 Quality Report: [detailed breakdown]

Your January content is ready to schedule! 🚀"
```

**Step 7: Showcase**
- Open Airtable, show 30 posts in calendar view
- Open one LinkedIn post, show quality (clean, no AI tells)
- Check GPTZero on a few posts, show <30% AI scores
- Show variety: motivational vs tactical vs case study formats

**Result:** Audience is blown away. This is an enterprise-grade solution.

### Success Metrics for Demo

- ✅ 30 posts created in <45 minutes
- ✅ Zero "On it..." hangs (progress updates every 30-60s)
- ✅ All 30 posts in separate Airtable rows
- ✅ Average quality score ≥20/25
- ✅ All posts pass GPTZero (<30% AI)
- ✅ User can revise mid-month without duplicates
- ✅ Content variety (not all same format)
- ✅ Platform variety (LinkedIn, Twitter, Email, Carousels)
- ✅ Theme rotation (3 themes distributed evenly)

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_prompt_flows.py` (already created)

**Coverage:**
- ✅ Bulk request creates N separate Airtable rows (not 1 merged row)
- ✅ Agent completes response (no hanging on "On it...")
- ✅ Mixed platforms (2 LinkedIn, 2 Twitter, 1 Email)
- ✅ Empty/malformed requests handled gracefully
- ✅ Platform field mapping correct (linkedin → Linkedin)

**New tests to add:**
- Contextual post count tracking (7 planned, 1 revised → still 7 total)
- Timeout handling (mock post takes 3 minutes → retry triggered)
- Partial failure (post 2 fails, posts 1 & 3 succeed)
- Progress updates sent to Slack (mock Slack client)

### Integration Tests

**File:** `tests/test_bulk_generation.py` (NEW)

**Scenarios:**
1. **Simple bulk (3 posts):**
   - Create 3 LinkedIn posts
   - Verify 3 Airtable records
   - Verify 4 Slack messages (On it + 3 completions)
   - Verify Airtable links in messages

2. **Mixed platforms:**
   - Create 2 LinkedIn, 2 Twitter, 1 Email
   - Verify correct platform field for each
   - Verify all 5 in Airtable

3. **Timeout scenario:**
   - Mock SDK agent to hang on post 2
   - Verify timeout after 2 minutes
   - Verify retry triggered
   - Verify other posts continue

4. **Week of content:**
   - Plan 7 posts (Mon-Sun)
   - Execute batch
   - Verify 7 Airtable records with dates

5. **Month of content:**
   - Plan 30 posts across 4 platforms
   - Execute in 4 weekly batches
   - Verify 30 Airtable records
   - Verify variety (platforms, formats, themes)

### Manual Testing Checklist

Before merging branch to main:

- [ ] Single post still works (no regression)
- [ ] DM: "Create 3 LinkedIn posts" → 3 separate Airtable rows
- [ ] Channel: "Create 5 Twitter threads" → progress updates every 30-60s
- [ ] Mixed: "Create 2 LinkedIn, 2 Twitter, 1 Email" → all 5 created correctly
- [ ] Revision: Request 7 posts, change post 3 → only 7 total in Airtable
- [ ] Week of content: Request 7 posts (Mon-Sun) → calendar format in Airtable
- [ ] Month of content: Request 30 posts → batched weekly with checkpoints
- [ ] Timeout: Kill network mid-post → graceful failure, retry triggered
- [ ] Airtable quota: Fill Airtable to quota → saves to Supabase only
- [ ] Cancellation: Request 10 posts, cancel after 3 → only 3 created

---

## Risk Mitigation

### Risk 1: Regression - Single Posts Break

**Mitigation:**
- Run all existing tests before each phase
- Keep single-post code path unchanged
- Only add bulk-specific code paths

**Rollback plan:**
- Revert to main branch
- Bulk requests temporarily disabled

### Risk 2: Slack Rate Limits

**Current:** Bot messages count toward rate limit (1 msg/second)

**Mitigation:**
- Batch progress updates (send every 3 posts, not every post)
- For month of content: Send weekly summaries, not per-post updates

**Monitoring:**
- Log all Slack API calls
- Track rate limit errors

### Risk 3: Memory Leak from 30 Concurrent SDK Clients

**Current:** Each SDK client uses ~50MB RAM

**Mitigation:**
- Limit to 3 concurrent clients (max 150MB)
- For month of content: Process in batches of 5
- Monitor memory usage in production

**Fallback:**
- Reduce concurrent limit to 1
- Slower but safer

### Risk 4: ContentQueueManager Hangs on One Failed Post

**Mitigation:**
- Phase 2 adds per-job timeout (120s)
- Failed post retries 2x, then marks as failed
- Queue continues with remaining posts

**Testing:**
- Mock a post that hangs forever
- Verify queue doesn't block

### Risk 5: User Revises Mid-Generation, Creates Duplicates

**Mitigation:**
- Phase 4 adds ConversationTracker
- Tracks total planned count
- Replace not add when user revises

**Testing:**
- Request 7 posts, revise post 3 mid-generation
- Verify only 7 total in Airtable

### Risk 6: Month-of-Content Fails at Week 3

**Mitigation:**
- Checkpoint after each week
- Save progress to Supabase
- Resume from last checkpoint

**User experience:**
- "Week 3 failed, but weeks 1-2 are in Airtable. Retry week 3?"

---

## Success Metrics

### Phase 1 Success (Slack Progress Updates)
- ✅ Zero "On it..." hangs (user always sees updates)
- ✅ Progress update every 30-60s during bulk generation
- ✅ Airtable link in each completion message
- ✅ Final summary with stats (completed/failed, avg time)

### Phase 2 Success (Timeout Handling)
- ✅ No queue blocks (even if one post hangs)
- ✅ Timeout errors logged + sent to Slack
- ✅ Retry logic works (timeout → retry → fail gracefully)

### Phase 3 Success (Bulk Detection)
- ✅ "Create 3 posts" → CMO agent calls delegate_bulk_workflow
- ✅ Never merges posts into one Airtable column
- ✅ Each post in separate Airtable row

### Phase 4 Success (Contextual Tracking)
- ✅ User revises post mid-generation → doesn't create duplicate
- ✅ Agent confirms: "Still 7 total posts"
- ✅ Old post marked "Replaced" in Airtable

### Phase 5 Success (Month-of-Content Vortex)
- ✅ 30 posts created in <45 minutes
- ✅ Content variety (platforms, formats, themes)
- ✅ User can review/revise after each week
- ✅ Final demo impresses enterprise clients

### Overall Success Criteria

Before merging branch to main:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing checklist complete
- [ ] Zero regressions in single-post workflows
- [ ] Documentation updated (README, API docs)
- [ ] Demo video recorded (month-of-content vortex)

---

## Next Steps

1. **Complete Phase 0 research:**
   - Slack SDK async patterns
   - Agent SDK concurrent sessions
   - FastAPI background tasks
   - Document findings in this file

2. **Create feature branch:**
   - `git checkout -b feature/bulk-content-generation`
   - Copy all relevant files
   - Add initial tests

3. **Implement Phase 1:**
   - Wire ContentQueueManager to Slack
   - Send progress updates
   - Test with 3 posts

4. **Review & iterate:**
   - Test thoroughly
   - Fix bugs
   - Update this plan based on learnings

5. **Continue through phases 2-6:**
   - One phase at a time
   - Test after each phase
   - Update plan as needed

6. **Prepare demo:**
   - Record month-of-content demo video
   - Create pitch deck
   - Show to potential clients

---

## Key Research Findings & Plan Adjustments

### ✅ Research Complete (2025-10-24)

All 4 research areas investigated. Key findings that affect implementation:

#### 1. FastAPI Background Tasks (CRITICAL ADJUSTMENT)

**Finding:** Current `/slack/events` endpoint processes synchronously, blocking Slack response.

**Required change:** Add `BackgroundTasks` parameter to immediately return "On it..." within 3 seconds:

```python
# Phase 1 must include this FastAPI change
@app.post('/slack/events')
async def handle_slack_event(request: Request, background_tasks: BackgroundTasks):
    # Send "On it..." immediately
    slack_client.chat_postMessage(...)
    # Queue bulk workflow as background task
    background_tasks.add_task(process_bulk_workflow, ...)
    return {'status': 'ok'}  # Returns in < 3 seconds
```

**Without this:** Slack retries event after 3 seconds → duplicate processing.

#### 2. Slack Rate Limits (NO CHANGES NEEDED)

**Finding:** `chat.postMessage` allows 1 msg/second per channel, bursts OK.

**Our usage:** 30 progress updates over 45 minutes = 0.67 msg/min (well within limits).

**Conclusion:** No rate limit handling needed.

#### 3. Bot Messages in Context (NEW FILTER REQUIRED)

**Finding:** CMO agent sees ALL thread messages including progress updates.

**Impact:** With 30 posts, CMO agent context includes 30x "✅ Post X/30 complete" messages (noise).

**Required change:** Filter bot messages when fetching thread history for CMO agent:

```python
# Add to Phase 1 or 3
thread_messages = client.conversations_replies(channel=channel, ts=thread_ts)
user_messages = [
    msg for msg in thread_messages['messages']
    if not msg.get('bot_id') and msg.get('subtype') != 'bot_message'
]
```

**Benefit:** Keeps CMO agent context clean, reduces token usage.

#### 4. Agent SDK Memory (NO CHANGES NEEDED)

**Finding:** Each post is independent session (`continue_conversation=False`).

**Memory per SDK client:** ~50-100MB (estimated)

**3 concurrent clients:** ~300MB

**Replit Reserved VM:** 8GB RAM

**Conclusion:** Plenty of headroom, no memory constraints.

#### 5. Timeout Handling (PHASE 2 CONFIRMED)

**Finding:** No explicit timeout in `ClaudeAgentOptions`.

**Confirmed requirement:** Phase 2 must add `asyncio.wait_for(workflow(), timeout=120)`.

**Without this:** One stuck post blocks entire queue for hours.

#### 6. Replit Deployment (NO CONCERNS)

**Finding:** $20/month Reserved VM provides 8GB RAM, 4 vCPUs.

**Our peak usage:** ~2GB RAM for 3 concurrent posts.

**Conclusion:** Current Replit tier is sufficient for month-of-content.

### Updated Implementation Order

**Phase 0.5 (NEW):** FastAPI Background Tasks Integration
- **Before Phase 1:** Update `/slack/events` to use `BackgroundTasks`
- **Duration:** 1 hour
- **Risk:** Low (standard FastAPI pattern)
- **Why critical:** Without this, Slack retries events → duplicate posts

**Phase 1:** Slack Progress Updates (unchanged)
- Wire ContentQueueManager to Slack
- Add bot message filtering for CMO agent context

**Phases 2-6:** Proceed as planned

---

## Resolved Questions

### 1. Slack SDK

- ❓ Can we edit a message to show progress?
  - ✅ **Answer:** Yes, but multiple messages are clearer UX (easier to implement)

- ❓ Do progress updates interfere with CMO agent context?
  - ✅ **Answer:** Yes, must filter `bot_id` messages when building context

### 2. Agent SDK

- ❓ What's the max recommended concurrent SDK clients?
  - ✅ **Answer:** No official limit, 3 concurrent is safe (300MB peak memory)

- ❓ Does session memory accumulate over long conversations?
  - ✅ **Answer:** Each post is independent session, no accumulation

### 3. ContentQueueManager

- ❓ Should we persist queue state to Supabase?
  - ✅ **Answer:** Phase 6 enhancement, not critical for MVP

- ❓ What's the right batch size for month-of-content?
  - ✅ **Answer:** 5-7 posts per week (natural checkpoint)

### 4. Airtable

- ❓ Should we use Airtable API batching?
  - ✅ **Answer:** No, each post creates 1 record (simpler, no batching needed)

- ❓ What's the rate limit?
  - ✅ **Answer:** 5 req/sec (we create ~1 post/min, well within limit)

### 5. User Experience

- ❓ Should progress updates be in main message or thread?
  - ✅ **Answer:** Thread (keeps channel clean)

- ❓ Should we send notifications for EVERY post or batch by 3?
  - ✅ **Answer:** Every post (users want real-time visibility)

---

## Resources

- Slack SDK docs: https://slack.dev/python-slack-sdk/
- Slack AsyncWebClient: https://slack.dev/python-slack-sdk/web/index.html
- Agent SDK docs: https://docs.claude.com/en/api/agent-sdk/python
- FastAPI background tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Anthropic rate limits: https://docs.anthropic.com/en/api/rate-limits
- Replit Reserved VM: https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments
- Slack rate limits (2025): https://api.slack.com/apis/rate-limits

---

**Last updated:** 2025-10-24 (Research complete)
**Status:** Ready for Phase 0.5 (FastAPI background tasks)
**Next milestone:** Implement Phase 0.5, then Phase 1

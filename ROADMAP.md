# Slack Content Agent Roadmap

## ✅ Phase 1: Core Infrastructure (DONE)
- [x] Clean Slack-only codebase (main_slack.py)
- [x] Database schema (Supabase with vector search)
- [x] Slack event handlers (mentions, DMs, reactions)
- [x] 3-agent workflow system (Writer → Validator → Reviser)
- [x] Deploy to Replit

## ✅ Phase 2: Agent Orchestration (COMPLETE - 2025-10-09)
- [x] **Claude Agent SDK Implementation** (`claude-agent-sdk` v0.1.1)
  - [x] Proper `@tool` decorator pattern
  - [x] 6 working tools with web_search as PRIMARY
  - [x] Clean handler architecture (`slack_bot/claude_agent_handler.py`)
  - [x] Session management per thread
  - [x] Automatic tool orchestration (no manual loops)
- [x] Tool calling system with ~~Anthropic~~ Claude Agent SDK
- [x] RAG search integration (search_knowledge_base tool)
- [x] Web search (Tavily via web_search tool)
- [x] Workflow execution via tools
- [x] Brand voice management
- [x] Calendar scheduling (Airtable)
- [x] ~~Voice notes → content (Whisper API)~~ (removed due to issues)
- [x] Fully agentic LinkedIn workflow with autonomous research
- [x] Context-aware conversation (resolves "both", "this", "that")
- [x] Slack mrkdwn formatting for responses
- [x] Twitter workflow (5 format types)
- [x] Email workflow (3 types: Value, Indirect, Direct)

## 🚀 Phase 2.5: Platform Quality System (BREAKTHROUGH - 2025-10-10)

**WE CRACKED THE CODE: 88% Human Score on LinkedIn**

See [PLATFORM_REPLICATION_BLUEPRINT.md](PLATFORM_REPLICATION_BLUEPRINT.md) for complete system.

### ✅ LinkedIn SDK Agent (PROVEN - 88% Human)
- [x] **Quality Gate Framework** (Ethan Evans' rubric approach)
  - [x] 5-axis scoring rubric (Hook, Audience, Headers, Proof, CTA)
  - [x] 0-5 scoring per axis with concrete examples
  - [x] Minimum threshold: 18/25 (72%)
  - [x] Decision logic: accept (≥20) | revise (18-19) | reject (<18)

- [x] **Example-Driven Prompting**
  - [x] 5 complete 100% human posts from Cole/Dickie/Daniel
  - [x] Full text embedded in prompts (not summaries)
  - [x] Leverages Anthropic prompt caching (~90% token savings)

- [x] **Human Voice Patterns**
  - [x] Heavy contractions: "I'm", "I've", "here're", "'Cause"
  - [x] Informal starters: "So", "And", "But"
  - [x] Hedging language: "pretty well", "definitely", "a bunch of"
  - [x] Conversational fragments & ellipses
  - [x] AI tell detection: contrast framing, Rule of Three, cringe questions

- [x] **JSON Structured Feedback**
  - [x] create_human_draft → {post_text, self_assessment: {total: 23}}
  - [x] quality_check → {scores, decision, issues, surgical_summary}
  - [x] apply_fixes → {revised_post, changes_made, estimated_new_score}
  - [x] Programmatic decisions based on scores

- [x] **5-Tool Architecture**
  - [x] generate_5_hooks
  - [x] create_human_draft (with self-assessment)
  - [x] inject_proof_points
  - [x] quality_check (with web_search for fact-checking)
  - [x] apply_fixes (surgical, not rewrites)

**Results:**
- GPTZero: 88% human (target: 80-90%)
- Quality scores: 22-24/25 on draft, 18-21/25 on check
- Acceptance rate: ~80% first draft, ~95% after fixes

**Critical Learning:**
Rich input required. Vague prompt → 99% AI. Rich context (opinions, specifics, names) → 88% human.

### 📋 Platform Expansion (Using Replication Blueprint)

**Template ready to clone for:**

- [ ] **Twitter/X Threads**
  - [ ] Research: Find 5 threads scoring 90-100% human
  - [ ] Design: 5 quality axes (Hook, Thread Flow, Brevity, Proof, Engagement)
  - [ ] Extract: Human patterns (lowercase, no punctuation, abbreviations)
  - [ ] Build: Prompts with complete examples
  - [ ] Test: Target 80-90% human detection

- [ ] **Blog/Long-Form**
  - [ ] Research: Find 5 blog posts scoring 90-100% human
  - [ ] Design: 5 quality axes (Title, Intro, Structure, Depth, CTA)
  - [ ] Extract: Human patterns (subheaders as questions, paragraph variance)
  - [ ] Build: Prompts with complete examples
  - [ ] Test: Target 80-90% human detection

- [ ] **Email Newsletters**
  - [ ] Research: Find 5 newsletters scoring 90-100% human
  - [ ] Design: 5 quality axes (Subject, Open, Value, Cadence, CTA)
  - [ ] Extract: Human patterns (email-specific voice)
  - [ ] Build: Prompts with complete examples
  - [ ] Test: Target 80-90% human detection

- [ ] **YouTube Scripts**
  - [ ] Research: Find 5 scripts scoring 90-100% human
  - [ ] Design: 5 quality axes (Hook, Spoken Flow, Pacing, Value, Outro)
  - [ ] Extract: Human patterns (spoken vs written differences)
  - [ ] Build: Prompts with complete examples
  - [ ] Test: Target 80-90% human detection

**Each platform uses same 5-tool architecture with platform-specific:**
1. Quality axes (what makes content great on that platform)
2. Example posts (5 complete 100% human examples)
3. Human voice patterns (platform-specific authenticity markers)
4. JSON feedback schemas (same structure, different rubrics)

### 🎯 Platform Quality Metrics (Track Per Platform)

**Success Criteria for Each Platform:**
- AI Detection: 80-90% human (GPTZero or Originality.ai)
- Quality Score: 20-24/25 on create_draft
- Acceptance Rate: 80%+ first draft, 95%+ after fixes
- User Satisfaction: Rich context provided → quality output

**Quarterly Maintenance:**
- Refresh example posts if AI detection scores drop
- Update human voice patterns if platform evolves
- Monitor algorithm changes (LinkedIn, Twitter, etc.)

### Old Content Workflows (To Be Upgraded)
- [ ] Substack flow → Upgrade with quality system
- [ ] Youtube script flow → Build with replication blueprint
- [ ] Lead Magnet LI/X flows → Apply quality gates
- [ ] Documents for Training → Extract as examples

## 📋 Phase 3: Enhanced Features (NEXT)

### 🎭 Agent Progress Feedback (Priority - UX)
- [ ] **Real-time Progress Updates During SDK Agent Execution**
  - **Problem:** User sends "create a LinkedIn post" → sees nothing for 30-60 seconds → feels frozen
  - **Solution:** Pass `slack_client` + `thread_ts` into SDK agent workflows
  - **Implementation:**
    - Update `create_linkedin_post_workflow()` signature to accept `slack_client`, `channel`, `thread_ts`
    - Add Slack reactions at each tool checkpoint:
      - 👀 "On it!" - Agent starts, connecting to SDK
      - 🎨 "Generating 5 hooks..." - After `generate_5_hooks` call
      - ✍️ "Writing draft..." - After `create_human_draft` call
      - 📊 "Adding proof points..." - After `inject_proof_points` call
      - 🔍 "Quality checking..." - After `quality_check` call
      - ✨ "Polishing..." - After `apply_fixes` call
      - ✅ "Done!" - Final post ready
    - Use `client.reactions_add(channel=channel, timestamp=thread_ts, name="eyes")` pattern
  - **Apply to all 4 SDK agents:** LinkedIn, Twitter, Email, YouTube
  - **Benefits:**
    - User knows agent is working
    - Shows progress through 5-tool workflow
    - Reduces perceived wait time
    - Professional UX vs "is it frozen?"

  **Technical Details:**
  - Modify `_delegate_workflow_func()` in `claude_agent_handler.py` to capture Slack context
  - Pass through to each SDK agent's workflow function
  - Each agent adds reactions at tool boundaries
  - Reactions persist in thread, showing full workflow history
  - Error handling: If Slack API fails, agent continues (reactions are UX, not critical)

### 🎭 Slack Emoji Reactions (User Actions)
- [ ] **📅 Add to Calendar** (also creates Google Doc)
  - User reacts with 📅 to approved content
  - Creates entry in Airtable `content_calendar` table
  - Auto-generates Google Doc for fine-tuning
  - Links doc back to calendar entry
  - Includes metadata: platform, publish_date, status

- [ ] **🔍 Research**
  - User reacts with 🔍 to content
  - Triggers deep research using `web_search` tool
  - Finds 3-5 supporting stats/case studies
  - Adds findings to `research` table with sources
  - Updates content draft with proof points
  - Returns updated version with citations

- [ ] **📊 Find Similar**
  - User reacts with 📊 to content
  - RAG search across `content_examples` for similar topics
  - Shows top 3 matches with engagement metrics
  - Suggests structure improvements based on winners
  - Provides insights: "Your hook is weaker than top performers. Try leading with a stat."

### 📚 Template Library System
- [ ] **Template Search Infrastructure**
  - Semantic search across JSON templates in `templates/` directory
  - Embed `description` + `use_when` fields for similarity matching
  - Prime Agent tool: `search_templates(user_intent) → top 3 matches`
  - User picks template → structure passed to platform sub-agent

- [ ] **Initial Template Set**
  - [x] Email: VALUE email (educational with soft CTA)
  - [x] LinkedIn: Framework post (numbered steps with proof)
  - [x] Twitter: Hot take (provocative single tweet)
  - [ ] Email: STORY email (narrative arc with lesson)
  - [ ] LinkedIn: Personal story (vulnerability + insight)
  - [ ] Twitter: Thread template (hook → context → proof → CTA)

### 🔌 Google Workspace Integration
- [ ] **Google Docs API**
  - Create doc from approved content
  - Sync doc changes back to Airtable
  - RAG indexing of doc content

- [ ] Batch content creation
- [ ] Performance analytics
- [ ] User-specific brand voice learning
- [ ] Conversation memory per thread

## 🎯 Phase 4: Advanced (FUTURE)
- [ ] Multi-workspace support
- [ ] Team collaboration features
- [ ] A/B testing suggestions
- [ ] Content repurposing (LinkedIn → Twitter thread)
- [ ] Scheduled content reminders
- [ ] Integration with publishing tools (Buffer, Hootsuite)

## 🛠️ Critical Implementation Rules

### **MUST FOLLOW - NO EXCEPTIONS:**

1. **ALWAYS use Claude Agent SDK** for the primary Slack agent
   - Never revert to manual Anthropic API loops
   - Use `@tool` decorator pattern
   - Handler must be separate from main.py

2. **Web Search is PRIMARY**
   - First tool in the list
   - System prompt must aggressively direct to use it
   - NEVER tell users to "check websites" - agent searches for them

3. **Architecture Pattern**
   ```
   main_slack.py → claude_agent_handler.py → tools
   ```
   - Clean separation of concerns
   - Handler manages agent state
   - Tools are properly decorated functions

4. **Database Schema**
   - `conversation_history` table must have correct schema:
     - thread_ts, channel_id, user_id, role, content
   - NOT the old schema with message_text/agent_response

5. **Testing Before Deployment**
   - Always test Claude Agent SDK imports work
   - Verify all 6 tools are registered
   - Check web_search responds to current events questions

## 🔮 Blue Sky Ideas

- [ ] **Real-time streaming for agentic workflows**
  - Stream draft creation in real-time using Anthropic streaming API
  - Live progress updates: "🎤 Generating hooks (1/5)...", "🔍 Researching proof points..."
  - Update Slack messages incrementally as agent works
  - Show hook generation, draft writing, and editing iterations live
  - Makes 20-30 second wait feel interactive and engaging
- [ ] Image generation (DALL-E for social posts)
- [ ] Video script generation
- [ ] SEO optimization tools
- [ ] Competitor content analysis

---

# 🚀 PRODUCTION DEPLOYMENT PLAN

## ✅ Phase 3: SDK Agent Completion (2025-10-11)

### **Platform Status:**
| Platform | SDK Agent | Prompts | Examples | Handler Integration | Status |
|----------|-----------|---------|----------|---------------------|--------|
| **LinkedIn** | ✅ | ✅ | Unknown | ✅ claude_agent_handler | 🟢 READY |
| **Twitter** | ✅ | ✅ | 229 (73 threads) | ✅ claude_agent_handler | 🟢 **INTEGRATED** |
| **Email** | ✅ | ✅ | 190 (4 types) | ✅ claude_agent_handler | 🟢 READY (20/25) |
| **YouTube** | ✅ | ✅ | 26 scripts | ✅ claude_agent_handler | 🟢 READY (22/25) |

**Update 2025-10-11:** Twitter SDK Agent now integrated into `claude_agent_handler.py` (line 202-206). All 4 platforms use modern SDK architecture.

---

## 📦 Architecture: Modern vs Legacy

### **Two Parallel Systems (Coexist for Now):**

#### **System 1: MODERN (Primary)**
```
Slack @mention
    ↓
main_slack.py (line 352)
    ↓
slack_bot/claude_agent_handler.py
    ↓
ClaudeAgentHandler.handle_conversation()
    ↓
delegate_to_workflow tool
    ↓
    ├── LinkedIn → linkedin_sdk_agent ✅
    ├── Twitter → twitter_sdk_agent ✅ (NEWLY INTEGRATED)
    ├── Email → email_sdk_agent ✅
    └── YouTube → youtube_sdk_agent ✅
```

**Status:** Primary system, all 4 platforms use SDK agents

#### **System 2: LEGACY (Transition)**
```
Slack /command
    ↓
main_slack.py
    ↓
slack_bot/handler.py
    ↓
WORKFLOW_REGISTRY[platform]
    ↓
workflows/agentic_*_workflow.py
    ↓
    ├── agentic_linkedin_workflow → linkedin_sdk_agent
    ├── agentic_twitter_workflow → twitter_orchestrator
    └── agentic_email_workflow → email_orchestrator
```

**Status:** Still active, used by old slash commands. Kept for backward compatibility.

---

## 📋 Production File Checklist

### **✅ CORE - Must Include (61 files)**

#### **Entry Point & Slack Bot:**
```
main_slack.py
slack_bot/
├── claude_agent_handler.py         # Modern: Uses SDK agents directly
├── handler.py                       # Legacy: Uses WORKFLOW_REGISTRY
├── memory.py
├── reactions.py
├── formatters.py
├── plan_mode_handler.py
└── agent_tools.py
```

#### **SDK Agents (4 platforms):**
```
agents/
├── linkedin_sdk_agent.py
├── twitter_sdk_agent.py
├── email_sdk_agent.py
└── youtube_sdk_agent.py
```

#### **SDK Agent Prompts:**
```
prompts/
├── linkedin_tools.py
├── twitter_tools.py
├── email_tools.py
└── youtube_tools.py
```

#### **Tools:**
```
tools/
├── search_tools.py
├── template_search.py
└── pattern_matching.py             # Email + YouTube pattern extraction
```

#### **Legacy (Still Used by handler.py):**
```
workflows/
├── __init__.py                     # WORKFLOW_REGISTRY
├── base_workflow.py
├── agentic_linkedin_workflow.py
├── agentic_twitter_workflow.py
└── agentic_email_workflow.py

agents/
├── agentic_twitter_orchestrator.py
├── agentic_email_orchestrator.py
├── agentic_linkedin_orchestrator.py
├── agentic_twitter_format_generator.py
└── content_queue.py                # Bulk operations
```

#### **Supporting:**
```
integrations/airtable_client.py
validators/
├── linkedin_validator.py
└── pattern_library.py
templates/[linkedin, twitter, email folders]
frameworks/write-like-a-human.md
utils/health_check.py
```

#### **Database Setup:**
```
setup/
├── database_schema_v2.sql
├── create_rpc_functions.sql
├── load_email_newsletters.py
└── verify_and_embed_emails.py
```

#### **Replit:**
```
.replit
replit.nix
Procfile
pyproject.toml
requirements.txt
.env.example
README.md
ARCHITECTURE.md
```

---

### **❌ DELETE - Not Used (30 files)**

```
# Duplicate Tools (Use prompts/ instead)
agents/
├── email_tools.py
├── linkedin_tools.py
└── twitter_tools.py

# Old Helpers (SDK agents handle internally)
agents/
├── agentic_hook_generator.py
├── agentic_proof_injector.py
├── hook_generator.py
├── proof_injector.py
└── hybrid_editor.py

# Old Workflows (Not in WORKFLOW_REGISTRY)
workflows/
├── linkedin_workflow.py
├── twitter_workflow.py
└── email_workflow.py

# Dev/Test
test_*.py
test_tools/ (keep for validation, exclude from runtime)
demo_*.py
*.log
```

---

## 🔧 Pre-Deployment Fixes (Required)

### **1. Slack Signature Verification ⚠️ CRITICAL**

**File:** `main_slack.py` line 197

**Current:** Reads headers but doesn't verify
```python
slack_signature = request.headers.get('X-Slack-Signature', '')
slack_timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
```

**Add After Line 197:**
```python
import hmac
import hashlib
from time import time

# Verify Slack signature
if not slack_signature or not slack_timestamp:
    return {"challenge": "missing_signature"}

# Prevent replay attacks (reject if >5 min old)
if abs(time() - int(slack_timestamp)) > 300:
    return {"challenge": "timestamp_too_old"}

# Reconstruct base string: v0:{timestamp}:{raw_body}
raw_body = await request.body()
base_string = f"v0:{slack_timestamp}:{raw_body.decode('utf-8')}"

# Compute HMAC-SHA256
signing_secret = os.getenv('SLACK_SIGNING_SECRET')
our_signature = 'v0=' + hmac.new(
    signing_secret.encode(),
    base_string.encode(),
    hashlib.sha256
).hexdigest()

# Timing-safe comparison
if not hmac.compare_digest(our_signature, slack_signature):
    return {"challenge": "invalid_signature"}
```

---

### **2. Fix Batch Handler Mismatch**

**File:** `main_slack.py` line 497

**Current (BROKEN):**
```python
result = await handler.handle_batch_creation(...)  # ❌ Method doesn't exist
```

**Fix:**
```python
result = await handler.handle_batch_request(
    ...
    send_message_fn=send_slack_message  # Add missing parameter
)
```

---

### **3. Twitter SDK Agent ✅ DONE**

**File:** `slack_bot/claude_agent_handler.py` line 202-206

**Status:** ✅ Completed 2025-10-11 - Now uses `twitter_sdk_agent` instead of orchestrator

---

## 🔐 Replit Deployment: Client Setup

### **What Clients Do:**
1. Fork Replit project
2. Create new Supabase project
3. Run 3 SQL scripts
4. Add 5-8 secrets in Replit UI
5. Hit "Run" → Bot live

### **Required Secrets:**
```env
# Core (Required)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxxx...
ANTHROPIC_API_KEY=sk-ant-xxx
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx            # ⚠️ CRITICAL for signature verification

# Embeddings (Required for Email/YouTube)
OPENAI_API_KEY=sk-xxx

# Optional (Feature Flags)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx       # Observability
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
AIRTABLE_API_KEY=patxxx             # Calendar sync
AIRTABLE_BASE_ID=appxxx
TAVILY_API_KEY=tvly-xxx             # Web search
```

---

### **Database Setup (3 Scripts):**
```bash
# 1. Create tables
psql $DATABASE_URL < setup/database_schema_v2.sql

# 2. Create RPC functions
psql $DATABASE_URL < setup/create_rpc_functions.sql

# 3. Load email examples (for Email SDK Agent)
python3 setup/load_email_newsletters.py
```

---

### **Slack App Config:**
```
Event Subscriptions:
  URL: https://your-repl-url.replit.dev/slack/events
  Events: app_mention, message.channels

Slash Commands:
  /content → /slack/commands/content
  /batch → /slack/commands/batch
  /calendar → /slack/commands/calendar
  /plan → /slack/commands/plan
  /stats → /slack/commands/stats

OAuth Scopes:
  chat:write
  app_mentions:read
  channels:history
  reactions:write
```

---

## ✅ Pre-Launch Testing Checklist

### **Platform Tests:**
```bash
# In Slack, test each platform:
@Bot create a LinkedIn post about AI tools
@Bot create a Twitter thread about content strategy
@Bot create an email newsletter about growth hacking
@Bot create a YouTube script about finding your voice
```

### **Batch Test:**
```bash
/batch platform:linkedin topic:AI productivity count:3
```

### **Memory Test:**
```bash
@Bot create a LinkedIn post about AI
# Then in same thread:
@Bot make it more casual
```

### **Health Check:**
```bash
curl https://your-repl-url.replit.dev/healthz
```

---

## 📊 Success Metrics

### **Quality Scores (Per Platform):**
- LinkedIn: Target 20-24/25
- Twitter: Target TBD (not yet tested)
- Email: Target 20/25 ✅ (achieved)
- YouTube: Target 22/25 ✅ (achieved)

### **AI Detection:**
- Target: 80-90% human (GPTZero)
- LinkedIn: Proven at 88%
- Email/YouTube: Not yet tested

### **User Satisfaction:**
- First draft acceptance: 80%+
- After fixes: 95%+
- Response time: <60 seconds

---

## 🎯 Next Steps (Post-Deployment)

1. ✅ Monitor quality scores per platform
2. ✅ Test Twitter SDK Agent in production
3. ✅ Migrate `handler.py` to use SDK agents (remove WORKFLOW_REGISTRY)
4. ✅ Delete duplicate files after migration verified
5. ✅ Document migration guide for future platforms
6. ✅ Add real-time streaming for better UX

---

**Last Updated:** 2025-10-11
**Status:** Ready for Replit deployment after 2 critical fixes (signature verification + batch handler)

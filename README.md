# AI Content Agent Template

A production-ready AI content creation system powered by Anthropic Claude Agent SDK. Creates high-quality, human-like content for LinkedIn, Twitter/X, and Email through Slack integration with intelligent workflows, validators, and quality controls.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
npm install

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Bootstrap database (creates tables and RAG functions)
node scripts/bootstrap_database.js

# 4. Start the Slack bot
npm start
# Or manually: python3 -m uvicorn main_slack:app --host 0.0.0.0 --port 5000
```

## 📁 Project Structure

```
ai-content-agent-template/
├── main_slack.py               # FastAPI app with Slack event handlers
├── package.json                # NPM scripts and dependencies
├── requirements.txt            # Python dependencies
│
├── agents/                     # Claude Agent SDK implementations
│   ├── email_sdk_agent.py      # Email content generation
│   ├── linkedin_sdk_agent.py   # LinkedIn content generation
│   ├── twitter_sdk_agent.py    # Twitter/X content generation
│   └── youtube_sdk_agent.py    # YouTube script generation
│
├── workflows/                  # Content creation workflows
│   ├── base_workflow.py        # Core workflow orchestration
│   ├── agentic_linkedin_workflow.py
│   ├── agentic_twitter_workflow.py
│   └── agentic_email_workflow.py
│
├── validators/                 # Quality control validators
│   ├── base_validator.py       # Validation framework (0-25 scale)
│   ├── linkedin_validator.py   # LinkedIn-specific rules
│   ├── twitter_validator.py    # Twitter/X-specific rules
│   ├── email_validator.py      # Email-specific rules
│   └── pattern_library.py      # Writing pattern detection
│
├── slack_bot/                  # Slack integration layer
│   ├── handler.py              # Main Slack event handler
│   ├── claude_agent_handler.py # Claude Agent SDK wrapper
│   ├── memory.py               # Thread-based conversation memory
│   └── reactions.py            # Emoji-based interactions
│
├── tools/                      # Agent tools and utilities
│   ├── brand_tools.py          # Brand voice & guidelines
│   ├── content_tools.py        # Content search & analysis
│   ├── research_tools.py       # Web search via Tavily
│   ├── template_search.py      # Content template library
│   └── google_drive_sync.py    # Google Drive integration
│
├── templates/                  # Content templates & frameworks
│   ├── linkedin/               # LinkedIn post templates
│   ├── twitter/                # Twitter thread templates
│   ├── email/                  # Email templates
│   ├── ship-30/                # Ship 30 for 30 frameworks
│   └── frameworks/             # Writing frameworks (hooks, listicles)
│
├── integrations/               # External service integrations
│   ├── supabase_client.py      # Database client
│   └── airtable_client.py      # Content calendar (optional)
│
├── scripts/                    # Setup and utility scripts
│   ├── bootstrap_database.js   # Database initialization
│   └── export_database.py      # Database export utility
│
└── prompts/                    # System prompts for agents
    ├── linkedin_tools.py
    ├── twitter_tools.py
    └── email_tools.py
```

## 🛠️ Features

### Core Capabilities
- **Multi-Platform Content Creation**: LinkedIn posts, Twitter threads, Emails, YouTube scripts
- **Claude Agent SDK Integration**: Autonomous workflows with tool use and self-correction
- **Quality Validation**: 25-point scoring system with platform-specific validators
- **Pattern Detection**: Identifies overused phrases, clichés, and robotic patterns
- **RAG-Powered Research**: Semantic search across brand docs, templates, and past content
- **Conversation Memory**: Thread-based context retention for continuous conversations
- **Web Search Integration**: Real-time research via Tavily API
- **Template Library**: Ship 30 for 30 frameworks, hooks, listicles, comparisons
- **AI Detection Validation**: Optional GPTZero integration for human-likeness scoring

### Content Workflows
Each platform has specialized workflows with:
- **Research Phase**: Web search, template matching, brand voice retrieval
- **Generation Phase**: Outline → Draft → Validation → Iteration
- **Quality Control**: Validators check hooks, structure, voice, patterns
- **Iteration Loop**: Auto-revises until quality threshold met (18/25 = 72%)

### Platform Support
- **LinkedIn**: Framework posts, storytelling, professional insights
- **Twitter/X**: Threads, hot takes, comparisons, outlines
- **Email**: Value-driven, indirect sales, direct sales approaches
- **YouTube**: Video scripts with timing markers and retention hooks

### Slack Integration
- **Event Handlers**: Mentions, DMs, thread replies with deduplication
- **Slash Commands**: `/content`, `/batch`, `/calendar`, `/plan`, `/stats`
- **Reaction Controls**: Emoji-based interactions for approvals/iterations
- **Thread Memory**: Maintains conversation context within threads

## 🔧 Setup & Configuration

### 1. Environment Variables
Copy [.env.example](.env.example) to `.env` and configure:

**Required:**
- `ANTHROPIC_API_KEY` - Claude API key
- `SLACK_BOT_TOKEN` - Slack bot token (xoxb-...)
- `SLACK_SIGNING_SECRET` - Slack signing secret
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/service key
- `OPENAI_API_KEY` - OpenAI API key (for embeddings)
- `TAVILY_API_KEY` - Tavily API key (for web search)

**Optional:**
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` - AI observability
- `GPTZERO_API_KEY` - AI detection validation (human-likeness scoring)
- `AIRTABLE_ACCESS_TOKEN` - Content calendar integration
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR; default: INFO)

### 2. Database Setup
The bootstrap script creates all necessary tables and RAG functions:

```bash
node scripts/bootstrap_database.js
```

This creates:
- `knowledge_base` - Brand voice, guidelines, frameworks
- `documents` - General documents and resources
- `social_content` - Past LinkedIn/Twitter posts
- `email_content` - Past email examples
- `conversation_history` - Thread-based memory
- RAG functions with pgvector for semantic search

### 3. Slack App Setup
1. Create Slack app at https://api.slack.com/apps
2. Enable **Event Subscriptions** → Point to `https://your-domain.com/slack/events`
3. Subscribe to: `app_mention`, `message.im`, `message.channels`, `reaction_added`
4. Enable **Slash Commands**: `/content`, `/batch`, `/calendar`, `/plan`, `/stats`
5. Install app to workspace and copy tokens to `.env`

## 📖 Usage

### Slack Interactions

**Direct Mentions:**
```
@CMO write a LinkedIn post about AI automation trends in 2025
@CMO create a Twitter thread comparing X vs Y
@CMO draft an email promoting our new product
```

**Thread Replies:**
The agent maintains conversation context within threads:
```
You: @CMO write a LinkedIn post about AI agents
CMO: [generates post]
You: make it more technical
CMO: [revises with technical details]
You: both versions
CMO: [returns original + technical version]
```

**Slash Commands:**
```bash
/content linkedin AI automation trends
/batch 5 linkedin content marketing tips
/calendar                    # View upcoming scheduled content
/plan create a week of content about X
/stats                       # View content statistics
```

### Content Creation Flow

1. **User Request** → Agent analyzes intent and platform
2. **Research Phase** → Web search, template matching, brand voice
3. **Draft Generation** → Creates outline then full content
4. **Validation** → Quality scoring (0-25 scale)
5. **Iteration** → Revises until score ≥ 18/25 (72%)
6. **Delivery** → Returns content via Slack thread

### Quality Scoring (25-point scale)

Each validator checks:
- **Hook Quality** (5 pts) - Attention-grabbing, specific, tension-building
- **Content Structure** (5 pts) - Logical flow, scannable formatting
- **Brand Voice** (5 pts) - Authentic tone, avoids clichés
- **Supporting Evidence** (5 pts) - Specific examples, data, stories
- **Call-to-Action** (5 pts) - Clear next step, appropriate urgency

**Threshold:** 18/25 (72%) required to pass

### Content Validation System

The validation system runs automatically after content generation and performs two checks in parallel for optimal performance:

#### 1. Quality Check (AI Pattern Detection)
- Uses Claude to analyze content for AI writing patterns
- Detects robotic phrases, clichés, and overused expressions
- Scores content on 5 dimensions (0-5 each):
  - Hook quality (attention-grabbing, specific)
  - Proof points (data, examples, specificity)
  - Structure (flow, formatting, readability)
  - Call-to-action (clear, appropriate urgency)
  - Human-likeness (varied sentences, natural voice)
- Returns: Score (0-25), decision (accept/revise/reject), surgical fixes

#### 2. GPTZero AI Detection (Optional)
- Analyzes content for AI-generation probability
- Requires `GPTZERO_API_KEY` environment variable
- Returns: Human probability, AI probability, flagged sentences
- **Threshold:** >70% human probability = PASS

**Validation Results:**
- Saved to Airtable "Suggested Edits" field (human-readable format)
- Includes quality breakdown, AI patterns found, recommended fixes
- GPTZero results (if configured)
- Available in Supabase for analytics

**Performance:**
- Validators run in parallel using `asyncio.gather()`
- Total validation time: ~3-5 seconds (vs 6-8s sequential)
- Graceful degradation: Works without GPTZero API key

**Example validation output in Airtable:**
```
🔍 CONTENT VALIDATION REPORT
================================================
✅ OVERALL: ACCEPT (Score: 20/25)

📊 Quality Breakdown:
   • Hook: 4/5
   • Proof: 4/5
   • Structure: 4/5
   • Cta: 4/5
   • Human: 4/5

⚡ AI Patterns Detected:
   • Contrast structure: "It's not X, it's Y"

💡 Recommended Fixes:
   Remove contrast framing. State point directly.

✅ GPTZero AI Detection:
   • Human-written: 78.5%
   • AI-generated: 21.5%

📅 Generated: 2025-10-16 10:00:00
```

## 🎯 Deployment

### Client Deployment (Replit)

For detailed deployment instructions, see **[docs/CLIENT_DEPLOYMENT.md](docs/CLIENT_DEPLOYMENT.md)**

**Quick Start:**
```bash
# 1. First-time setup
bash scripts/client_setup.sh

# 2. Create brand context
cp .claude/CLAUDE.md.example .claude/CLAUDE.md
nano .claude/CLAUDE.md  # Edit with your brand voice

# 3. Bootstrap database
node scripts/bootstrap_database.js

# 4. Start the agent
npm start
```

**Update to Latest:**
```bash
# Safe update (handles divergent branches)
bash scripts/client_update.sh review-fix

# Or for production:
bash scripts/client_update.sh main
```

**Why this matters:**
- ✅ Your `.claude/CLAUDE.md` customizations are **gitignored** (safe from updates)
- ✅ Update scripts preserve your brand context
- ✅ System prompts are automatically cached (90% cost savings)
- ✅ No merge conflicts when pulling updates

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Bootstrap database
node scripts/bootstrap_database.js

# Start server
npm start
```

### Production (Railway/Render/Fly.io)
1. Set environment variables in platform dashboard
2. Deploy from GitHub repository
3. Platform will run: `npm install` → `npm start`
4. Bootstrap script runs automatically via `prestart` hook

### Environment Setup
- **Railway**: Add env vars in dashboard → Deploy
- **Render**: Create Web Service → Add env vars → Deploy
- **Fly.io**: `fly secrets set KEY=value` → `fly deploy`
- **Replit**: See [docs/CLIENT_DEPLOYMENT.md](docs/CLIENT_DEPLOYMENT.md)

## 🔧 Architecture

### Claude Agent SDK Integration
The agent uses Anthropic's Claude Agent SDK for autonomous operation:

```python
# agents/linkedin_sdk_agent.py
from claude_agent_sdk import Agent, tool

agent = Agent(
    name="LinkedIn Content Creator",
    tools=[
        web_search_tool,
        search_templates_tool,
        search_knowledge_base_tool,
        quality_check_tool
    ]
)

# Agent autonomously:
# 1. Researches topic via web search
# 2. Finds relevant templates
# 3. Retrieves brand voice
# 4. Generates content
# 5. Validates quality
# 6. Iterates until threshold met
```

### Workflow Orchestration
Each platform has a specialized workflow:

```python
# workflows/agentic_linkedin_workflow.py
class AgenticLinkedInWorkflow:
    async def create_content(self, topic: str):
        # 1. Research phase
        research = await agent.research(topic)

        # 2. Generation phase
        draft = await agent.generate(research)

        # 3. Validation phase
        score = validator.validate(draft)

        # 4. Iteration phase (if needed)
        while score < 18:
            feedback = validator.get_feedback(draft)
            draft = await agent.revise(draft, feedback)
            score = validator.validate(draft)

        return draft
```

### Memory System
Thread-based memory maintains conversation context:

```python
# slack_bot/memory.py
class ConversationMemory:
    def get_context(self, thread_ts: str) -> List[Dict]:
        """Retrieve last N messages from thread"""

    def add_message(self, thread_ts: str, role: str, content: str):
        """Store message in conversation history"""
```

## 🧪 Testing

```bash
# Test database connection
node test_supabase_connection.js

# Test content generation
python test_generated_posts.py

# Run validator tests
python -m pytest validators/tests/
```

## 📚 Resources

- **Claude Agent SDK**: [docs.anthropic.com](https://docs.anthropic.com/claude/docs/agent-sdk)
- **Supabase**: [supabase.com/docs](https://supabase.com/docs)
- **Tavily API**: [docs.tavily.com](https://docs.tavily.com)
- **Langfuse**: [langfuse.com/docs](https://langfuse.com/docs)

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with:** Claude Agent SDK • FastAPI • Supabase • Slack SDK • Tavily

**Author:** Mitch Harris

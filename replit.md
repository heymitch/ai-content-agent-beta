# AI Content Agent Template

## Overview

An autonomous content creation system that lives in Slack and generates high-quality LinkedIn posts, Twitter threads, emails, and YouTube scripts. Built on Anthropic's Claude Agent SDK with a 3-tier architecture: orchestrator agents delegate to specialized tool agents, which use validators to ensure quality. Content is iteratively refined until it meets platform-specific quality thresholds (typically 85/100), with human-like writing enforced through comprehensive pattern detection.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Agent Architecture (3-Tier Hierarchy)

**Tier 1: Slack Interface**
- `main_slack.py` - FastAPI app handling Slack events (messages, reactions, commands)
- `SlackContentHandler` - Routes requests to appropriate workflows
- Thread-based conversation memory via Supabase
- Emoji reactions trigger actions (📅 schedule, ✏️ revise, 🔄 regenerate)

**Tier 2: Platform Orchestrators (SDK Agents)**
- `LinkedInSDKAgent` - Delegates to hook generator, proof injector, editor tools
- `TwitterSDKAgent` - Manages thread creation with format selection
- `EmailSDKAgent` - Handles value/indirect/direct email types
- `YouTubeSDKAgent` - Generates scripts with timing markers
- Each uses Claude Agent SDK with persistent memory and lazy-loaded prompts

**Tier 3: Specialized Tools**
- Hook generation (5 variations using proven frameworks)
- Proof injection (adds data, stats, concrete examples)
- Web search (Tavily API for current events/research)
- Knowledge base search (RAG via Supabase pgvector)
- Template search (semantic matching against format library)

### Validation System (Hybrid: Code + LLM)

**Code Validators** (Fast, deterministic)
- `LinkedInValidator` - Checks hook strength, proof points, line length, forbidden patterns
- `TwitterValidator` - Character limits, thread structure, emoji usage
- `EmailValidator` - Subject lines, spam triggers, word count by type
- Scoring: 0-25 scale across multiple quality axes

**LLM Validator** (Strategic, creative)
- Grades content holistically after code validation
- Identifies vague claims, weak hooks, missing proof
- Returns specific improvement suggestions

**Hybrid Editor**
- Applies regex fixes for deterministic issues (formatting, banned words)
- Uses LLM for strategic rewrites (improving hooks, adding specificity)

### Data Architecture

**Supabase Tables**
- `content_examples` - 741 high-performing posts with embeddings (RAG)
- `conversation_history` - Thread memory for Slack conversations
- `generated_posts` - Created content with quality scores
- `research` - Industry research digests
- `company_documents` - Brand voice and product docs
- `performance_analytics` - Content performance tracking

**Vector Search** (pgvector with IVFFlat index)
- `match_content_examples()` - Semantic similarity for finding relevant examples
- `search_generated_posts()` - Search past created content
- Embeddings: OpenAI text-embedding-3-small (1536 dimensions)

**Airtable Integration**
- Content calendar with status tracking (Draft → Scheduled → Published)
- Quality scores, suggested edits, publish dates
- Replaces n8n webhook with direct API calls

### Writing Quality System

**Global Writing Rules** (`WRITE_LIKE_HUMAN_RULES`)
- Cached across all prompts (~80% token savings)
- Enforces: short sentences (10-20 words), active voice (90%), concrete details
- Bans: semicolons, em dashes, buzzwords (leverage, utilize, cutting-edge)
- Detects AI patterns: contrast structures ("It's not X, it's Y"), rule of three

**Pattern Detection** (`ForbiddenPatterns`)
- AI tells: contrast framing, parallel structure with exactly 3 items
- Overused phrases: "At the end of the day", "When it comes to"
- Banned words: however, moreover, furthermore, consequently

**Quality Thresholds**
- LinkedIn: 85/100 minimum (targets 90+)
- Twitter: 18/25 minimum (80-90% human detection on GPTZero)
- Email: Type-specific (Value: 400-500 words, Direct: 100-200 words)

### Content Workflow

1. **User Request** → Slack message or slash command (`/content linkedin AI infrastructure`)
2. **Research Phase** → Agent autonomously searches web, knowledge base, templates
3. **Generation** → Platform orchestrator delegates to specialized tools
4. **Validation** → Code validator + LLM grading (target: 85/100)
5. **Iteration** → Hybrid editor fixes issues (max 3 iterations)
6. **Delivery** → Posted to Slack thread, optionally scheduled to Airtable

### Prompt Optimization

**Lazy Loading Pattern**
- Tool descriptions kept minimal in SDK definitions
- Detailed prompts loaded just-in-time when tools execute
- Reduces context window usage by ~70%

**Prompt Caching**
- `WRITE_LIKE_HUMAN_RULES` constant reused across all generations
- Anthropic recognizes exact string and caches it
- Saves ~80% tokens on writing guidelines

## External Dependencies

### AI Services
- **Anthropic Claude** - Agent SDK (primary reasoning), Sonnet 3.5 (content generation)
- **OpenAI** - Embeddings (text-embedding-3-small), GPTZero for human detection scoring

### Search & Research
- **Tavily API** - Web search for current events, examples, data points
- Integrates with year/date queries for accuracy ("OpenAI Dev Day 2025")

### Data Storage
- **Supabase** - PostgreSQL with pgvector extension
  - Tables: content_examples, conversation_history, generated_posts, research, company_documents
  - RPC functions: match_content_examples, search_generated_posts
  - Connection: Transaction pooler (port 6543) for Replit compatibility
- **Airtable** - Content calendar management
  - Fields: Post Hook, Body Content, Status, Platform, Publish Date, % Score
  - Direct API integration (pyairtable)

### Communication
- **Slack** - Primary interface
  - Event subscriptions: message.channels, app_mention, reaction_added
  - Slash commands: /content, /calendar, /batch
  - Bot token for posting, reactions, thread management

### Document Processing (Optional)
- **pypdf2** - PDF parsing for company documents
- **python-docx** - Word document parsing
- **markdown** - Markdown parsing
- Not required for Slack-only operation

### Development Tools
- **FastAPI** - Web framework for Slack webhook handling
- **Langfuse** - Observability for agent execution traces
- **pytest** - Testing framework
- **Node.js** - Database bootstrap scripts (pg library)

### Deployment
- **Replit** - Primary hosting platform
  - Auto-setup via `prestart` hook (runs bootstrap_database.js)
  - Secrets management for API keys
  - Persistent storage for .env files
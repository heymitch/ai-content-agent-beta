# AI Content Agent Template

## Overview

This is a production-ready AI content creation system that lives entirely in Slack. It generates high-quality, human-like content for LinkedIn, Twitter/X, Email, and YouTube using Anthropic's Claude Agent SDK. The system uses a multi-agent architecture with quality validation, iterative editing, and semantic knowledge retrieval to create content that scores 85+ on quality metrics and passes AI detection at 80-90% human rates.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern: Multi-Agent Workflow System

The application uses a **3-tier agent hierarchy** with specialized sub-agents:

1. **Tier 1: Main Orchestrator (CMO Agent)** - Lives in Slack, routes requests to platform-specific workflows
2. **Tier 2: Platform SDK Agents** - Claude Agent SDK implementations for LinkedIn, Twitter, Email, YouTube
3. **Tier 3: Specialized Tools** - Hook generation, proof injection, quality validation, research

**Key Design Decisions:**

- **Why multi-agent?** Single monolithic prompts hit context limits and reduce quality. Specialized agents maintain focus on specific tasks (hooks vs body vs editing).
- **Why Claude Agent SDK?** Provides persistent memory, tool-calling capabilities, and structured workflows. Enables agents to autonomously decide when to search for examples, research data, or validate quality.
- **Quality-first approach:** All content goes through validation (hybrid code + LLM) and iterative editing until hitting 85+ score threshold.

### Content Generation Flow

1. **User request** arrives via Slack message or emoji reaction
2. **Main handler** (main_slack.py) parses intent and routes to platform workflow
3. **SDK Agent** executes multi-step workflow:
   - Research phase (web search, knowledge base lookup)
   - Hook generation (5 options, user picks best)
   - Body generation (follows platform-specific rules)
   - Proof injection (adds specific numbers, data, examples)
   - Quality validation (hybrid validator scores 0-25 scale)
   - Iterative editing (hybrid editor fixes issues until score hits target)
4. **Content saved** to Airtable (calendar) and Supabase (knowledge base with embeddings)
5. **Slack response** with formatted content, quality score, and action buttons

### Database Architecture (Supabase)

**Primary Tables:**
- `content_examples` - High-performing content with embeddings for RAG (741 rows with vector search)
- `generated_posts` - All generated content with quality scores
- `conversation_history` - Slack thread memory for context continuity
- `company_documents` - Brand voice, product docs (RAG source)
- `research` - Industry research digests with embeddings

**Why Supabase?** Provides PostgreSQL with pgvector extension for semantic search. RAG functions use IVFFlat indexes for fast similarity matching (~100ms queries).

**Embedding Strategy:** 
- Model: text-embedding-3-small (OpenAI)
- Dimension: 1536
- Generated on content save, used for semantic search via RPC functions

### Validation System

**Hybrid Validation Approach:**
- **Code-based rules** (regex, structure checks) - Fast, deterministic, catches formatting issues
- **LLM validation** (Claude Haiku) - Catches AI patterns, evaluates quality, provides reasoning

**Quality Scoring (0-25 scale):**
- Hook strength: /5
- Structure: /5  
- Specificity: /5
- Voice authenticity: /5
- Engagement potential: /5

**Why 0-25 scale?** Converts to percentage (85/100 = 21.25/25). More granular than pass/fail, enables iterative improvement.

### Platform-Specific Workflows

**LinkedIn** (`agents/linkedin_sdk_agent.py`):
- Length: 100-300 words optimal
- Structure: Hook → Body → CTA
- Quality gates: No AI buzzwords, specific numbers, authentic voice
- Tools: Hook generator, proof injector, web search, template search

**Twitter/X** (`agents/twitter_sdk_agent.py`):
- Length: 280 chars per tweet, 5-7 tweet threads
- Formats: Paragraph, What/How/Why, Listicle, Old vs New
- Quality gates: 18/25 minimum, human detection 80%+
- Autonomous format selection based on topic

**Email** (`agents/email_sdk_agent.py`):
- Types: Value (400-500 words), Indirect (400-600 words), Direct (100-200 words)
- Quality gates: Subject line A/B tested, clear CTA, skimmable structure
- Autonomous type selection based on audience warmth

**YouTube** (`agents/youtube_sdk_agent.py`):
- Structure: Script with timing markers (0:00, 0:30, etc.)
- Length: 8-12 minutes optimal
- Quality gates: Retention hooks every 90 seconds, clear B-roll cues

### Knowledge Base & RAG

**RAG Strategy:**
- Semantic search for similar content examples (match_content_examples RPC)
- Metadata filtering by platform, content_type, performance score
- Cross-platform principle extraction (structural patterns vs topic matching)

**Why this approach?** Topic-based search fails for generic requests. Principle-based search finds structural patterns (e.g., "listicle with 7 items") that work across any topic.

### Memory & Context Management

**Thread-based memory** (Slack conversations):
- Stores conversation history per thread_ts
- Enables iterative refinement ("make it shorter", "add more data")
- TTL: 24 hours for bot participation tracking

**Why thread-based?** Each Slack thread is isolated content creation session. Users can have multiple parallel sessions without context bleeding.

### Error Handling & Rate Limiting

**Anthropic Rate Limits:**
- Messages API: 50 requests/min
- Implementation: Exponential backoff with jitter
- Retry strategy: 3 attempts max, 2^attempt * 1s delay

**Supabase Connection Pooling:**
- Transaction pooler (port 6543) for serverless environments
- Connection reuse via singleton pattern
- Fallback to direct connection (port 5432) if pooler fails

## External Dependencies

### AI/ML Services
- **Anthropic Claude** (claude-sonnet-4-5) - Primary content generation, quality validation
- **OpenAI** (text-embedding-3-small) - Embeddings for semantic search
- **GPTZero API** - Optional AI detection scoring

### Data Storage
- **Supabase** (PostgreSQL + pgvector) - Primary database with vector search
- **Airtable** - Content calendar and scheduling (optional)

### Integrations
- **Slack SDK** - Bot interface, event handling, reactions
- **Tavily API** - Web search for current events and research
- **Google Drive API** - Optional document sync for brand voice

### Infrastructure
- **FastAPI** - Web server for Slack webhooks
- **Uvicorn** - ASGI server (runs on port 5000)
- **Replit** - Deployment environment (requires SUPABASE_DB_URL in secrets)

### Key Libraries
- `claude-agent-sdk>=0.1.0` - Claude Agent SDK for workflows
- `anthropic>=0.39.0` - Anthropic Messages API
- `supabase` - Database client with pgvector support
- `slack-sdk` - Slack integration
- `tavily-python` - Web search
- `pyairtable` - Airtable API

**Note:** The application does NOT require PostgreSQL client installation. Database setup uses Node.js scripts (`pg` package) or REST API methods for Replit compatibility.
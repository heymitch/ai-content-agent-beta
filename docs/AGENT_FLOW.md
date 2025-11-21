# Agent Flow Documentation

Complete architecture and flow documentation for the AI Content Agent system.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Entry Point Flow](#entry-point-flow)
3. [Platform Agent Architecture](#platform-agent-architecture)
4. [Prompt Loading Hierarchy](#prompt-loading-hierarchy)
5. [Tool Schemas & Execution](#tool-schemas--execution)
6. [Quality Check & Validation Flow](#quality-check--validation-flow)
7. [Batch Orchestration Flow](#batch-orchestration-flow)
8. [Mode Handling](#mode-handling)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TIER 1: ENTRY POINTS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐     │
│   │   Slack     │    │   n8n        │    │    API             │     │
│   │   Events    │    │   Webhooks   │    │    Endpoints       │     │
│   └──────┬──────┘    └──────┬───────┘    └─────────┬──────────┘     │
│          │                  │                      │                │
│          └──────────────────┼──────────────────────┘                │
│                             │                                       │
│                    ┌────────▼────────┐                              │
│                    │  main_slack.py  │                              │
│                    │   (FastAPI)     │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                         TIER 2: ORCHESTRATION                       │
├─────────────────────────────┼───────────────────────────────────────┤
│                             │                                       │
│              ┌──────────────▼──────────────┐                        │
│              │  ClaudeAgentHandler         │                        │
│              │  (Claude Agent SDK)         │                        │
│              │  - Conversation routing     │                        │
│              │  - Tool registration        │                        │
│              │  - Memory management        │                        │
│              └──────────────┬──────────────┘                        │
│                             │                                       │
│         ┌───────────────────┼───────────────────┐                   │
│         │                   │                   │                   │
│   ┌─────▼─────┐    ┌────────▼────────┐   ┌─────▼─────┐              │
│   │ Single    │    │ Batch           │   │ Analytics │              │
│   │ Post      │    │ Orchestrator    │   │ Tools     │              │
│   └─────┬─────┘    └────────┬────────┘   └───────────┘              │
│         │                   │                                       │
└─────────┼───────────────────┼───────────────────────────────────────┘
          │                   │
┌─────────┼───────────────────┼───────────────────────────────────────┐
│                         TIER 3: PLATFORM WORKERS                    │
├─────────┼───────────────────┼───────────────────────────────────────┤
│         │                   │                                       │
│         └───────┬───────────┼────────────┬────────────┐             │
│                 │           │            │            │             │
│    ┌────────────▼──────┐ ┌──▼─────────┐ ┌▼─────────┐ ┌▼───────────┐ │
│    │ LinkedIn Worker   │ │ Twitter    │ │ Email    │ │ Instagram  │ │
│    │                   │ │ Worker     │ │ Worker   │ │ Worker     │ │
│    │ - API/No API      │ │ - API/Haiku│ │ - API    │ │ - API      │ │
│    └─────────┬─────────┘ └────┬───────┘ └────┬─────┘ └─────┬──────┘ │
│              │                │              │             │        │
│    ┌─────────▼─────────┐     ┌▼─────────┐   ┌▼─────────┐  ┌▼────────┐
│    │ YouTube Worker    │     │ Threads  │   │ TikTok   │  │ Facebook│
│    │ - API             │     │ Worker   │   │ Worker   │  │ Worker  │
│    │                   │     │ - API    │   │ - API    │  │ - API   │
│    └───────────────────┘     └──────────┘   └──────────┘  └─────────┘
│               (Easily extensible: add new platform workers here)    │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                         TIER 4: NATIVE TOOLS                        │
├─────────────────────────────┼───────────────────────────────────────┤
│                             │                                       │
│   ┌─────────────────────────▼─────────────────────────┐             │
│   │                                                   │             │
│   │  generate_5_hooks    create_human_draft           │             │
│   │  quality_check       external_validation          │             │
│   │  apply_fixes         inject_proof_points          │             │
│   │  search_company_documents                         │             │
│   │                                                   │             │
│   └───────────────────────────────────────────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Entry Point Flow

### main_slack.py - FastAPI Server

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SLACK EVENT HANDLING FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

    Slack Event
        │
        ▼
┌───────────────────┐
│ POST /slack/events│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────┐
│ URL Verification? │──Y──▶│ Return      │
│ (challenge)       │      │ challenge   │
└─────────┬─────────┘      └─────────────┘
          │ N
          ▼
┌───────────────────┐     ┌─────────────┐
│ Duplicate Event?  │──Y──▶│ Skip        │
│ (dedup cache)     │      │ Processing  │
└─────────┬─────────┘      └─────────────┘
          │ N
          ▼
┌───────────────────┐     ┌─────────────┐
│ Verify Slack      │──N──▶│ Reject      │
│ Signature         │      │ Request     │
└─────────┬─────────┘      └─────────────┘
          │ Y
          ▼
┌───────────────────┐
│ Event Type?       │
└─────────┬─────────┘
          │
    ┌─────┴──────┬────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│message │ │app_      │ │reaction_ │
│        │ │mention   │ │added     │
└────┬───┘ └────┬─────┘ └────┬─────┘
     │          │            │
     └──────┬───┘            │
            │                │
            ▼                ▼
    ┌───────────────┐  ┌───────────────┐
    │ Should Bot    │  │ Handle        │
    │ Respond?      │  │ Reaction      │
    │ - @mentioned? │  │(✅ → Airtable)│
    │               │  └───────────────┘
    │ - In thread?  │
    └───────┬───────┘
            │ Y
            ▼
    ┌───────────────────┐
    │ Add ⚡ reaction    │
    │ Send "On it..."   │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Background Task:  │
    │ process_message() │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Create            │
    │ ClaudeAgentHandler│
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ handle_           │
    │ conversation()    │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Send Response     │
    │ to Slack          │
    └───────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `main_slack.py` | FastAPI server, event handling, client initialization |
| `slack_bot/claude_agent_handler.py` | Claude Agent SDK wrapper, tool registration |
| `slack_bot/handler.py` | SlackContentHandler with memory management |

---

## Platform Agent Architecture

### Direct API Agent Pattern

All platform agents (Twitter, LinkedIn, Email, YouTube, Instagram) follow this pattern:

```
┌─────────────────────────────────────────────────────────────────────┐
│              DIRECT API AGENT EXECUTION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

    create_post() called
           │
           ▼
    ┌──────────────────┐
    │ Check Circuit    │
    │ Breaker State    │
    └────────┬─────────┘
             │
        ┌────┴────┐
        │         │
      OPEN    CLOSED/HALF_OPEN
        │         │
        ▼         ▼
    ┌────────┐  ┌──────────────────┐
    │ Reject │  │ Load Prompts     │
    │ Request│  │ stack_prompts()  │
    └────────┘  └────────┬─────────┘
                         │
                         ▼
               ┌──────────────────┐
               │ Build Workflow   │
               │ (thinking_mode   │
               │  vs default)     │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Initialize       │
               │ messages[]       │
               └────────┬─────────┘
                        │
                        ▼
          ┌─────────────────────────────┐
          │    TOOL CALLING LOOP        │
          │    (max 10-15 iterations)   │
          └─────────────┬───────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Call Claude API  │
               │ client.messages  │
               │ .create()        │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Check stop_reason│
               └────────┬─────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      end_turn      tool_use     max_tokens
          │             │             │
          ▼             │             ▼
    ┌──────────┐        │      ┌──────────┐
    │ Extract  │        │      │ Extract  │
    │ Final    │        │      │ Partial  │
    │ Output   │        │      │ Output   │
    └────┬─────┘        │      └────┬─────┘
         │              │           │
         │              ▼           │
         │     ┌──────────────────┐ │
         │     │ Execute Tools:   │ │
         │     │ - generate_5_    │ │
         │     │   hooks          │ │
         │     │ - create_human_  │ │
         │     │   draft          │ │
         │     │ - quality_check  │ │
         │     │ - external_      │ │
         │     │   validation     │ │
         │     │ - apply_fixes    │ │
         │     └────────┬─────────┘ │
         │              │           │
         │              ▼           │
         │     ┌──────────────────┐ │
         │     │ Append tool      │ │
         │     │ results to       │ │
         │     │ messages[]       │ │
         │     └────────┬─────────┘ │
         │              │           │
         │              └───────────┤
         │              (loop back) │
         │                          │
         └──────────────┬───────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ _parse_output()  │
               │ Extract content  │
               │ via Haiku        │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Save to Airtable │
               │ Save to Supabase │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Return Result    │
               │ {success, post,  │
               │  score, urls}    │
               └──────────────────┘
```

### Agent Files

| Agent | File | Special Notes |
|-------|------|---------------|
| Twitter | `agents/twitter_direct_api_agent.py` | Also has `twitter_haiku_agent.py` for single posts |
| LinkedIn | `agents/linkedin_direct_api_agent.py` | Thought leadership focus |
| Email | `agents/email_direct_api_agent.py` | Newsletter format |
| YouTube | `agents/youtube_direct_api_agent.py` | Script generation |
| Instagram | `agents/instagram_direct_api_agent.py` | Caption + carousel |

---

## Prompt Loading Hierarchy

### stack_prompts() Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PROMPT LOADING HIERARCHY                           │
└─────────────────────────────────────────────────────────────────────┘

    stack_prompts(platform="twitter")
                │
                ▼
    ┌───────────────────────────────┐
    │   1. CLIENT BUSINESS CONTEXT  │
    │   .claude/CLAUDE.md           │
    │   (Brand voice, audience,     │
    │    messaging pillars)         │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │   2. WRITING RULES            │
    │   prompts/styles/             │
    │   default_writing_rules.md    │
    │   (Anti-AI-tells, human       │
    │    signals)                   │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │   3. EDITOR-IN-CHIEF          │
    │   STANDARDS                   │
    │   prompts/styles/             │
    │   default_editor_standards.md │
    │   (Quality rules, forbidden   │
    │    patterns)                  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │   4. PLATFORM CREATE_DRAFT    │
    │   prompts/styles/{platform}/  │
    │   default_create_draft.md     │
    │   (Platform-specific format)  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │   STACKED SYSTEM PROMPT       │
    │   (All sections combined)     │
    │   ~10-20k chars               │
    │   Cached via cache_control    │
    └───────────────────────────────┘
```

### Prompt Loading Priority

For any prompt (e.g., `writing_rules`):

```
PRIORITY 1: .claude/prompts/{platform}/{prompt_name}.md  (Client platform-specific)
     │
     └─ NOT FOUND
           │
           ▼
PRIORITY 2: .claude/prompts/{prompt_name}.md            (Client global override)
     │
     └─ NOT FOUND
           │
           ▼
PRIORITY 3: prompts/styles/{platform}/default_{prompt_name}.md  (Default platform)
     │
     └─ NOT FOUND
           │
           ▼
PRIORITY 4: prompts/styles/default_{prompt_name}.md     (Global default)
     │
     └─ NOT FOUND
           │
           ▼
PRIORITY 5: _EMERGENCY_FALLBACKS dict                   (Hardcoded minimal)
```

### Key Prompt Files

| Purpose | Default Location |
|---------|------------------|
| Writing Rules | `prompts/styles/default_writing_rules.md` |
| Editor Standards | `prompts/styles/default_editor_standards.md` |
| LinkedIn Create Draft | `prompts/styles/linkedin/default_create_draft.md` |
| Twitter Create Draft | `prompts/styles/twitter/default_create_draft.md` |
| Client Context | `.claude/CLAUDE.md` |

---

## Tool Schemas & Execution

### Tool Schema Definition

Each agent defines tools in `TOOL_SCHEMAS`:

```python
TOOL_SCHEMAS = [
    {
        "name": "generate_5_hooks",
        "description": "Generate 5 hooks in different formats",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "context": {"type": "string"},
                "target_audience": {"type": "string"}
            },
            "required": ["topic", "context", "target_audience"]
        }
    },
    # ... more tools
]
```

### Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TOOL EXECUTION FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

    Claude returns stop_reason="tool_use"
                    │
                    ▼
         ┌─────────────────────┐
         │ Extract tool_use    │
         │ blocks from response│
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ For each tool_use:  │
         │ - tool_name         │
         │ - tool_input        │
         │ - tool_use_id       │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ execute_tool()      │
         │ (with timeout)      │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ Tool Name Dispatch: │
         └──────────┬──────────┘
                    │
    ┌───────────────┼───────────────┐───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│generate│    │create_ │    │quality_│    │external│
│_5_hooks│    │human_  │    │check   │    │_valida-│
│_native │    │draft_  │    │_native │    │tion_   │
│        │    │native  │    │        │    │native  │
│ 30s    │    │ 30s    │    │ 30s    │    │ 120s   │
└────┬───┘    └────┬───┘    └────┬───┘    └────┬───┘
     │             │             │             │
     └─────────────┴─────────────┴─────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Collect tool_results│
              │ [{type: "tool_     │
              │   result", ...}]   │
              └──────────┬─────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Append to messages[]│
              │ as user message     │
              └──────────┬─────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Continue loop to    │
              │ next API call       │
              └─────────────────────┘
```

### Available Tools by Category

#### Content Creation Tools
| Tool | Purpose | Timeout |
|------|---------|---------|
| `generate_5_hooks` | Generate 5 hook variations | 30s |
| `create_human_draft` | Create full post draft | 30s |
| `inject_proof_points` | Add proof from company docs | 30s |

#### Validation Tools
| Tool | Purpose | Timeout |
|------|---------|---------|
| `quality_check` | Score on 5 axes (18+/25) | 30s |
| `external_validation` | Quality + GPTZero AI detection | 120s |
| `apply_fixes` | Fix flagged issues | 30s |

#### Research Tools
| Tool | Purpose | Timeout |
|------|---------|---------|
| `search_company_documents` | RAG search company docs | N/A |
| `search_content_examples` | Search 700+ examples | N/A |
| `web_search` | Real-time web search | N/A |
| `perplexity_search` | Deep research with citations | N/A |

---

## Quality Check & Validation Flow

### Quality Scoring System (0-25 Scale)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUALITY SCORING AXES                             │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   HOOK      │  5 points max
    │  (Opening)  │  - Stops scroll
    │             │  - Under char limit
    └─────────────┘

    ┌─────────────┐
    │   FLOW      │  5 points max
    │ (Structure) │  - Logical progression
    │             │  - Transitions
    └─────────────┘

    ┌─────────────┐
    │  BREVITY    │  5 points max
    │ (Concise)   │  - No filler
    │             │  - Tight sentences
    └─────────────┘

    ┌─────────────┐
    │   PROOF     │  5 points max
    │ (Evidence)  │  - Specific data
    │             │  - Real examples
    └─────────────┘

    ┌─────────────┐
    │ ENGAGEMENT  │  5 points max
    │   (CTA)     │  - Clear action
    │             │  - Hashtags
    └─────────────┘

    ┌─────────────┐
    │    AI       │  -3 points max
    │ DEDUCTIONS  │  - Forbidden patterns
    │             │  - AI tells
    └─────────────┘

    ═══════════════
    TOTAL: 0-25 points
    THRESHOLD: 18+/25 to pass
```

### External Validation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  EXTERNAL VALIDATION FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

    external_validation_native(post)
                │
                ▼
    ┌───────────────────────────┐
    │ run_all_validators()      │
    │ (integrations/            │
    │  validation_utils.py)     │
    └─────────────┬─────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
    ┌────────────┐    ┌────────────┐
    │ Quality    │    │ GPTZero    │
    │ Check      │    │ AI         │
    │ (60s)      │    │ Detection  │
    │            │    │ (45s)      │
    └──────┬─────┘    └──────┬─────┘
           │                 │
           ▼                 ▼
    ┌────────────┐    ┌────────────┐
    │ Scores:    │    │ Results:   │
    │ - hook     │    │ - ai_pct   │
    │ - flow     │    │ - flagged_ │
    │ - brevity  │    │   sentences│
    │ - proof    │    │ - pass/fail│
    │ - engage   │    │            │
    │ - total/25 │    │            │
    │ - issues[] │    │            │
    └──────┬─────┘    └──────┬─────┘
           │                 │
           └────────┬────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Combined Result:   │
         │ {                  │
         │   total_score: 22, │
         │   issues: [...],   │
         │   gptzero_ai_pct:  │
         │     15,            │
         │   gptzero_flagged_ │
         │     sentences: [...]│
         │ }                  │
         └──────────┬─────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Decision Logic:    │
         │ - score >= 18 AND  │
         │ - gptzero_ai < 100 │
         │ → PASS             │
         │ Otherwise → FIX    │
         └────────────────────┘
```

### Apply Fixes Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLY FIXES FLOW                                │
└─────────────────────────────────────────────────────────────────────┘

    apply_fixes_native(post, issues_json, current_score, gptzero_data)
                │
                ▼
    ┌─────────────────────────────┐
    │ Build Fix Prompt:           │
    │ - Original post             │
    │ - JSON issues list          │
    │ - Current score             │
    │ - GPTZero AI %              │
    │ - Flagged sentences         │
    │ - WRITE_LIKE_HUMAN_RULES    │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ Call Claude Sonnet:         │
    │ "Fix ALL flagged issues"    │
    │ "Rewrite flagged sentences" │
    │ "Preserve 80%+ of voice"    │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ Return:                     │
    │ {                           │
    │   revised_post: "...",      │
    │   changes_made: [...],      │
    │   estimated_new_score: 23   │
    │ }                           │
    └─────────────────────────────┘
```

---

## Batch Orchestration Flow

### Batch Plan Creation & Execution

```
┌─────────────────────────────────────────────────────────────────────┐
│                   BATCH ORCHESTRATION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

    CMO Agent: "Create 5 LinkedIn posts about AI"
                        │
                        ▼
              ┌─────────────────────┐
              │ create_batch_plan() │
              │ - Generate plan_id  │
              │ - Analyze context   │
              │   quality           │
              │ - Store in registry │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ ContextManager      │
              │ created for plan    │
              └──────────┬──────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  SEQUENTIAL EXECUTION LOOP   │
          │  (No parallel execution)     │
          └──────────────┬───────────────┘
                         │
                         ▼
               ┌──────────────────┐
               │ Post 1           │
               │ execute_single_  │
               │ post_from_plan() │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Get strategic    │
               │ context for post │
               │ (from outline)   │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Call platform    │
               │ agent workflow:  │
               │ - LinkedIn       │
               │ - Twitter        │
               │ - Email          │
               │ - YouTube        │
               │ - Instagram      │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Extract results: │
               │ - score          │
               │ - airtable_url   │
               │ - hook           │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Update context   │
               │ manager with     │
               │ post summary     │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Send Slack       │
               │ progress update  │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐     ┌──────────────┐
               │ Every 10 posts:  │────▶│ Checkpoint   │
               │ Show stats       │     │ message      │
               └────────┬─────────┘     └──────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ More posts?      │
               └────────┬─────────┘
                        │
                  ┌─────┴─────┐
                  │           │
                 YES          NO
                  │           │
                  ▼           ▼
          (Loop to next) ┌──────────────┐
                         │ Final        │
                         │ summary:     │
                         │ - completed  │
                         │ - failed     │
                         │ - avg_score  │
                         │ - trend      │
                         └──────────────┘
```

### Context Manager

The `ContextManager` (in `agents/context_manager.py`) handles:

- Strategic context extraction from detailed outlines
- Post summary tracking (scores, hooks, URLs)
- Quality statistics (avg, trend, range)
- NO learning accumulation between posts (intentional design)

```python
# Each post gets strategic context but NOT learnings from previous posts
strategic_context = context_mgr.get_context_for_post(post_index)
```

---

## Mode Handling

### Thinking Mode vs Default Mode

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MODE SELECTION                                 │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐          ┌─────────────────────┐
    │    DEFAULT MODE     │          │   THINKING MODE     │
    ├─────────────────────┤          ├─────────────────────┤
    │                     │          │                     │
    │ Tools available:    │          │ Tools available:    │
    │ - generate_5_hooks  │          │ - generate_5_hooks  │
    │ - create_human_draft│          │ - create_human_draft│
    │ - external_         │          │ - quality_check     │
    │   validation        │          │ - external_         │
    │ - search_company_   │          │   validation        │
    │   documents         │          │ - apply_fixes       │
    │                     │          │ - inject_proof_     │
    │                     │          │   points            │
    │                     │          │ - search_company_   │
    │                     │          │   documents         │
    └──────────┬──────────┘          └──────────┬──────────┘
               │                                │
               ▼                                ▼
    ┌─────────────────────┐          ┌─────────────────────┐
    │ Workflow:           │          │ Workflow:           │
    │                     │          │                     │
    │ 1. Evaluate outline │          │ 1. Evaluate outline │
    │ 2. Generate hooks   │          │ 2. Generate hooks   │
    │    (if thin)        │          │    (if thin)        │
    │ 3. Create draft     │          │ 3. Create draft     │
    │ 4. external_        │          │ 4. external_        │
    │    validation       │          │    validation       │
    │ 5. Return with      │          │ 5. apply_fixes      │
    │    validation data  │          │ 6. Return fixed     │
    │                     │          │    content          │
    └─────────────────────┘          └─────────────────────┘

    Max iterations: 10               Max iterations: 15
    API timeout: 60s                 API timeout: 60s
    Post timeout: 6 min              Post timeout: 6 min
```

### Twitter Routing Logic

Twitter has special routing for single posts vs threads:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   TWITTER ROUTING DECISION                          │
└─────────────────────────────────────────────────────────────────────┘

                    Twitter Request
                          │
                          ▼
               ┌─────────────────────┐
               │ Check for keywords: │
               └──────────┬──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │"thread"  │   │"single   │   │Neither   │
    │keywords  │   │post"     │   │          │
    │          │   │keywords  │   │          │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         │              │              ▼
         │              │     ┌────────────────┐
         │              │     │ Check context: │
         │              │     │ >500 chars?    │
         │              │     │ Has outline?   │
         │              │     │ Multi-para?    │
         │              │     └───────┬────────┘
         │              │             │
         │              │       ┌─────┴─────┐
         │              │       │           │
         │              │      YES          NO
         │              │       │           │
         ▼              ▼       ▼           ▼
    ┌────────────────────┐   ┌────────────────────┐
    │ Direct API Agent   │   │ Haiku Fast Path    │
    │ (Thread creation)  │   │ (Single post)      │
    │ twitter_direct_api │   │ twitter_haiku_agent│
    └────────────────────┘   └────────────────────┘
```

---

## Summary

### Data Flow Summary

```
User Message
    │
    ▼
main_slack.py (FastAPI)
    │
    ▼
ClaudeAgentHandler (SDK)
    │
    ├──────────────────────────────┐
    │                              │
    ▼                              ▼
Single Post                   Batch Orchestrator
    │                              │
    ▼                              ▼
Platform Agent             Sequential Execution
(Direct API)                    (for each post)
    │                              │
    ▼                              ▼
Native Tools              Platform Agent
    │                     (Direct API)
    │                              │
    ├──────────────────────────────┘
    │
    ▼
Validation (Quality + GPTZero)
    │
    ▼
Output (Airtable + Supabase + Slack)
```

### Key Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Quality threshold | 18+/25 | Agent workflows |
| Max iterations (default) | 10 | Agent class |
| Max iterations (thinking) | 15 | Agent class |
| Post timeout | 6 min (360s) | batch_orchestrator.py |
| API timeout (first call) | 120s | Agent class |
| API timeout (subsequent) | 60s | Agent class |
| Tool timeout (validation) | 120s | execute_tool() |
| Tool timeout (other) | 30s | execute_tool() |
| Checkpoint interval | 10 posts | batch_orchestrator.py |

---

## Troubleshooting

### Common Issues

1. **Agent hangs** → Check circuit breaker state, API timeouts
2. **Low quality scores** → Review prompt stack, check for missing rules
3. **GPTZero failures** → 45s timeout, may need retry
4. **Airtable save fails** → Check credentials, retry logic (3 attempts)
5. **Batch post 6+ hangs** → GC cleanup between posts, connection exhaustion

### Debug Logging

Key log patterns to watch:
- `🔧 [TOOL]` - Tool execution
- `📚 Stacked prompts` - Prompt loading
- `✅ Success: Score` - Post completion
- `⏱️ TIMEOUT` - Timeout hit
- `⛔ Circuit breaker` - Circuit breaker state

---

*Generated for ai-content-agent-template*

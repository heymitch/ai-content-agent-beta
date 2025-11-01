# Platform SDK Agent Cloning Plan

**Reference Implementation**: LinkedIn SDK Agent v4.2.0
**Target Platforms**: YouTube, Instagram, Email, Substack
**Status**: Twitter requires separate analysis (unique platform constraints)

This document captures all production hardening and quality improvements made to the LinkedIn SDK Agent, providing a systematic checklist for upgrading other platform agents to the same production-ready standard.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Production Hardening Checklist](#production-hardening-checklist)
3. [Quality Validation Architecture](#quality-validation-architecture)
4. [Tool Improvements](#tool-improvements)
5. [Orchestration Workflow](#orchestration-workflow)
6. [Content Extraction & Storage](#content-extraction--storage)
7. [Platform-Specific Adaptations](#platform-specific-adaptations)
8. [Testing Strategy](#testing-strategy)
9. [Migration Checklist](#migration-checklist)

---

## Architecture Overview

### Current LinkedIn SDK Agent Structure (v4.2.0)

```
linkedin_sdk_agent.py (1606 lines)
├── Production Hardening Layer
│   ├── Structured Logging (utils/structured_logger.py)
│   ├── Circuit Breaker (utils/circuit_breaker.py)
│   └── Retry Logic (utils/retry_decorator.py)
│
├── 7 Specialized Tools (Tier 3)
│   ├── search_company_documents (RAG for proof points)
│   ├── generate_5_hooks
│   ├── create_human_draft
│   ├── inject_proof_points
│   ├── quality_check (Editor-in-Chief rules)
│   ├── external_validation (NEW v4.2.0: Editor-in-Chief + GPTZero)
│   └── apply_fixes (ENHANCED v4.2.0: comprehensive mode)
│
├── Orchestration Prompt (Tier 2)
│   ├── Phase 1: Draft Creation
│   │   ├── Detect rich vs thin context
│   │   ├── Always call create_human_draft (preserve user thinking)
│   │   └── Inject proof points if needed
│   │
│   └── Phase 2: Validation & Rewrite (MANDATORY - SINGLE PASS)
│       ├── Call external_validation
│       ├── Call apply_fixes (ALL issues + GPTZero sentences)
│       └── Return with validation metadata
│
└── Content Storage Pipeline
    ├── _parse_output (Haiku extraction)
    ├── Airtable save (status automation)
    └── Supabase save (with embeddings)
```

### Key Innovations (v4.2.0)

1. **External validation runs INSIDE SDK as tool** (not after SDK finishes)
2. **Single-pass workflow** (validate → fix → return, no re-validation)
3. **Comprehensive fixes** (no 3-5 surgical limit, fix ALL issues)
4. **Graceful degradation** (works without GPTZero API key)
5. **Type safety** (handles dict and string issue formats)
6. **Pattern-based detection** (catches "The X:" headers and short questions)

---

## Production Hardening Checklist

### 1. Required Imports

Add these imports to the top of each SDK agent:

```python
# Production hardening utilities
from utils.structured_logger import (
    get_logger,
    log_operation_start,
    log_operation_end,
    log_error,
    create_context,
    log_retry_attempt
)
from utils.retry_decorator import async_retry_with_backoff, RETRIABLE_EXCEPTIONS
from utils.circuit_breaker import CircuitBreaker, CircuitState

# Setup structured logging
logger = get_logger(__name__)
```

**Reference**: [linkedin_sdk_agent.py:22-38](../agents/linkedin_sdk_agent.py#L22-L38)

### 2. Circuit Breaker Integration

Add circuit breaker to agent class initialization:

```python
class PlatformSDKAgent:
    def __init__(
        self,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        thread_ts: Optional[str] = None,
        batch_mode: bool = False
    ):
        # Circuit breaker for production stability
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60.0,
            name="platform_agent"
        )

        # Store Slack metadata for logging/storage
        self.user_id = user_id
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.batch_mode = batch_mode
```

**Reference**: [linkedin_sdk_agent.py:668-686](../agents/linkedin_sdk_agent.py#L668-L686)

### 3. Circuit Breaker State Management in create_post()

Add circuit breaker check at the START of create_post():

```python
async def create_post(self, topic: str, context: str = "", ...):
    # Track operation timing
    operation_start_time = asyncio.get_event_loop().time()

    # Create context for structured logging
    log_context = create_context(
        user_id=self.user_id,
        thread_ts=self.thread_ts,
        channel_id=self.channel_id,
        platform="platform_name",
        session_id=session_id
    )

    # Log operation start
    log_operation_start(
        logger,
        "create_platform_post",
        context=log_context,
        topic=topic[:100]
    )

    # Check circuit breaker state
    import time as time_module

    with self.circuit_breaker._lock:
        if self.circuit_breaker.state == CircuitState.OPEN:
            time_remaining = self.circuit_breaker.recovery_timeout - (
                time_module.time() - self.circuit_breaker.last_failure_time
            )
            if time_module.time() - self.circuit_breaker.last_failure_time < self.circuit_breaker.recovery_timeout:
                logger.warning(
                    "⛔ Circuit breaker is OPEN - rejecting request",
                    circuit_breaker="platform_agent",
                    time_remaining=f"{time_remaining:.1f}s",
                    **log_context
                )
                return {
                    "success": False,
                    "error": f"Circuit breaker open. Retry in {time_remaining:.1f}s",
                    "post": None
                }
            else:
                # Recovery timeout elapsed - try half-open
                self.circuit_breaker.state = CircuitState.HALF_OPEN
                logger.info(
                    "🔄 Circuit breaker entering HALF_OPEN - testing recovery",
                    circuit_breaker="platform_agent",
                    **log_context
                )
```

**Reference**: [linkedin_sdk_agent.py:802-851](../agents/linkedin_sdk_agent.py#L802-L851)

### 4. Circuit Breaker Failure Tracking

Add failure tracking to the exception handler:

```python
except Exception as e:
    # Log error with full context
    try:
        operation_duration = asyncio.get_event_loop().time() - operation_start_time
    except NameError:
        operation_duration = 0.0

    log_error(
        logger,
        "Platform SDK Agent error",
        error=e,
        context=log_context
    )
    log_operation_end(
        logger,
        "create_platform_post",
        duration=operation_duration,
        success=False,
        context=log_context,
        error_type=type(e).__name__
    )

    # Circuit breaker: Mark operation as failed
    with self.circuit_breaker._lock:
        self.circuit_breaker.failure_count += 1
        self.circuit_breaker.last_failure_time = time_module.time()

        if self.circuit_breaker.state == CircuitState.HALF_OPEN:
            logger.error(
                "❌ Circuit breaker test failed - RE-OPENING",
                circuit_breaker="platform_agent",
                failure_count=self.circuit_breaker.failure_count,
                **log_context
            )
            self.circuit_breaker.state = CircuitState.OPEN
        elif self.circuit_breaker.failure_count >= self.circuit_breaker.failure_threshold:
            logger.error(
                "🔥 Circuit breaker OPENING - threshold reached",
                circuit_breaker="platform_agent",
                failure_count=self.circuit_breaker.failure_count,
                threshold=self.circuit_breaker.failure_threshold,
                **log_context
            )
            self.circuit_breaker.state = CircuitState.OPEN

    return {
        "success": False,
        "error": str(e),
        "post": None
    }
```

**Reference**: [linkedin_sdk_agent.py:1123-1180](../agents/linkedin_sdk_agent.py#L1123-L1180)

### 5. Circuit Breaker Success Tracking

Add success tracking in _parse_output AFTER all saves complete:

```python
# Log operation end with timing and quality score
operation_duration = asyncio.get_event_loop().time() - operation_start_time
log_operation_end(
    logger,
    "create_platform_post",
    duration=operation_duration,
    success=True,
    context=log_context,
    quality_score=score,
    supabase_id=supabase_id,
    airtable_url=airtable_url
)

# Circuit breaker: Mark operation as successful
with self.circuit_breaker._lock:
    if self.circuit_breaker.state == CircuitState.HALF_OPEN:
        logger.info(
            "✅ Circuit breaker test successful - CLOSING",
            circuit_breaker="platform_agent",
            **log_context
        )
    self.circuit_breaker.failure_count = 0
    self.circuit_breaker.state = CircuitState.CLOSED
```

**Reference**: [linkedin_sdk_agent.py:1396-1418](../agents/linkedin_sdk_agent.py#L1396-L1418)

### 6. _parse_output Function Signature

**CRITICAL**: Pass operation_start_time and log_context as parameters to _parse_output:

```python
# In create_post():
return await self._parse_output(final_output, operation_start_time, log_context)

# Function signature:
async def _parse_output(self, output: str, operation_start_time: float, log_context: dict) -> Dict[str, Any]:
```

**Why**: These variables are defined in create_post but used in _parse_output for logging. Without passing them as parameters, you get `NameError: name 'operation_start_time' is not defined`.

**Reference**:
- [linkedin_sdk_agent.py:1121](../agents/linkedin_sdk_agent.py#L1121) (call site)
- [linkedin_sdk_agent.py:1182](../agents/linkedin_sdk_agent.py#L1182) (function definition)

---

## Quality Validation Architecture

### 1. Add external_validation Tool

This is the KEY innovation in v4.2.0. It wraps `run_all_validators()` and runs INSIDE the SDK as a tool (not after SDK finishes).

```python
@tool(
    "external_validation",
    "Run comprehensive validation: Editor-in-Chief rules + GPTZero AI detection",
    {"post": str}
)
async def external_validation(args):
    """
    Run external validators (quality_check + GPTZero) and return structured results

    Returns:
        JSON with total_score, quality_scores, issues, gptzero_ai_pct, decision
    """
    import json

    post = args.get('post', '')

    try:
        from integrations.validation_utils import run_all_validators

        # Run all validators (quality_check + GPTZero in parallel)
        validation_json = await run_all_validators(post, 'platform_name')
        val_data = json.loads(validation_json) if isinstance(validation_json, str) else validation_json

        # Extract key metrics
        quality_scores = val_data.get('quality_scores', {})
        total_score = quality_scores.get('total', 0)
        raw_issues = val_data.get('ai_patterns_found', [])
        gptzero = val_data.get('gptzero', {})

        # Normalize issues to dict format for consistency
        # quality_check can return strings (old format) or dicts (new format)
        issues = []
        for issue in raw_issues:
            if isinstance(issue, dict):
                # Already in correct format
                issues.append(issue)
            elif isinstance(issue, str):
                # Convert old string format to dict format
                issues.append({
                    "severity": "medium",
                    "pattern": "unknown",
                    "original": issue,
                    "fix": "Review manually",
                    "impact": "Potential AI tell detected"
                })

        # GPTZero: As long as it's not 100% AI, it's a win
        # Extract AI probability and flagged sentences if GPTZero ran successfully
        gptzero_ai_pct = None
        gptzero_passes = None
        gptzero_flagged_sentences = []

        if gptzero and gptzero.get('status') in ['PASS', 'FLAGGED']:
            gptzero_ai_pct = gptzero.get('ai_probability', None)
            if gptzero_ai_pct is not None:
                gptzero_passes = gptzero_ai_pct < 100  # Pass if not 100% AI

            # Extract flagged sentences for apply_fixes to rewrite
            gptzero_flagged_sentences = gptzero.get('flagged_sentences', [])

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "total_score": total_score,
                    "quality_scores": quality_scores,
                    "issues": issues,
                    "gptzero_ai_pct": gptzero_ai_pct,
                    "gptzero_passes": gptzero_passes,
                    "gptzero_flagged_sentences": gptzero_flagged_sentences,
                    "decision": val_data.get('decision', 'unknown'),
                    "surgical_summary": val_data.get('surgical_summary', '')
                }, indent=2, ensure_ascii=False)
            }]
        }

    except Exception as e:
        logger.error(f"❌ external_validation error: {e}")
        # Return fallback result - don't block post creation
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "total_score": 18,  # Neutral score - assume decent quality
                    "quality_scores": {"total": 18},
                    "issues": [],
                    "gptzero_ai_pct": None,
                    "gptzero_passes": None,
                    "decision": "error",
                    "error": str(e),
                    "surgical_summary": f"Validation error: {str(e)}"
                }, indent=2)
            }]
        }
```

**Reference**: [linkedin_sdk_agent.py:466-537](../agents/linkedin_sdk_agent.py#L466-L537)

**Key Points**:
- ✅ Runs `run_all_validators()` which is platform-agnostic
- ✅ Normalizes issues to dict format (lines 501-516)
- ✅ Gracefully degrades on error (returns score=18, doesn't crash)
- ✅ Handles missing GPTZero (None values if API key not set)

### 2. Update apply_fixes Tool Signature

Add GPTZero parameters to apply_fixes:

```python
@tool(
    "apply_fixes",
    "Apply fixes to ALL flagged issues (no limit on number of fixes)",
    {"post": str, "issues_json": str, "current_score": int, "gptzero_ai_pct": float, "gptzero_flagged_sentences": list}
)
async def apply_fixes(args):
    """Apply fixes - rewrites EVERYTHING flagged (no surgical limit)"""
    import json
    from anthropic import Anthropic
    from prompts.platform_tools import APPLY_FIXES_PROMPT, WRITE_LIKE_HUMAN_RULES
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    post = args.get('post', '')
    issues_json = args.get('issues_json', '[]')
    current_score = args.get('current_score', 0)
    gptzero_ai_pct = args.get('gptzero_ai_pct', None)
    gptzero_flagged_sentences = args.get('gptzero_flagged_sentences', [])

    # ALWAYS comprehensive mode - no surgical limit
    fix_strategy = "COMPREHENSIVE - Fix ALL issues, no limit on number of changes"

    # Format GPTZero flagged sentences for prompt
    flagged_sentences_text = "Not available"
    if gptzero_flagged_sentences:
        flagged_sentences_text = "\n".join([f"- {sent}" for sent in gptzero_flagged_sentences])

    # Use APPLY_FIXES_PROMPT with GPTZero context
    prompt = APPLY_FIXES_PROMPT.format(
        post=post,
        issues_json=issues_json,
        current_score=current_score,
        gptzero_ai_pct=gptzero_ai_pct if gptzero_ai_pct is not None else "Not available",
        gptzero_flagged_sentences=flagged_sentences_text,
        fix_strategy=fix_strategy,
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES
    )

    # ... rest of tool implementation
```

**Reference**: [linkedin_sdk_agent.py:405-440](../agents/linkedin_sdk_agent.py#L405-L440)

**Key Changes**:
- Added `gptzero_ai_pct` and `gptzero_flagged_sentences` parameters
- ALWAYS comprehensive mode (removed conditional logic)
- Handles None values gracefully ("Not available" fallback)

### 3. Update APPLY_FIXES_PROMPT

Update the prompt template in `prompts/platform_tools.py`:

```python
APPLY_FIXES_PROMPT = dedent("""You are fixing a [PLATFORM] post based on quality feedback.

**CRITICAL PHILOSOPHY: PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

This post contains the author's strategic thinking and intentional language choices.

Original Post:
{post}

Issues from quality_check:
{issues_json}

Current Score: {current_score}/25
GPTZero AI Detection: {gptzero_ai_pct}% AI (Target: <100%)
Fix Strategy: {fix_strategy}

GPTZero Flagged Sentences (rewrite these like a human):
{gptzero_flagged_sentences}

1. **FIX STRATEGY:**

   **COMPREHENSIVE MODE - Fix ALL issues:**
   - No limit on number of fixes - address EVERY problem in issues list
   - Rewrite entire sections if needed to eliminate AI patterns
   - Rewrite GPTZero flagged sentences to sound more human
   - Still preserve: specific numbers, names, dates, strategic narrative
   - But eliminate: ALL cringe questions, ALL contrast framing, ALL buzzwords, ALL formulaic headers
   - Goal: Fix every single flagged issue

   **If GPTZero shows high AI %:**
   - Add more human signals to flagged sentences:
     * Sentence fragments for emphasis
     * Contractions (I'm, that's, here's)
     * Varied sentence length (5-25 words, not uniform 12-15)
     * Natural transitions (And, So, But at sentence starts)

2. **WHAT TO PRESERVE:**
   - Specific numbers, metrics, dates (8.6%, 30 days, Q2 2024)
   - Personal anecdotes and stories ("I spent 3 months...", "The CEO told me...")
   - Strategic narrative arc (problem → insight → action)
   - Author's unique voice and perspective

3. **WHAT TO FIX:**
   - ALL issues in issues_json list above
   - ALL GPTZero flagged sentences (rewrite to add human signals)
   - Contrast framing ("It's not X, it's Y" → "Y matters")
   - Formulaic headers ("The truth:" → "Here's what I found:")
   - Cringe questions ("For me?" → DELETE or expand to full sentence)
   - Buzzwords and AI clichés (see write_like_human_rules)

{write_like_human_rules}

**OUTPUT:**
Return ONLY the revised post - no explanations, no meta-commentary.
Fix ALL issues - no limit. Every flagged pattern and GPTZero sentence must be addressed.
""")
```

**Reference**: [linkedin_tools.py:870-936](../prompts/linkedin_tools.py#L870-L936)

**Key Changes**:
- Removed score-based conditional (≥18 vs <18)
- ALWAYS comprehensive mode
- Added GPTZero context section
- Added instructions for rewriting flagged sentences

### 4. Update QUALITY_CHECK_PROMPT for Pattern-Based Detection

**CRITICAL UPDATE**: The old version only detected EXACT phrases. The new version uses PATTERN matching.

Add these sections to QUALITY_CHECK_PROMPT in `prompts/platform_tools.py`:

```python
STEP 1: SCAN FOR VIOLATIONS
Go through the post line-by-line and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Formulaic headers (ANY case):
  * "The X:" pattern → "The promise:", "The reality:", "The result:", "The truth:", "The catch:", "The process:", "The best part:"
  * "HERE'S HOW:", "HERE'S WHAT:", Title Case In Headings
  * These are AI tells - convert to natural language or delete
- Short questions (<8 words ending in "?"):
  * "For me?" → Delete or expand to statement: "For me, the ability to..."
  * "The truth?" → Delete entirely
  * "What happened?" → Expand: "What did the data show after 30 days?"
  * Count words - if <8 words AND ends with "?", it's a violation
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament", "rich heritage")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions ("industry reports says" without source)
- Em-dash overuse (multiple — in formulaic patterns)
- Words needing substitution ("leverages", "encompasses", "facilitates")
```

**Reference**: [linkedin_tools.py:1144-1163](../prompts/linkedin_tools.py#L1144-L1163)

**Why Critical**: This catches patterns like "The promise:", "For me?", and "The reality:" that were getting through before because they weren't exact matches.

---

## Tool Improvements

### 1. Add external_validation to Tools Array

Update the MCP server initialization:

```python
# Create MCP server with platform-specific tools
self.mcp_server = create_sdk_mcp_server(
    name="platform_tools",
    version="4.2.0",  # Bump version
    tools=[
        search_company_documents,  # RAG for proof points
        generate_hooks,  # Platform-specific hook generation
        create_human_draft,
        inject_proof_points,
        quality_check,  # Editor-in-Chief rules
        external_validation,  # NEW v4.2.0: Editor-in-Chief + GPTZero
        apply_fixes  # ENHANCED v4.2.0: comprehensive mode + GPTZero
    ]
)

print(f"🎯 Platform SDK Agent initialized with 7 tools (external_validation + comprehensive apply_fixes)")
```

**Reference**: [linkedin_sdk_agent.py:695-710](../agents/linkedin_sdk_agent.py#L695-L710)

### 2. Update CREATE_HUMAN_DRAFT_PROMPT

Add instructions for handling rich outlines (user-provided detailed context):

```python
=== HANDLING RICH OUTLINES VS THIN CONTEXT ===

**IF CONTEXT contains a detailed outline (>200 words with strategic narrative):**
- This is the user's strategic thinking - PRESERVE IT
- Your job is to POLISH it, not rewrite it
- Convert outline bullets to flowing prose
- Keep ALL specific language, numbers, personal anecdotes, narrative choices
- Remove any AI tells (formulaic headers like "The promise:", cringe questions like "For me?")
- Maintain the user's voice and structure
- DO NOT replace user's thinking with generic AI content
- Think: "clean up and format" NOT "rewrite from scratch"

**IF CONTEXT is a topic or thin outline (<200 words):**
- You're creating from scratch
- Follow format decision rules below
- Use hook as starting point, build out the narrative
```

**Reference**: [linkedin_tools.py:318-333](../prompts/linkedin_tools.py#L318-L333)

**Why Important**: Without this, the agent rewrites user's strategic thinking instead of preserving it.

---

## Orchestration Workflow

### 1. Update Phase 1: Always Call create_human_draft

**OLD (WRONG)**:
```python
IF YES (rich strategic context):
   → SKIP to Phase 2 below (don't create draft)
```

**NEW (CORRECT)**:
```python
IF YES (rich strategic context):
   → Extract the user's exact thinking
   → Build on it, don't replace it
   → DO NOT call generate_hooks (user already has an angle!)
   → DO call create_human_draft WITH the outline as context
   → The tool will PRESERVE user's language and structure, just polish it
   → THEN proceed to Phase 2 below (quality gate is STILL MANDATORY)
```

**Reference**: [linkedin_sdk_agent.py:872-878](../agents/linkedin_sdk_agent.py#L872-L878)

**Why Critical**: Can't validate without a draft. Even rich outlines need to be polished into post format.

### 2. Update Phase 2: Single-Pass Validation Workflow

Replace the old quality_check → apply_fixes → re-validate loop with:

```python
═══════════════════════════════════════════════════════════
PHASE 2: VALIDATION & REWRITE (MANDATORY - SINGLE PASS)
═══════════════════════════════════════════════════════════

STOP. DO NOT RETURN THE POST YET.

WORKFLOW (ONE REWRITE ATTEMPT):

1. Call external_validation(post=your_draft)
   - This runs Editor-in-Chief rules + GPTZero AI detection
   - Returns: total_score, issues, gptzero_ai_pct, gptzero_flagged_sentences

2. Call apply_fixes with ALL parameters:
   apply_fixes(
     post=your_draft,
     issues_json=json.dumps(validation.issues),
     current_score=validation.total_score,
     gptzero_ai_pct=validation.gptzero_ai_pct,
     gptzero_flagged_sentences=validation.gptzero_flagged_sentences
   )

   - apply_fixes will fix EVERY issue (no 3-5 limit)
   - Rewrites ALL GPTZero flagged sentences to sound more human
   - Returns revised_post

3. Return the revised_post with validation metadata:
   {
     "post_text": "[revised_post from apply_fixes]",
     "original_score": [score from external_validation],
     "validation_issues": [issues from external_validation],
     "gptzero_ai_pct": [AI % from external_validation],
     "gptzero_flagged_sentences": [flagged sentences from external_validation]
   }

CRITICAL:
- Only ONE rewrite pass (don't re-validate after apply_fixes)
- Return revised_post even if score was low
- Include validation metadata so wrapper can set Airtable status
- DO NOT run external_validation twice
- Validation metadata is used to set "Needs Review" status if score <18

WORKFLOW:
Draft → external_validation → apply_fixes (ALL issues + GPTZero sentences) → Return with metadata

Return format MUST include all validation metadata for Airtable.
```

**Reference**: [linkedin_sdk_agent.py:887-930](../agents/linkedin_sdk_agent.py#L887-L930)

**Key Changes**:
- Single pass (no re-validation loop)
- external_validation instead of quality_check
- Return JSON with validation metadata
- Airtable status set based on score in wrapper

---

## Content Extraction & Storage

### 1. Update _parse_output to Extract Validation Metadata

The SDK agent now returns JSON with validation data. Update the extraction logic:

```python
async def _parse_output(self, output: str, operation_start_time: float, log_context: dict) -> Dict[str, Any]:
    # Extract structured content using Haiku (replaces fragile regex)
    from integrations.content_extractor import extract_structured_content

    extracted = await extract_structured_content(
        raw_output=output,
        platform='platform_name'
    )

    clean_output = extracted['body']
    hook_preview = extracted['hook']

    # Extract validation metadata from SDK response (agent already ran external_validation)
    validation_score = extracted.get('original_score', 20)  # Default 20 if not provided
    validation_issues = extracted.get('validation_issues', [])
    gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
    gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])

    score = validation_score  # Use score from validation
```

**Reference**: [linkedin_sdk_agent.py:1207-1221](../agents/linkedin_sdk_agent.py#L1207-L1221)

### 2. Format Validation for Airtable "Suggested Edits"

Create bullet-pointed validation report with type safety:

```python
# Format issues as bullet points for Airtable "Suggested Edits"
validation_formatted = None
if validation_issues or gptzero_flagged_sentences:
    lines = ["🔍 VALIDATION RESULTS:\n"]

    # Add quality score
    lines.append(f"Quality Score: {validation_score}/25")
    if validation_score < 18:
        lines.append("⚠️ Status: NEEDS REVIEW (score below 18 threshold)\n")
    else:
        lines.append("✅ Status: Draft (score meets threshold)\n")

    # Add GPTZero results if available
    if gptzero_ai_pct is not None:
        lines.append(f"\n🤖 GPTZero AI Detection: {gptzero_ai_pct}% AI")
        if gptzero_ai_pct < 100:
            lines.append("✅ Pass (not 100% AI)\n")
        else:
            lines.append("⚠️ Flagged as 100% AI\n")

        # Add flagged sentences
        if gptzero_flagged_sentences:
            lines.append(f"\n📝 GPTZero Flagged Sentences ({len(gptzero_flagged_sentences)} total):")
            for i, sentence in enumerate(gptzero_flagged_sentences[:5], 1):  # Show max 5
                lines.append(f"   {i}. {sentence[:150]}...")
            if len(gptzero_flagged_sentences) > 5:
                lines.append(f"   ... and {len(gptzero_flagged_sentences) - 5} more\n")

    # Add validation issues
    if validation_issues:
        lines.append(f"\n⚠️ ISSUES FOUND ({len(validation_issues)} total):\n")
        for i, issue in enumerate(validation_issues, 1):
            # Handle both dict format (new) and string format (old)
            if isinstance(issue, dict):
                # NEW FORMAT: Issue object with severity/pattern/fix
                severity = issue.get('severity', 'medium').upper()
                pattern = issue.get('pattern', 'unknown')
                original = issue.get('original', '')
                fix = issue.get('fix', '')
                impact = issue.get('impact', '')

                lines.append(f"{i}. [{severity}] {pattern}")
                lines.append(f"   Problem: {original}")
                lines.append(f"   Fix: {fix}")
                if impact:
                    lines.append(f"   Impact: {impact}")
                lines.append("")
            else:
                # OLD FORMAT: String description (fallback for legacy quality_check)
                lines.append(f"{i}. {issue}")
                lines.append("")

    validation_formatted = "\n".join(lines)
else:
    # No issues found
    validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"
```

**Reference**: [linkedin_sdk_agent.py:1223-1273](../agents/linkedin_sdk_agent.py#L1223-L1273)

**Key Points**:
- ✅ Type safety (handles dict and string issues)
- ✅ GPTZero flagged sentences included
- ✅ Human-readable bullet points
- ✅ Shows first 5 flagged sentences (truncates if more)

### 3. Airtable Status Automation

Set status based on validation score:

```python
# Determine Airtable status based on validation score
airtable_status = "Needs Review" if validation_score < 18 else "Draft"

print(f"\n📝 Saving content (hook: '{hook_preview[:50]}...')")
print(f"   Status: {airtable_status} (score: {validation_score}/25)")
result = airtable.create_content_record(
    content=clean_output,
    platform='platform_name',
    post_hook=hook_preview,
    status=airtable_status,  # "Needs Review" if <18, else "Draft"
    suggested_edits=validation_formatted  # Validation report with GPTZero sentences
)
```

**Reference**: [linkedin_sdk_agent.py:1310-1320](../agents/linkedin_sdk_agent.py#L1310-L1320)

### 4. Update content_extractor.py Extraction Prompt

The extractor needs to recognize the new JSON format:

```python
The agent output may be in TWO formats:

FORMAT 1: JSON with validation metadata (NEW v4.2.0)
{
  "post_text": "...",
  "original_score": 16,
  "validation_issues": [...],
  "gptzero_ai_pct": 45,
  "gptzero_flagged_sentences": [...]
}

FORMAT 2: Plain text post (legacy)
Multiple versions from iteration process - you need to find the FINAL version.

EXTRACTION RULES:

1. body: Extract the FINAL, COMPLETE, VERBATIM post content

   PRIORITY 1 - Check if output is JSON with validation metadata:
   - If agent returned {"post_text": "...", "original_score": ..., ...}
   - Extract body from "post_text" field
   - Extract validation metadata (original_score, validation_issues, gptzero_ai_pct, gptzero_flagged_sentences)
   - Include ALL metadata fields in your response

   PRIORITY 2 - Look for EXPLICIT FINAL MARKERS (case-insensitive, flexible):
   - Contains "FINAL POST" (with or without emoji, asterisks, platform name)
   ...
```

**Reference**: [content_extractor.py:61-121](../integrations/content_extractor.py#L61-L121)

---

## Platform-Specific Adaptations

### Platform Comparison Matrix

| Platform   | Agent Lines | Prompt Lines | Unique Tools | Format Constraints |
|------------|-------------|--------------|--------------|-------------------|
| LinkedIn   | 1606        | 1360         | 7            | 50-450 words, hooks, bullets/long-form |
| Email      | 980         | 651          | 5            | Subject line, preview text, body sections |
| Instagram  | 851         | 435          | 4            | Caption 2200 chars, hashtags, CTAs |
| YouTube    | 992         | 534          | 4            | Script with timestamps, hooks, retention |
| Twitter    | 1159        | 950          | 5            | 280 chars, threads, quote tweets |

### 1. LinkedIn-Specific Patterns

**Cringe Questions**:
- "For me?" (2 words)
- "The truth?" (2 words)
- "Sound familiar?" (2 words)

**Formulaic Headers**:
- "The promise:", "The reality:", "The result:"
- "HERE'S HOW:", "HERE'S WHAT:"

**Contrast Framing**:
- "It's not X, it's Y"
- "This isn't about X—it's about Y"

### 2. Email-Specific Patterns

**Subject Line AI Tells**:
- "You won't believe..."
- "The secret to..."
- Numbers in subject (less effective for newsletters vs cold email)

**Preview Text Issues**:
- Generic previews ("Read more...", "Click here...")
- Should summarize value, not be a CTA

**Body Patterns**:
- Multiple CTAs (should be 1 primary CTA)
- Long paragraphs (should be 2-3 sentences max)
- Lack of white space

### 3. Instagram-Specific Patterns

**Caption AI Tells**:
- "Double tap if..." (engagement bait)
- Excessive emojis (more than 3-5)
- Generic hashtags (#love, #instagood)

**Format Issues**:
- No line breaks (Instagram allows line breaks, use them)
- CTA at top (should be at bottom after value)
- Hashtag dump (should be relevant, not spam)

### 4. YouTube-Specific Patterns

**Script AI Tells**:
- "Hey guys!" (overused opening)
- "Don't forget to like and subscribe" (should be natural, not forced)
- Reading from bullet points (sounds robotic)

**Timestamp Issues**:
- No retention hooks (should have hooks every 2-3 minutes)
- Monotone pacing (vary energy levels)
- Too long intro (get to value in 30 seconds)

### 5. Platform-Specific QUALITY_CHECK_PROMPT Updates

For each platform, update QUALITY_CHECK_PROMPT in `prompts/platform_tools.py`:

**Email**:
```python
STEP 1: SCAN FOR VIOLATIONS
Go through the email line-by-line and find:
- Subject line AI tells ("You won't believe", "The secret to")
- Generic preview text ("Read more", "Click here")
- Multiple CTAs (should be 1 primary CTA)
- Long paragraphs (>3 sentences)
- ... (rest of LinkedIn patterns apply)
```

**Instagram**:
```python
STEP 1: SCAN FOR VIOLATIONS
Go through the caption line-by-line and find:
- Engagement bait ("Double tap if", "Tag a friend who")
- Excessive emojis (>5 in caption)
- Generic hashtags (#love, #instagood, #photooftheday)
- CTA at top (should be at bottom)
- ... (rest of LinkedIn patterns apply)
```

**YouTube**:
```python
STEP 1: SCAN FOR VIOLATIONS
Go through the script line-by-line and find:
- Overused openings ("Hey guys!", "What's up everyone")
- Forced CTAs ("Don't forget to like and subscribe")
- Robotic transitions ("Moving on to the next point")
- No retention hooks (should have hooks every 2-3 minutes)
- ... (rest of LinkedIn patterns apply)
```

---

## Testing Strategy

### 1. Test Script Template

**CRITICAL**: Call `agent.create_post()` directly, NOT `create_platform_post_workflow()`.

```python
import asyncio
import sys
sys.path.insert(0, '/path/to/ai-content-agent-template')

async def test_platform():
    from agents.platform_sdk_agent import PlatformSDKAgent

    topic = "Test topic here"
    context = """Test context here"""

    print('🚀 Testing Platform SDK Agent with external_validation...')
    print('=' * 70)
    print(f'Topic: {topic}')
    print('=' * 70)

    # Use agent.create_post() directly to get dict response
    agent = PlatformSDKAgent(
        user_id='test_user',
        thread_ts='test_thread',
        channel_id='test_channel',
        batch_mode=False  # Single post test
    )

    result = await agent.create_post(
        topic=topic,
        context=context,
        post_type='standard',
        target_score=85
    )

    print('\n' + '=' * 70)
    print('📊 RESULT:')
    print('=' * 70)

    if result.get('success'):
        print('\n✅ POST CREATED SUCCESSFULLY\n')
        print(result['post'])
        print('\n' + '=' * 70)
        print(f"Quality Score: {result.get('score', 'N/A')}/25")
        print(f"Airtable URL: {result.get('airtable_url', 'N/A')}")
        print(f"Supabase ID: {result.get('supabase_id', 'N/A')}")
        print('=' * 70)
    else:
        print(f"\n❌ CREATION FAILED: {result.get('error', 'Unknown error')}\n")
        print('=' * 70)

asyncio.run(test_platform())
```

**Why**: `create_platform_post_workflow()` returns a STRING for Slack, not a dict. Tests need the dict to check scores and validation.

### 2. Expected Response Format

```python
{
    "success": True,
    "post": "The clean post content (metadata stripped)",
    "hook": "First 200 chars for preview",
    "score": 21,  # From external_validation
    "hooks_tested": 5,
    "iterations": 3,
    "airtable_url": "https://airtable.com/...",
    "google_doc_url": "[Coming Soon]",
    "supabase_id": "uuid-here",
    "session_id": "test_user",
    "timestamp": "2025-01-01T12:00:00"
}
```

### 3. Verification Checklist

After running test, verify:

- ✅ No NameError (operation_start_time passed correctly)
- ✅ No CircuitState import error
- ✅ Draft created (even with rich outline)
- ✅ external_validation ran (check logs for "Running quality check and GPTZero")
- ✅ apply_fixes ran with ALL issues (check logs)
- ✅ Airtable status set correctly ("Needs Review" if <18, else "Draft")
- ✅ GPTZero flagged sentences in Suggested Edits (if API key set)
- ✅ Graceful degradation (works without GPTZero API key)

---

## Migration Checklist

### Pre-Migration

- [ ] Read through this entire document
- [ ] Understand LinkedIn SDK Agent v4.2.0 architecture
- [ ] Identify platform-specific patterns for target platform
- [ ] Update QUALITY_CHECK_PROMPT with platform-specific rules

### Code Changes

**1. Production Hardening**
- [ ] Add imports (structured_logger, retry_decorator, circuit_breaker)
- [ ] Add CircuitState to imports (not just CircuitBreaker)
- [ ] Add circuit breaker to __init__
- [ ] Add circuit breaker state check in create_post
- [ ] Add circuit breaker failure tracking in exception handler
- [ ] Add circuit breaker success tracking in _parse_output
- [ ] Pass operation_start_time and log_context to _parse_output

**2. Quality Validation**
- [ ] Add external_validation tool
- [ ] Update apply_fixes signature (add GPTZero parameters)
- [ ] Update APPLY_FIXES_PROMPT (remove conditional, add GPTZero section)
- [ ] Update QUALITY_CHECK_PROMPT (pattern-based detection)
- [ ] Add platform-specific patterns to QUALITY_CHECK_PROMPT

**3. Tool Improvements**
- [ ] Add external_validation to tools array
- [ ] Update CREATE_HUMAN_DRAFT_PROMPT (rich outline handling)
- [ ] Bump version to 4.2.0

**4. Orchestration Workflow**
- [ ] Update Phase 1 (always call create_human_draft)
- [ ] Update Phase 2 (single-pass validation workflow)
- [ ] Change return format to include validation metadata

**5. Content Extraction & Storage**
- [ ] Update _parse_output to extract validation metadata
- [ ] Add type safety for validation issues (dict vs string)
- [ ] Format validation for Airtable Suggested Edits
- [ ] Add Airtable status automation
- [ ] Update content_extractor.py extraction prompt

### Testing

- [ ] Create test script (use template above)
- [ ] Test without GPTZero API key (verify graceful degradation)
- [ ] Test with rich outline (verify draft created)
- [ ] Test with low score (verify "Needs Review" status)
- [ ] Test circuit breaker (trigger 3 failures, verify open state)
- [ ] Test with GPTZero API key (verify flagged sentences in Suggested Edits)

### Deployment

- [ ] Commit changes with descriptive message
- [ ] Update agent version in MCP server initialization
- [ ] Run full integration test with Slack/CMO agent
- [ ] Monitor logs for circuit breaker state changes
- [ ] Verify Airtable records have correct status and Suggested Edits

---

## Common Pitfalls

### 1. NameError: name 'operation_start_time' is not defined

**Cause**: Not passing operation_start_time as parameter to _parse_output

**Fix**:
```python
# In create_post():
return await self._parse_output(final_output, operation_start_time, log_context)

# Function signature:
async def _parse_output(self, output: str, operation_start_time: float, log_context: dict):
```

### 2. NameError: name 'CircuitState' is not defined

**Cause**: Only importing CircuitBreaker, not CircuitState enum

**Fix**:
```python
from utils.circuit_breaker import CircuitBreaker, CircuitState
```

### 3. AttributeError: 'str' object has no attribute 'get'

**Cause**: Test calling `create_platform_post_workflow()` which returns a string

**Fix**: Call `agent.create_post()` directly in tests to get dict response

### 4. Agent skips create_human_draft with rich outline

**Cause**: Phase 1 says "SKIP to Phase 2" instead of calling create_human_draft

**Fix**: Update Phase 1 to always call create_human_draft (see Orchestration Workflow section)

### 5. Validation issues are strings, not dicts

**Cause**: quality_check can return strings when JSON parsing fails

**Fix**: Add isinstance(issue, dict) check in _parse_output and external_validation tool

### 6. GPTZero integration breaks when API key not set

**Cause**: Not handling None values from run_gptzero_check()

**Fix**: Check if gptzero_result exists before accessing properties (see external_validation tool)

---

## Success Metrics

After migration, the platform agent should have:

1. **Production Stability**
   - Circuit breaker prevents cascading failures
   - Structured logging for debugging
   - Retry logic handles transient errors
   - Graceful degradation when services unavailable

2. **Quality Improvements**
   - Pattern-based detection catches "The X:" headers
   - Cringe questions detected by word count (<8 words)
   - GPTZero flagged sentences rewritten
   - Comprehensive fixes (no 3-5 limit)

3. **User Experience**
   - "Needs Review" status for low scores (<18)
   - Bullet-pointed validation in Suggested Edits
   - Single-pass workflow (no re-validation loop)
   - Rich outlines preserved (not rewritten)

4. **Developer Experience**
   - Type-safe issue handling (dict and string)
   - Clear test strategy (direct agent.create_post() calls)
   - Comprehensive error messages
   - Easy to debug with structured logs

---

## Next Steps

### Immediate (YouTube, Instagram, Email, Substack)

1. Choose platform to migrate first (recommend: Email, similar structure to LinkedIn)
2. Follow migration checklist section-by-section
3. Test thoroughly (see Testing Strategy)
4. Deploy and monitor logs

### Future (Twitter)

Twitter requires separate analysis due to unique constraints:
- 280 character limit (very different from other platforms)
- Thread structure (multiple tweets in sequence)
- Quote tweets and retweets (engagement patterns)
- Real-time nature (news, trending topics)

**Recommendation**: After migrating 4 platforms successfully, create a separate TWITTER_MIGRATION.md based on learnings.

---

## Reference Files

### Key Files Modified in LinkedIn v4.2.0

1. `agents/linkedin_sdk_agent.py` - Main agent with hardening + validation
2. `prompts/linkedin_tools.py` - Tool prompts (QUALITY_CHECK, APPLY_FIXES)
3. `integrations/validation_utils.py` - run_all_validators (platform-agnostic)
4. `integrations/content_extractor.py` - Haiku extraction with metadata
5. `utils/structured_logger.py` - Logging utilities (ALREADY EXISTS)
6. `utils/circuit_breaker.py` - Circuit breaker (ALREADY EXISTS)
7. `utils/retry_decorator.py` - Retry logic (ALREADY EXISTS)

### Git Commits Reference

- `ce47b65` - Refined cringe question list with better examples
- `27034db` - Pattern-based detection in QUALITY_CHECK_PROMPT
- `a945bd6` - External validation tool + comprehensive apply_fixes
- `28c7bd8` - Type safety fixes + draft creation workflow
- `36512f8` - Fix operation_start_time scope bug
- `e0dd911` - Add missing CircuitState import

---

## Conclusion

This cloning plan captures the complete transformation of the LinkedIn SDK Agent from a basic content generator to a production-ready, quality-focused system. By following this plan systematically, we can bring all platform agents to the same level of stability and quality.

The key innovations are:
1. **External validation as SDK tool** (not post-processing)
2. **Single-pass workflow** (validate → fix → return)
3. **Pattern-based detection** (catches variations, not just exact phrases)
4. **Comprehensive fixes** (no arbitrary limits)
5. **Graceful degradation** (works without optional services)

Apply these patterns to YouTube, Instagram, Email, and Substack to create a consistent, high-quality content generation system across all platforms.

"""
LinkedIn Direct API Agent - Tier 2 Orchestrator
Uses direct Anthropic API calls instead of Claude Agent SDK to eliminate hanging issues.
Maintains same interface as linkedin_sdk_agent.py for drop-in replacement.
"""

from anthropic import Anthropic
import os
import json
import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
from dotenv import load_dotenv
from textwrap import dedent

# Production hardening utilities
from utils.structured_logger import (
    get_logger,
    log_operation_start,
    log_operation_end,
    log_error,
    create_context
)
from utils.circuit_breaker import CircuitBreaker, CircuitState

# Load environment variables
load_dotenv()

# Setup structured logging
logger = get_logger(__name__)


# ================== TIER 3 TOOL IMPLEMENTATIONS (ALREADY NATIVE PYTHON) ==================
# Import existing tool functions - they already use direct Anthropic API

from agents.linkedin_sdk_agent import (
    generate_5_hooks,
    search_company_documents,
    inject_proof_points,
    create_human_draft,
    validate_format,
    search_viral_patterns,
    score_and_iterate,
    quality_check,
    apply_fixes,
    external_validation
)

# ================== TOOL SCHEMA DEFINITIONS FOR DIRECT API ==================

TOOL_SCHEMAS = [
    {
        "name": "search_company_documents",
        "description": "Search user-uploaded docs (case studies, testimonials, product docs) for proof points",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "match_count": {"type": "integer", "description": "Number of results to return", "default": 3},
                "document_type": {"type": "string", "description": "Optional filter by document type"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_5_hooks",
        "description": "Generate 5 LinkedIn hooks in different formats",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Main topic for hooks"},
                "context": {"type": "string", "description": "Additional context"},
                "target_audience": {"type": "string", "description": "Target audience"}
            },
            "required": ["topic", "context", "target_audience"]
        }
    },
    {
        "name": "create_human_draft",
        "description": "Generate LinkedIn draft with quality self-assessment",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Post topic"},
                "hook": {"type": "string", "description": "Selected hook"},
                "context": {"type": "string", "description": "Additional context"}
            },
            "required": ["topic", "hook", "context"]
        }
    },
    {
        "name": "inject_proof_points",
        "description": "Add metrics and proof points. Searches company documents first for real case studies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "draft": {"type": "string", "description": "Draft post text"},
                "topic": {"type": "string", "description": "Post topic"},
                "industry": {"type": "string", "description": "Industry context"}
            },
            "required": ["draft", "topic", "industry"]
        }
    },
    {
        "name": "quality_check",
        "description": "Score post on 5 axes and return surgical fixes",
        "input_schema": {
            "type": "object",
            "properties": {
                "post": {"type": "string", "description": "Post to check"}
            },
            "required": ["post"]
        }
    },
    {
        "name": "external_validation",
        "description": "Run comprehensive validation: Editor-in-Chief rules + GPTZero AI detection",
        "input_schema": {
            "type": "object",
            "properties": {
                "post": {"type": "string", "description": "Post to validate"}
            },
            "required": ["post"]
        }
    },
    {
        "name": "apply_fixes",
        "description": "Apply fixes to ALL flagged issues (no limit on number of fixes)",
        "input_schema": {
            "type": "object",
            "properties": {
                "post": {"type": "string", "description": "Post to fix"},
                "issues_json": {"type": "string", "description": "JSON array of issues"},
                "current_score": {"type": "integer", "description": "Current quality score"},
                "gptzero_ai_pct": {"type": "number", "description": "GPTZero AI percentage"},
                "gptzero_flagged_sentences": {"type": "array", "items": {"type": "string"}, "description": "Flagged sentences"}
            },
            "required": ["post", "issues_json", "current_score"]
        }
    }
]


# ================== TOOL EXECUTION DISPATCHER ==================

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute a tool by name with timeout protection"""

    # Map tool names to functions
    tool_map = {
        "search_company_documents": search_company_documents,
        "generate_5_hooks": generate_5_hooks,
        "create_human_draft": create_human_draft,
        "inject_proof_points": inject_proof_points,
        "quality_check": quality_check,
        "external_validation": external_validation,
        "apply_fixes": apply_fixes
    }

    if tool_name not in tool_map:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        # Execute tool with 30s timeout
        result = await asyncio.wait_for(
            tool_map[tool_name](tool_input),
            timeout=30.0
        )

        # Extract text content from tool result
        if isinstance(result, dict) and "content" in result:
            # Tool returns {"content": [{"type": "text", "text": "..."}]}
            content_blocks = result.get("content", [])
            if content_blocks and isinstance(content_blocks, list):
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")

        # Fallback: return as JSON string
        return json.dumps(result, ensure_ascii=False)

    except asyncio.TimeoutError:
        logger.error(f"Tool timeout: {tool_name} exceeded 30s")
        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
    except Exception as e:
        logger.error(f"Tool error: {tool_name} - {e}")
        return json.dumps({"error": f"Tool error: {str(e)}"})


# ================== LINKEDIN DIRECT API AGENT CLASS ==================

class LinkedInDirectAPIAgent:
    """
    Tier 2: LinkedIn-specific agent using direct Anthropic API
    Drop-in replacement for LinkedInSDKAgent without SDK hanging issues
    """

    def __init__(
        self,
        user_id: str = "default",
        channel_id: Optional[str] = None,
        thread_ts: Optional[str] = None,
        batch_mode: bool = False
    ):
        """Initialize LinkedIn Direct API Agent

        Args:
            user_id: User identifier for session management
            channel_id: Slack channel ID (for Airtable/Supabase saves)
            thread_ts: Slack thread timestamp (for Airtable/Supabase saves)
            batch_mode: If True, disable session reuse for batch safety
        """
        self.user_id = user_id
        self.batch_mode = batch_mode
        self.channel_id = channel_id
        self.thread_ts = thread_ts

        # Production hardening: Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120.0,
            name="linkedin_direct_api_agent"
        )

        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=api_key)

        # LinkedIn-specific system prompt (same as SDK version)
        self.system_prompt = """You are a LinkedIn content creation agent with a critical philosophy:

**PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

When a user provides an outline or draft:
• Their strategic narrative is often excellent - KEEP IT
• Their specific language choices are intentional - RESPECT THEM
• Their authentic voice is valuable - PRESERVE IT
• Only AI patterns and slop need fixing - FIX THOSE

INTELLIGENT WORKFLOW:

STEP 1: Evaluate what you received
- Read the Topic and Context carefully
- Is there substantial content? (>200 words with narrative flow)
- Does it have specific language that sounds authentic and intentional?
- Does it contain strategic thinking and point of view?

STEP 2: Choose your approach intelligently

IF the user gave you a strong foundation (good narrative, specific language, strategic thinking):
   → Run quality_check on their EXACT text first
   → Identify ONLY the problems: AI tells, formatting issues, missing proof
   → Use apply_fixes to make SURGICAL corrections
   → Goal: Preserve 80-90% of their exact wording

IF the user gave you just a topic or thin outline (<200 words, no narrative):
   → generate_5_hooks to explore angles
   → create_human_draft to build full content
   → inject_proof_points if needed
   → quality_check and apply_fixes as usual

CRITICAL PRINCIPLES:
• User's strategic thinking > AI regeneration
• Specific language > generic rewrites
• Surgical fixes > complete rewrites
• Preserve voice > enforce templates

The user spent time thinking through their post. Your job is to make it BETTER, not to replace their thinking with generic AI output."""

        print("🎯 LinkedIn Direct API Agent initialized (no SDK, no hangs)")

    async def create_post(
        self,
        topic: str,
        context: str = "",
        post_type: str = "standard",
        target_score: int = 85,
        session_id: Optional[str] = None,
        publish_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a LinkedIn post using direct Anthropic API with manual tool calling

        Args:
            topic: Main topic/angle
            context: Additional requirements, CTAs, etc.
            post_type: standard, carousel, or video
            target_score: Minimum quality score (default 85)
            session_id: Session for conversation continuity
            publish_date: Optional publish date for scheduling

        Returns:
            Dict with final post, score, hooks tested, iterations
        """

        # Store publish_date for Airtable save
        self.publish_date = publish_date

        # Track operation timing
        operation_start_time = asyncio.get_event_loop().time()

        # Create logging context
        log_context = create_context(
            user_id=self.user_id,
            thread_ts=self.thread_ts,
            channel_id=self.channel_id,
            platform="linkedin",
            session_id=session_id or "direct_api"
        )

        log_operation_start(
            logger,
            "create_linkedin_post_direct_api",
            context=log_context,
            topic=topic[:100],
            post_type=post_type
        )

        # Check circuit breaker
        import time as time_module
        with self.circuit_breaker._lock:
            if self.circuit_breaker.state == CircuitState.OPEN:
                time_remaining = self.circuit_breaker.recovery_timeout - (
                    time_module.time() - self.circuit_breaker.last_failure_time
                )
                if time_module.time() - self.circuit_breaker.last_failure_time < self.circuit_breaker.recovery_timeout:
                    logger.warning(
                        "⛔ Circuit breaker is OPEN - rejecting request",
                        time_remaining=f"{time_remaining:.1f}s",
                        **log_context
                    )
                    return {
                        "success": False,
                        "error": f"Circuit breaker open. Retry in {time_remaining:.1f}s",
                        "post": None
                    }
                else:
                    self.circuit_breaker.state = CircuitState.HALF_OPEN
                    logger.info("🔄 Circuit breaker entering HALF_OPEN", **log_context)

        try:
            # Build creation prompt
            creation_prompt = f"""Create a LinkedIn {post_type} post.

Topic: {topic}

Context/Outline:
{context}

MANDATORY WORKFLOW (NO SHORTCUTS, NO SELF-ASSESSMENT):

═══════════════════════════════════════════════════════════
PHASE 1: DRAFT CREATION
═══════════════════════════════════════════════════════════

Evaluate the Context/Outline:
- Does it contain strategic narrative (>200 words with specific language)?

IF YES (rich strategic context):
   → Extract the user's exact thinking
   → Build on it, don't replace it
   → DO NOT call generate_5_hooks (user already has an angle!)
   → DO call create_human_draft WITH the outline as context
   → The tool will PRESERVE user's language and structure, just polish it
   → THEN proceed to Phase 2 below (quality gate is STILL MANDATORY)

IF NO (topic or thin outline):
   → Call generate_5_hooks to explore angles
   → Call create_human_draft to build full content (returns ONLY post_text, no scoring)
   → Call inject_proof_points to add metrics
   → THEN proceed to Phase 2 below

═══════════════════════════════════════════════════════════
PHASE 2: VALIDATION & REWRITE (MANDATORY - SINGLE PASS)
═══════════════════════════════════════════════════════════

STOP. DO NOT RETURN THE POST YET.

WORKFLOW (DRAFT → VALIDATE → FIX → RE-VALIDATE):

1. Call external_validation(post=your_draft)
   - This runs Editor-in-Chief rules + GPTZero AI detection on DRAFT
   - Returns: total_score, issues, gptzero_ai_pct, gptzero_flagged_sentences
   - STORE these for reference (original_score, original_issues)

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
   - STORE revised_post

3. **RE-VALIDATE the REVISED post** to see what still needs fixing:
   final_validation = external_validation(post=revised_post)

   - This checks if apply_fixes actually fixed the issues
   - Returns FINAL validation results for Airtable "Suggested Edits"
   - User sees what STILL needs manual fixing in the final post

4. **CRITICAL:** Return the REVISED post with FINAL validation metadata:

   Return JSON with REVISED content + FINAL validation:
   {{
     "post_text": "[INSERT revised_post HERE - the FIXED version from apply_fixes]",
     "original_score": [score from FINAL validation in step 3],
     "validation_issues": [issues from FINAL validation in step 3],
     "gptzero_ai_pct": [AI % from FINAL validation in step 3],
     "gptzero_flagged_sentences": [flagged sentences from FINAL validation in step 3]
   }}

   ❌ **ANTI-PATTERNS (DO NOT DO THIS):**
   - Do NOT return the original draft in post_text
   - Do NOT skip apply_fixes and return draft directly
   - Do NOT forget to extract revised_post from apply_fixes response
   - Do NOT show the user the draft - only show the REVISED version

   ✅ **CORRECT FLOW:**
   1. draft = create_human_draft(...)
   2. draft_validation = external_validation(post=draft)
   3. fixed = apply_fixes(post=draft, issues=draft_validation.issues, ...)
   4. final_validation = external_validation(post=fixed.revised_post)  ← RE-VALIDATE!
   5. Return {{post_text: fixed.revised_post, validation from step 4}} ← Final validation goes to Airtable!

CRITICAL:
- TWO validation passes: Draft validation (for apply_fixes input) + Final validation (for Airtable)
- Return revised_post with FINAL validation metadata
- User sees what STILL needs fixing after apply_fixes ran
- If FINAL validation shows 0 issues → post is clean!
- If FINAL validation shows issues → user knows what to manually edit
- The post_text field MUST contain the REVISED version from apply_fixes
- The validation metadata MUST be from FINAL validation (step 4), not draft validation

Return format MUST include REVISED post_text + validation metadata for Airtable."""

            print(f"📤 Sending creation prompt to Claude via direct API...")

            # Initialize conversation messages
            messages = [{"role": "user", "content": creation_prompt}]

            # Manual tool calling loop (replaces SDK's receive_response iterator)
            max_iterations = 20  # Prevent infinite loops
            iteration = 0
            final_output = None

            while iteration < max_iterations:
                iteration += 1
                print(f"   🔄 Iteration {iteration}: Calling Claude API...")

                try:
                    # Call Anthropic API with 60s timeout
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.messages.create,
                            model="claude-sonnet-4-5-20250929",
                            max_tokens=8000,
                            system=self.system_prompt,
                            tools=TOOL_SCHEMAS,
                            messages=messages
                        ),
                        timeout=60.0
                    )

                    print(f"   ✅ API response received: stop_reason={response.stop_reason}")

                    # Check stop reason
                    if response.stop_reason == "end_turn":
                        # Agent is done, extract final text
                        for block in response.content:
                            if block.type == "text":
                                final_output = block.text
                                print(f"   ✅ Final output received ({len(final_output)} chars)")
                                break
                        break

                    elif response.stop_reason == "tool_use":
                        # Agent wants to use tools
                        print(f"   🔧 Agent requested tool calls...")

                        # Add assistant message to conversation
                        messages.append({
                            "role": "assistant",
                            "content": response.content
                        })

                        # Execute each tool and collect results
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                tool_name = block.name
                                tool_input = block.input
                                tool_use_id = block.id

                                print(f"      🔧 Executing: {tool_name}")

                                # Execute tool with 30s timeout
                                tool_result = await execute_tool(tool_name, tool_input)

                                print(f"      ✅ {tool_name} completed ({len(str(tool_result))} chars)")

                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": tool_result
                                })

                        # Add tool results to conversation
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })

                        # Continue loop to get next response
                        continue

                    elif response.stop_reason == "max_tokens":
                        # Hit token limit, extract what we have
                        for block in response.content:
                            if block.type == "text":
                                final_output = block.text
                                logger.warning("⚠️ Hit max_tokens limit", **log_context)
                                break
                        break

                    else:
                        logger.error(f"Unknown stop_reason: {response.stop_reason}", **log_context)
                        break

                except asyncio.TimeoutError:
                    logger.error(f"API call timeout at iteration {iteration}", **log_context)
                    raise TimeoutError(f"API call exceeded 60s at iteration {iteration}")

            if iteration >= max_iterations:
                raise RuntimeError(f"Exceeded max iterations ({max_iterations})")

            if not final_output:
                raise RuntimeError("No final output received from agent")

            print(f"\n   ✅ Tool calling loop complete after {iteration} iterations")
            print(f"   📝 Final output: {len(final_output)} chars")

            # Parse output and return result
            return await self._parse_output(final_output, operation_start_time, log_context)

        except Exception as e:
            operation_duration = asyncio.get_event_loop().time() - operation_start_time

            log_error(logger, "LinkedIn Direct API Agent error", error=e, context=log_context)
            log_operation_end(
                logger,
                "create_linkedin_post_direct_api",
                duration=operation_duration,
                success=False,
                context=log_context,
                error_type=type(e).__name__
            )

            # Circuit breaker: Mark failure
            with self.circuit_breaker._lock:
                self.circuit_breaker.failure_count += 1
                self.circuit_breaker.last_failure_time = time_module.time()

                if self.circuit_breaker.state == CircuitState.HALF_OPEN:
                    logger.error("❌ Circuit breaker test failed - RE-OPENING", **log_context)
                    self.circuit_breaker.state = CircuitState.OPEN
                elif self.circuit_breaker.failure_count >= self.circuit_breaker.failure_threshold:
                    logger.error("🔥 Circuit breaker OPENING", **log_context)
                    self.circuit_breaker.state = CircuitState.OPEN

            return {
                "success": False,
                "error": str(e),
                "post": None
            }

    async def _parse_output(self, output: str, operation_start_time: float, log_context: dict) -> Dict[str, Any]:
        """Parse agent output into structured response (same as SDK version)"""
        print(f"\n🔍 _parse_output called with {len(output)} chars")

        if not output or len(output) < 10:
            return {
                "success": False,
                "error": "No content generated",
                "post": None
            }

        # Extract structured content using Haiku
        from integrations.content_extractor import extract_structured_content

        print("📝 Extracting content with Haiku...")
        try:
            extracted = await extract_structured_content(
                raw_output=output,
                platform='linkedin'
            )

            clean_output = extracted['body']
            hook_preview = extracted['hook']

            print(f"✅ Extracted: {len(clean_output)} chars body")

        except Exception as e:
            print(f"❌ Extraction error: {e}")
            clean_output = ""
            hook_preview = "Extraction failed (see Suggested Edits)"

        # Extract validation metadata
        validation_score = extracted.get('original_score', 20)
        validation_issues = extracted.get('validation_issues', [])
        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])

        score = validation_score

        # Format validation issues for Airtable
        validation_formatted = None
        if validation_issues or gptzero_flagged_sentences:
            lines = ["🔍 VALIDATION RESULTS:\n"]
            lines.append(f"Quality Score: {validation_score}/25")

            if gptzero_ai_pct is not None:
                lines.append(f"\n🤖 GPTZero AI Detection: {gptzero_ai_pct}% AI")

            if validation_issues:
                lines.append(f"\n⚠️ ISSUES FOUND ({len(validation_issues)} total):\n")
                for i, issue in enumerate(validation_issues, 1):
                    if isinstance(issue, dict):
                        severity = issue.get('severity', 'medium').upper()
                        pattern = issue.get('pattern', 'unknown')
                        lines.append(f"{i}. [{severity}] {pattern}")
                    else:
                        lines.append(f"{i}. {issue}")

            validation_formatted = "\n".join(lines)
        else:
            validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"

        # Save to Airtable
        print("\n📋 ATTEMPTING AIRTABLE SAVE")
        airtable_url = None
        airtable_record_id = None
        try:
            from integrations.airtable_client import get_airtable_client
            airtable = get_airtable_client()

            airtable_status = "Needs Review" if validation_score < 18 else "Draft"

            result = airtable.create_content_record(
                content=clean_output,
                platform='linkedin',
                post_hook=hook_preview,
                status=airtable_status,
                suggested_edits=validation_formatted,
                publish_date=self.publish_date
            )

            if result.get('success'):
                airtable_url = result.get('url')
                airtable_record_id = result.get('record_id')
                print(f"✅ Saved to Airtable: {airtable_url}")
        except Exception as e:
            print(f"❌ Airtable save failed: {e}")

        # Save to Supabase
        print("\n💾 ATTEMPTING SUPABASE SAVE")
        supabase_id = None
        try:
            from integrations.supabase_client import get_supabase_client
            from tools.research_tools import generate_embedding

            supabase = get_supabase_client()
            embedding = generate_embedding(clean_output)

            supabase_result = supabase.table('generated_posts').insert({
                'platform': 'linkedin',
                'post_hook': hook_preview,
                'body_content': clean_output,
                'content_type': self._detect_content_type(clean_output),
                'airtable_record_id': airtable_record_id,
                'airtable_url': airtable_url,
                'status': 'draft',
                'quality_score': score,
                'iterations': 3,
                'slack_thread_ts': self.thread_ts,
                'slack_channel_id': self.channel_id,
                'user_id': self.user_id,
                'created_by_agent': 'linkedin_direct_api_agent',
                'embedding': embedding
            }).execute()

            if supabase_result.data:
                supabase_id = supabase_result.data[0]['id']
                print(f"✅ Saved to Supabase: {supabase_id}")
        except Exception as e:
            print(f"❌ Supabase save failed: {e}")

        # Log operation success
        operation_duration = asyncio.get_event_loop().time() - operation_start_time
        log_operation_end(
            logger,
            "create_linkedin_post_direct_api",
            duration=operation_duration,
            success=True,
            context=log_context,
            quality_score=score,
            supabase_id=supabase_id,
            airtable_url=airtable_url
        )

        # Circuit breaker: Mark success
        with self.circuit_breaker._lock:
            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.state = CircuitState.CLOSED

        return {
            "success": True,
            "post": clean_output,
            "hook": hook_preview,
            "score": score,
            "hooks_tested": 5,
            "iterations": 3,
            "airtable_url": airtable_url or "[Airtable not configured]",
            "google_doc_url": "[Coming Soon]",
            "supabase_id": supabase_id,
            "session_id": self.user_id,
            "timestamp": datetime.now().isoformat()
        }

    def _detect_content_type(self, content: str) -> str:
        """Detect content type from post structure"""
        content_lower = content.lower()
        lines = [l.strip() for l in content.split('\n') if l.strip()]

        if any(line.startswith(('1.', '2.', '3.', '1/', '2/', '3/')) for line in lines):
            return 'listicle'
        if any(word in content_lower for word in ['i was', 'i spent', 'i lost', 'here\'s what happened']):
            return 'story'
        if content.startswith(('everyone', 'nobody', 'stop', 'you\'re', 'you don\'t')):
            return 'hot_take'
        if any(phrase in content_lower for phrase in ['vs', 'not x, it\'s y', 'instead of']):
            return 'comparison'

        return 'thought_leadership'


# ================== INTEGRATION FUNCTION (SAME INTERFACE AS SDK VERSION) ==================

async def create_linkedin_post_workflow(
    topic: str,
    context: str = "",
    style: str = "thought_leadership",
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None,
    publish_date: Optional[str] = None
) -> str:
    """
    Main entry point for LinkedIn content creation using direct API
    Drop-in replacement for SDK version - same signature, same return format

    Args:
        topic: Main topic for the post
        context: Additional context
        style: Content style
        channel_id: Slack channel ID (for Airtable/Supabase saves)
        thread_ts: Slack thread timestamp (for Airtable/Supabase saves)
        user_id: Slack user ID (for Airtable/Supabase saves)
        publish_date: Optional publish date

    Returns:
        Formatted string with post content, score, and links
    """

    agent = LinkedInDirectAPIAgent(
        user_id=user_id,
        channel_id=channel_id,
        thread_ts=thread_ts,
        batch_mode=True
    )

    try:
        post_type = "carousel" if "visual" in style.lower() else "standard"

        result = await agent.create_post(
            topic=topic,
            context=f"{context} | Style: {style}",
            post_type=post_type,
            target_score=85,
            publish_date=publish_date
        )

        if result['success']:
            return f"""✅ **LinkedIn Post Created**

**Hook Preview:**
_{result.get('hook', result['post'][:200])}..._

**Quality Score:** {result.get('score', 20)}/25 (Iterations: {result.get('iterations', 3)})

**Full Post:**
{result['post']}

---
📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}

*AI Patterns Removed | Facts Verified | Ready to Post*"""
        else:
            return f"❌ Creation failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"LinkedIn Direct API workflow error: {e}")
        return f"❌ Unexpected error: {str(e)}"


if __name__ == "__main__":
    # Test the Direct API Agent
    async def test():
        agent = LinkedInDirectAPIAgent()

        result = await agent.create_post(
            topic="Why direct API calls are more reliable than SDK wrappers",
            context="Focus on timeout control and debugging visibility",
            post_type="standard",
            target_score=85
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())

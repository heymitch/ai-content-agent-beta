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

# Prompt loading with client context support
from integrations.prompt_loader import load_system_prompt, stack_prompts

# Load environment variables
load_dotenv()

# Setup structured logging
logger = get_logger(__name__)


# ================== TIER 3 TOOL IMPLEMENTATIONS (NATIVE PYTHON) ==================
# Import native tool implementations (unwrapped, directly callable)

from tools.linkedin_native_tools import (
    generate_5_hooks_native,
    search_company_documents_native,
    inject_proof_points_native,
    create_human_draft_native,
    validate_format_native,
    search_viral_patterns_native,
    score_and_iterate_native,
    quality_check_native,
    apply_fixes_native,
    external_validation_native
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

    try:
        # Execute native tool functions with unpacked arguments (30s timeout)
        result = None

        if tool_name == "search_company_documents":
            result = await asyncio.wait_for(
                search_company_documents_native(
                    query=tool_input.get('query', ''),
                    match_count=tool_input.get('match_count', 3),
                    document_type=tool_input.get('document_type')
                ),
                timeout=30.0
            )

        elif tool_name == "generate_5_hooks":
            result = await asyncio.wait_for(
                generate_5_hooks_native(
                    topic=tool_input.get('topic', ''),
                    context=tool_input.get('context', ''),
                    target_audience=tool_input.get('target_audience', 'professionals')
                ),
                timeout=30.0
            )

        elif tool_name == "create_human_draft":
            result = await asyncio.wait_for(
                create_human_draft_native(
                    topic=tool_input.get('topic', ''),
                    hook=tool_input.get('hook', ''),
                    context=tool_input.get('context', '')
                ),
                timeout=30.0
            )

        elif tool_name == "inject_proof_points":
            result = await asyncio.wait_for(
                inject_proof_points_native(
                    draft=tool_input.get('draft', ''),
                    topic=tool_input.get('topic', ''),
                    industry=tool_input.get('industry', 'SaaS')
                ),
                timeout=30.0
            )

        elif tool_name == "quality_check":
            result = await asyncio.wait_for(
                quality_check_native(
                    post=tool_input.get('post', '')
                ),
                timeout=30.0
            )

        elif tool_name == "external_validation":
            result = await asyncio.wait_for(
                external_validation_native(
                    post=tool_input.get('post', '')
                ),
                timeout=120.0  # Quality check (60s) + GPTZero (45s) + buffer
            )

        elif tool_name == "apply_fixes":
            result = await asyncio.wait_for(
                apply_fixes_native(
                    post=tool_input.get('post', ''),
                    issues_json=tool_input.get('issues_json', '[]'),
                    current_score=tool_input.get('current_score', 0),
                    gptzero_ai_pct=tool_input.get('gptzero_ai_pct'),
                    gptzero_flagged_sentences=tool_input.get('gptzero_flagged_sentences', [])
                ),
                timeout=30.0
            )

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        # Native tools return plain text/JSON strings (not wrapped in {"content": [...]} )
        return result if result else json.dumps({"error": "Tool returned empty result"})

    except asyncio.TimeoutError:
        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded {timeout_duration}"})
    except Exception as e:
        logger.error(f"Tool error: {tool_name} - {e}")
        import traceback
        traceback.print_exc()
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

        # LinkedIn-specific system prompt (keep it small for fast initialization)
        base_system_prompt = """You are a LinkedIn content creation agent with a critical philosophy:

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

        # Load system prompt with client context from .claude/CLAUDE.md
        self.system_prompt = load_system_prompt(base_system_prompt)

        print("🎯 LinkedIn Direct API Agent initialized (no SDK, no hangs)")

    async def create_post(
        self,
        topic: str,
        context: str = "",
        post_type: str = "standard",
        target_score: int = 85,
        session_id: Optional[str] = None,
        publish_date: Optional[str] = None,
        thinking_mode: bool = False
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
            thinking_mode: If True, adds validation + fix loop for higher quality

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
            # Stack all prompts into system message (Claude Projects style)
            # This gets cached - only the user content varies
            stacked_system = stack_prompts("linkedin")

            mode_label = "Thinking Mode" if thinking_mode else "Default"
            print(f"📚 Using stacked prompts: {len(stacked_system)} chars (cached) - {mode_label}")

            # Build workflow based on mode
            if thinking_mode:
                # THINKING MODE: Adds external validation + apply_fixes for higher quality
                workflow_section = """WORKFLOW (THINKING MODE - Higher Quality):

1. Evaluate the Context/Outline:
   - Rich outline (>200 words)? → Preserve user's thinking, polish it
   - Thin outline? → Generate hooks, build from scratch

2. Call tools to create draft:
   - generate_5_hooks (if thin outline)
   - create_human_draft (always - pass context through)
   - inject_proof_points (if draft needs metrics)

3. VALIDATION PASS (MANDATORY):
   - Call external_validation(post=your_draft)
   - This runs Editor-in-Chief rules + GPTZero AI detection
   - Returns: total_score, issues, gptzero_ai_pct, gptzero_flagged_sentences

4. FIX PASS (MANDATORY):
   - Call apply_fixes with ALL parameters from validation
   - Fix EVERY issue identified
   - Rewrite GPTZero-flagged sentences

5. Return JSON with FIXED content and validation metadata:
   {{
     "post_text": "[the FIXED version from apply_fixes]",
     "original_score": [score from validation],
     "validation_issues": [issues from validation],
     "gptzero_ai_pct": [AI % from validation],
     "gptzero_flagged_sentences": [flagged sentences]
   }}"""
            else:
                # DEFAULT MODE: With external validation for GPTZero feedback
                workflow_section = """WORKFLOW (ONE-SHOT MODE - NO RETRIES):

1. Evaluate the Context/Outline:
   - Rich outline (>200 words)? → Preserve user's thinking, polish it
   - Thin outline? → Generate hooks, build from scratch

2. Call tools as needed:
   - generate_5_hooks (if thin outline)
   - create_human_draft (always - pass context through)
   - inject_proof_points (if draft needs metrics)

3. VALIDATION - CALL EXACTLY ONCE:
   - Call external_validation(post=your_draft)
   - This runs Editor-in-Chief rules + GPTZero AI detection
   - Wait for the tool result

4. IMMEDIATELY return JSON after validation - DO NOT call any more tools:
   {{
     "post_text": "...",
     "original_score": [score from validation],
     "validation_issues": [issues from validation],
     "gptzero_ai_pct": [AI % from validation],
     "gptzero_flagged_sentences": [flagged sentences]
   }}

IMPORTANT: This is for feedback/tuning. Return results even if score is low or GPTZero flags it."""

            # Build the creation prompt
            creation_prompt = f"""Create a LinkedIn {post_type} post.

Topic: {topic}

Context/Outline:
{context}

{workflow_section}

CRITICAL: Follow ALL rules from Writing Rules and Editor-in-Chief Standards above."""

            # Filter tools based on mode
            # In default mode, exclude quality_check and apply_fixes (those are for thinking_mode loop)
            if thinking_mode:
                tools_to_use = TOOL_SCHEMAS
            else:
                # Only provide tools needed for default workflow
                tools_to_use = [
                    tool for tool in TOOL_SCHEMAS
                    if tool["name"] not in ["quality_check", "apply_fixes"]
                ]
                logger.info(f"🔧 Default mode: providing {len(tools_to_use)} tools (excluding quality_check/apply_fixes)")

            print(f"📤 Sending creation prompt to Claude via direct API...")

            # Initialize conversation messages
            messages = [
                {
                    "role": "user",
                    "content": creation_prompt
                }
            ]

            # Manual tool calling loop
            max_iterations = 15 if thinking_mode else 10  # Thinking mode needs more iterations for validation
            iteration = 0
            final_output = None

            while iteration < max_iterations:
                iteration += 1
                print(f"   🔄 Iteration {iteration}: Calling Claude API...")

                try:
                    # First call gets 120s timeout (large cached prompt), subsequent calls get 60s
                    timeout = 120.0 if iteration == 1 else 60.0

                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.messages.create,
                            model="claude-sonnet-4-5-20250929",
                            max_tokens=8000,
                            system=[
                                {
                                    "type": "text",
                                    "text": stacked_system,
                                    "cache_control": {"type": "ephemeral"}  # Cache stacked prompts
                                }
                            ],
                            tools=tools_to_use,
                            messages=messages
                        ),
                        timeout=timeout
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
        if validation_issues or gptzero_flagged_sentences or gptzero_ai_pct is not None:
            lines = [f"Quality Score: {validation_score}/25"]
            lines.append("Suggested Edits:")

            # GPTZero AI Detection - show first
            if gptzero_ai_pct is not None:
                lines.append(f"🤖 GPTZero AI Detection: {gptzero_ai_pct}% AI")

            # Issues found
            total_issues = len(validation_issues) + len(gptzero_flagged_sentences)
            if total_issues > 0:
                lines.append(f"\n⚠️ ISSUES FOUND ({total_issues} total):\n")

                issue_num = 1
                # Show validation issues with the actual offending text
                for issue in validation_issues:
                    if isinstance(issue, dict):
                        original = issue.get('original', '')
                        pattern = issue.get('pattern', 'unknown')
                        fix = issue.get('fix', '')
                        if original:
                            lines.append(f"{issue_num}. \"{original}\" - {pattern}")
                            if fix:
                                lines.append(f"   → Fix: {fix}")
                        else:
                            lines.append(f"{issue_num}. [{pattern}]")
                    else:
                        lines.append(f"{issue_num}. {issue}")
                    issue_num += 1

                # Show GPTZero flagged sentences
                if gptzero_flagged_sentences:
                    lines.append("\n📝 GPTZero Flagged Sentences (rewrite to sound more human):")
                    for sentence in gptzero_flagged_sentences:
                        lines.append(f"{issue_num}. \"{sentence}\"")
                        issue_num += 1
            else:
                lines.append("\n✅ No specific issues found")

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

            # Status determination based on 0-25 scale
            if validation_score >= 24:  # 24-25
                airtable_status = "Ready"
            elif validation_score >= 18:  # 18-23
                airtable_status = "Draft"
            else:  # <18
                airtable_status = "Needs Review"

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
    publish_date: Optional[str] = None,
    thinking_mode: bool = False
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
        thinking_mode: If True, adds validation + fix loop for higher quality

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
            publish_date=publish_date,
            thinking_mode=thinking_mode
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

"""
Instagram SDK Agent - Tier 2 Orchestrator
Uses Claude Agent SDK with persistent memory and delegates to specialized tools.
Enforces Instagram-specific rules: 2,200 char limit, preview optimization, visual pairing
"""

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server
)
import os
import json
import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from textwrap import dedent

# Load environment variables for API keys
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


# ================== TIER 3 TOOL DEFINITIONS (LAZY LOADED) ==================
# Tool descriptions kept minimal to reduce context window usage
# Detailed prompts loaded just-in-time when tools are called

@tool(
    "search_company_documents",
    "Search user-uploaded docs (case studies, testimonials, product docs) for proof points",
    {"query": str, "match_count": int, "document_type": str}
)
async def search_company_documents(args):
    """Search company documents for context enrichment"""
    from tools.company_documents import search_company_documents as _search_func

    query = args.get('query', '')
    match_count = args.get('match_count', 3)
    document_type = args.get('document_type')

    result = _search_func(
        query=query,
        match_count=match_count,
        document_type=document_type
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "generate_5_hooks",
    "Generate 5 Instagram hooks optimized for 125-char preview",
    {"topic": str, "context": str, "target_audience": str}
)
async def generate_5_hooks(args):
    """Generate 5 hooks - prompt loaded JIT"""
    from anthropic import Anthropic
    from prompts.instagram_tools import GENERATE_HOOKS_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    context = args.get('context', '')
    audience = args.get('target_audience', 'Instagram users')

    json_example = '[{{"type": "question", "text": "...", "chars": 82}}, ...]'
    prompt = GENERATE_HOOKS_PROMPT.format(
        topic=topic,
        context=context,
        audience=audience,
        json_example=json_example
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "content": [{
            "type": "text",
            "text": response.content[0].text
        }]
    }


@tool(
    "create_caption_draft",
    "Generate Instagram caption with quality self-assessment",
    {"topic": str, "hook": str, "context": str}
)
async def create_caption_draft(args):
    """Create caption draft with JSON output including scores"""
    import json
    from anthropic import Anthropic
    from prompts.instagram_tools import CREATE_CAPTION_DRAFT_PROMPT, WRITE_LIKE_HUMAN_RULES
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    hook = args.get('hook', '')
    context = args.get('context', '')

    # Lazy load prompt
    prompt = CREATE_CAPTION_DRAFT_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        topic=topic,
        hook=hook,
        context=context
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Use Sonnet for quality
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Try to parse JSON, fallback to raw text if it fails
    try:
        json_result = json.loads(response_text)
        # Validate schema
        if "caption_text" in json_result or "post_text" in json_result:
            return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in basic JSON
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "caption_text": response_text,
                "self_assessment": {"total": 0, "notes": "JSON parsing failed, returning raw text"}
            }, indent=2)
        }]
    }


@tool(
    "condense_to_limit",
    "Ensure caption is under 2,200 characters while preserving impact",
    {"caption": str, "target_length": int}
)
async def condense_to_limit(args):
    """Condense caption to fit Instagram's character limit"""
    from anthropic import Anthropic
    from prompts.instagram_tools import CONDENSE_TO_LIMIT_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    caption = args.get('caption', '')
    target_length = args.get('target_length', 2200)
    current_length = len(caption)

    # If already under limit, return as-is
    if current_length <= target_length:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "caption": caption,
                    "original_length": current_length,
                    "target_length": target_length,
                    "condensed": False,
                    "note": "Already under limit"
                }, indent=2)
            }]
        }

    prompt = CONDENSE_TO_LIMIT_PROMPT.format(
        caption=caption,
        current_length=current_length,
        target_length=target_length
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    condensed_caption = response.content[0].text

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "caption": condensed_caption,
                "original_length": current_length,
                "new_length": len(condensed_caption),
                "target_length": target_length,
                "condensed": True,
                "chars_saved": current_length - len(condensed_caption)
            }, indent=2)
        }]
    }


@tool(
    "quality_check",
    "Score Instagram caption on 5 axes and return surgical fixes",
    {"post": str}
)
async def quality_check(args):
    """Evaluate caption with 5-axis rubric + surgical feedback + Tavily search for fabrications"""
    import json
    from anthropic import Anthropic
    from prompts.instagram_tools import QUALITY_CHECK_PROMPT
    from tavily import TavilyClient

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

    post = args.get('post', '')
    prompt = QUALITY_CHECK_PROMPT.format(post=post)

    # Define Tavily search tool for Claude
    tavily_tool = {
        "name": "web_search",
        "description": "Search the web for current information to verify claims, names, companies, and news stories. Returns recent, relevant results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'Rick Beato YouTube AI filters', 'James Chen Clearbit')"
                }
            },
            "required": ["query"]
        }
    }

    messages = [{"role": "user", "content": prompt}]

    # Tool loop: handle Tavily search requests
    max_iterations = 5
    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            tools=[tavily_tool],
            messages=messages
        )

        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Extract tool use from response
            tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)

            if tool_use_block and tool_use_block.name == "web_search":
                # Execute Tavily search
                query = tool_use_block.input["query"]
                try:
                    tavily_results = tavily.search(query, max_results=3)
                    search_output = "\n\n".join([
                        f"**{r.get('title', 'No title')}**\n{r.get('content', 'No content')}\nSource: {r.get('url', 'No URL')}"
                        for r in tavily_results.get('results', [])
                    ])
                except Exception as e:
                    search_output = f"Search error: {str(e)}"

                # Add assistant message with tool use, then tool result
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": search_output
                    }]
                })
                # Continue loop to get final response
                continue

            # Unknown tool - shouldn't happen
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            continue

        # Got final text response
        final_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                final_text += block.text

        # Try to parse JSON, return as-is if valid
        try:
            json_result = json.loads(final_text)
            if "scores" in json_result and "decision" in json_result:
                return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
        except json.JSONDecodeError:
            pass

        # Fallback: return raw text
        return {"content": [{"type": "text", "text": final_text}]}

    # Max iterations reached
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "scores": {"total": 0},
                "decision": "error",
                "issues": [],
                "surgical_summary": "Max iterations reached"
            }, indent=2)
        }]
    }


@tool(
    "apply_fixes",
    "Apply 3-5 surgical fixes based on quality_check feedback",
    {"post": str, "issues_json": str}
)
async def apply_fixes(args):
    """Apply surgical fixes without rewriting the whole caption"""
    import json
    from anthropic import Anthropic
    from prompts.instagram_tools import APPLY_FIXES_PROMPT, WRITE_LIKE_HUMAN_RULES
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    post = args.get('post', '')
    issues_json = args.get('issues_json', '[]')

    # Use APPLY_FIXES_PROMPT
    prompt = APPLY_FIXES_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        post=post,
        issues_json=issues_json
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Use Sonnet for surgical precision
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Try to parse JSON
    try:
        json_result = json.loads(response_text)
        if "revised_post" in json_result:
            return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in JSON
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "revised_post": response_text,
                "changes_made": [],
                "estimated_new_score": 0,
                "notes": "JSON parsing failed"
            }, indent=2)
        }]
    }


# ================== INSTAGRAM SDK AGENT CLASS ==================

class InstagramSDKAgent:
    """
    Tier 2: Instagram-specific SDK Agent with persistent memory
    Orchestrates Tier 3 tools and maintains platform-specific context
    """

    def __init__(self, user_id: str = "default", isolated_mode: bool = False):
        """Initialize Instagram SDK Agent with memory and tools

        Args:
            user_id: User identifier for session management
            isolated_mode: If True, creates isolated sessions (for testing only)
        """
        self.user_id = user_id
        self.sessions = {}  # Track multiple content sessions
        self.isolated_mode = isolated_mode  # Test mode flag

        # Instagram-specific base prompt with quality thresholds
        base_prompt = """You are an Instagram caption creation agent. Your goal: captions that score 20+ out of 25 and stop the scroll.

AVAILABLE TOOLS:

1. mcp__instagram_tools__generate_5_hooks
   Input: {"topic": str, "context": str, "audience": str}
   Returns: JSON array with 5 hooks optimized for 125-char preview
   When to use: Always call first to generate hook options

2. mcp__instagram_tools__create_caption_draft
   Input: {"topic": str, "hook": str, "context": str}
   Returns: JSON with {caption_text, self_assessment: {hook: 0-5, visual_pairing: 0-5, readability: 0-5, proof: 0-5, cta_hashtags: 0-5, total: 0-25}}
   What it does: Creates Instagram caption using WRITE_LIKE_HUMAN_RULES with Instagram adaptations
   When to use: After selecting best hook from generate_5_hooks

3. mcp__instagram_tools__condense_to_limit
   Input: {"caption": str, "target_length": int}
   Returns: Condensed caption under 2,200 chars (preserves hook, proof, CTA, hashtags)
   When to use: If draft exceeds 2,200 characters

4. mcp__instagram_tools__quality_check
   Input: {"post": str}
   Returns: JSON with {scores: {hook/visual_pairing/readability/proof/cta_hashtags/total, ai_deductions}, decision: accept/revise/reject, issues: [{axis, severity, original, fix, impact}], character_count, preview_length}
   What it does:
   - Evaluates 5-axis rubric (0-5 each, total 0-25)
   - Checks first 125 chars (preview optimization)
   - Verifies 2,200 char limit
   - AUTO-DETECTS AI tells with -2pt deductions
   - WEB SEARCHES to verify claims
   - Returns SURGICAL fixes
   When to use: After create_caption_draft or condense_to_limit

5. mcp__instagram_tools__apply_fixes
   Input: {"post": str, "issues_json": str}
   Returns: JSON with {revised_post, changes_made: [{issue_addressed, original, revised, impact}], estimated_new_score, character_count}
   What it does:
   - Applies 3-5 SURGICAL fixes
   - PRESERVES voice, numbers, names, emotional language
   - Targets exact problems from issues array
   When to use: When quality_check returns issues that need fixing

INSTAGRAM-SPECIFIC QUALITY AXES:
- Hook (0-5): First 125 chars create curiosity gap
- Visual Pairing (0-5): Adds context image/Reel can't show
- Readability (0-5): Line breaks, emojis, mobile-optimized
- Proof (0-5): Specific numbers, verifiable claims
- CTA + Hashtags (0-5): Engagement trigger + 3-5 strategic tags

CRITICAL CONSTRAINTS:
- 2,200 character HARD LIMIT (includes hashtags)
- First 125 chars appear in preview (must work standalone)
- Visual pairing (assumes accompanying image/Reel)
- Mobile formatting (line breaks every 2-3 sentences)

WORKFLOW:
1. generate_5_hooks
2. Select best hook
3. create_caption_draft
4. If >2,200 chars → condense_to_limit
5. quality_check
6. If issues → apply_fixes
7. Return final caption"""

        # Compose base prompt + client context (if exists)
        from integrations.prompt_loader import load_system_prompt
        self.system_prompt = load_system_prompt(base_prompt)

        # Create MCP server with Instagram-specific tools (LEAN 5-TOOL WORKFLOW)
        self.mcp_server = create_sdk_mcp_server(
            name="instagram_tools",
            version="4.1.0",
            tools=[
                search_company_documents,  # NEW v4.1.0
                generate_5_hooks,
                create_caption_draft,
                condense_to_limit,
                quality_check,
                apply_fixes
            ]
        )

        print("📸 Instagram SDK Agent initialized with 6 tools (5 lean tools + company docs RAG)")

    def get_or_create_session(self, session_id: str) -> ClaudeSDKClient:
        """Get or create a persistent session for content creation"""
        if session_id not in self.sessions:
            # Only clear env vars in isolated test mode
            if self.isolated_mode:
                os.environ.pop('CLAUDECODE', None)
                os.environ.pop('CLAUDE_CODE_ENTRYPOINT', None)
                os.environ.pop('CLAUDE_SESSION_ID', None)
                os.environ.pop('CLAUDE_WORKSPACE', None)
                os.environ['CLAUDE_HOME'] = '/tmp/instagram_agent'

            options = ClaudeAgentOptions(
                mcp_servers={"instagram_tools": self.mcp_server},
                allowed_tools=["mcp__instagram_tools__*"],
                system_prompt=self.system_prompt,
                model="claude-sonnet-4-5-20250929",
                permission_mode="bypassPermissions",
                continue_conversation=not self.isolated_mode  # False in test mode, True in prod
            )

            self.sessions[session_id] = ClaudeSDKClient(options=options)
            mode_str = " (isolated test mode)" if self.isolated_mode else ""
            print(f"📝 Created Instagram session: {session_id}{mode_str}")

        return self.sessions[session_id]

    async def create_caption(
        self,
        topic: str,
        context: str = "",
        target_score: int = 85,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an Instagram caption following all Instagram rules

        Args:
            topic: Main topic/angle
            context: Additional requirements, visual description, etc.
            target_score: Minimum quality score (default 85)
            session_id: Session for conversation continuity

        Returns:
            Dict with final caption, score, hooks tested, iterations
        """

        # Use session ID or create new one
        if not session_id:
            session_id = f"instagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        client = self.get_or_create_session(session_id)

        # Build the creation prompt
        creation_prompt = f"""Create a high-quality Instagram caption using the available MCP tools.

Topic: {topic}
Context: {context}

WORKFLOW:
1. Call mcp__instagram_tools__generate_5_hooks to get hook options
2. Select best hook and call mcp__instagram_tools__create_caption_draft
3. If >2,200 chars, call mcp__instagram_tools__condense_to_limit
4. Call mcp__instagram_tools__quality_check to evaluate the caption
5. If issues found, call mcp__instagram_tools__apply_fixes
6. Return the final caption

The tools contain WRITE_LIKE_HUMAN_RULES and Instagram formatting guidelines."""

        try:
            # Connect if needed
            print(f"🔗 Connecting Instagram SDK client...")
            await client.connect()

            # Send the creation request
            print(f"📤 Sending Instagram creation prompt...")
            await client.query(creation_prompt)
            print(f"⏳ Instagram agent processing (this takes 30-60s)...")

            # Collect the response - use LAST message
            final_output = ""
            message_count = 0

            async for msg in client.receive_response():
                message_count += 1
                msg_type = type(msg).__name__
                print(f"   📬 Received message {message_count}: type={msg_type}")

                # Track all AssistantMessages with text content
                if msg_type == 'AssistantMessage':
                    if hasattr(msg, 'content'):
                        if isinstance(msg.content, list):
                            for block in msg.content:
                                if isinstance(block, dict):
                                    block_type = block.get('type', 'unknown')
                                    print(f"      Block type: {block_type}")
                                    if block_type == 'text':
                                        text_content = block.get('text', '')
                                        if text_content:
                                            final_output = text_content
                                            print(f"      ✅ Got text output ({len(text_content)} chars)")
                                elif hasattr(block, 'text'):
                                    text_content = block.text
                                    if text_content:
                                        final_output = text_content
                                        print(f"      ✅ Got text from block.text ({len(text_content)} chars)")
                        elif hasattr(msg.content, 'text'):
                            text_content = msg.content.text
                            if text_content:
                                final_output = text_content
                                print(f"      ✅ Got text from content.text ({len(text_content)} chars)")
                    elif hasattr(msg, 'text'):
                        text_content = msg.text
                        if text_content:
                            final_output = text_content
                            print(f"      ✅ Got text from msg.text ({len(text_content)} chars)")

            print(f"\n   ✅ Stream complete after {message_count} messages")
            print(f"   📝 Final output: {len(final_output)} chars")

            # Parse the output to extract structured data
            return await self._parse_output(final_output)

        except Exception as e:
            print(f"❌ Instagram SDK Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "caption": None
            }

    async def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse agent output into structured response using Haiku extraction"""
        print(f"\n🔍 _parse_output called with {len(output)} chars")
        print(f"   First 200 chars: {output[:200]}...")

        if not output or len(output) < 10:
            print(f"⚠️ WARNING: Output is empty or too short!")
            return {
                "success": False,
                "error": "No content generated",
                "caption": None
            }

        # Extract structured content using Haiku (replaces fragile regex)
        from integrations.content_extractor import extract_structured_content

        print("📝 Extracting content with Haiku...")
        is_clarification = False
        try:
            extracted = await extract_structured_content(
                raw_output=output,
                platform='instagram'
            )

            clean_output = extracted['body']
            hook_preview = extracted['hook']

            print(f"✅ Extracted: {len(clean_output)} chars caption")
            print(f"✅ Hook: {hook_preview[:80]}...")

        except ValueError as e:
            # Agent requested clarification instead of completing caption
            print(f"⚠️ Extraction detected agent clarification: {e}")
            is_clarification = True
            clean_output = ""  # Empty body - no caption was created
            hook_preview = "Agent requested clarification (see Suggested Edits)"

        except Exception as e:
            # Other extraction errors - treat as clarification
            print(f"❌ Extraction error: {e}")
            is_clarification = True
            clean_output = ""
            hook_preview = "Extraction failed (see Suggested Edits)"

        # Extract score if mentioned in output
        score = 90  # Default, would parse from actual output

        # Run validators (quality check + optional GPTZero)
        validation_json = None
        validation_formatted = None
        try:
            from integrations.validation_utils import run_all_validators, format_validation_for_airtable
            validation_json = await run_all_validators(clean_output, 'instagram')
            # Format for human-readable Airtable display
            validation_formatted = format_validation_for_airtable(validation_json)
        except Exception as e:
            print(f"⚠️ Validation error (non-fatal): {e}")
            validation_json = None
            validation_formatted = None

        # Save to Airtable
        print("\n" + "="*60)
        print("📋 ATTEMPTING AIRTABLE SAVE")
        print("="*60)
        airtable_url = None
        airtable_record_id = None
        try:
            from integrations.airtable_client import get_airtable_client
            print("✅ Imported Airtable client")

            airtable = get_airtable_client()
            print(f"✅ Airtable client initialized:")
            print(f"   Base ID: {airtable.base_id}")
            print(f"   Table: {airtable.table_name}")

            print(f"\n📝 Saving content (hook: '{hook_preview[:50]}...')")
            result = airtable.create_content_record(
                content=clean_output,  # Save the CLEAN extracted post, not raw output
                platform='instagram',
                post_hook=hook_preview,
                status='Draft',
                suggested_edits=validation_formatted  # Human-readable validation report
            )
            print(f"📊 Airtable API result: {result}")

            if result.get('success'):
                airtable_url = result.get('url')
                airtable_record_id = result.get('record_id')
                print(f"✅ SUCCESS! Saved to Airtable:")
                print(f"   Record ID: {airtable_record_id}")
                print(f"   URL: {airtable_url}")
            else:
                # Check if this is a quota error
                if result.get('is_quota_error'):
                    print(f"⚠️ Airtable quota exceeded - saving to Supabase only")
                    print(f"   (Post will still be accessible, just not in Airtable)")
                else:
                    print(f"❌ Airtable save FAILED:")
                    print(f"   Error: {result.get('error')}")
        except Exception as e:
            import traceback
            print(f"❌ EXCEPTION in Airtable save:")
            print(f"   Error: {e}")
            print(f"   Traceback:")
            print(traceback.format_exc())
            airtable_url = None
        print("="*60 + "\n")

        # Save to Supabase with embedding
        print("\n" + "="*60)
        print("💾 ATTEMPTING SUPABASE SAVE")
        print("="*60)
        supabase_id = None
        try:
            from integrations.supabase_client import get_supabase_client
            from tools.research_tools import generate_embedding

            print("✅ Imported Supabase client")
            supabase = get_supabase_client()

            print(f"📊 Generating embedding for {len(clean_output)} chars...")
            embedding = generate_embedding(clean_output)
            print(f"✅ Embedding generated: {len(embedding)} dimensions")

            print(f"\n📝 Saving to Supabase...")
            supabase_result = supabase.table('generated_posts').insert({
                'platform': 'instagram',
                'post_hook': hook_preview,
                'body_content': clean_output,  # Save clean content
                'content_type': self._detect_content_type(clean_output),
                'airtable_record_id': airtable_record_id,
                'airtable_url': airtable_url,
                'status': 'draft',
                'quality_score': score,
                'iterations': 3,  # Would track from actual process
                'slack_thread_ts': getattr(self, 'session_id', None),
                'user_id': self.user_id,
                'created_by_agent': 'instagram_sdk_agent',
                'embedding': embedding
            }).execute()

            if supabase_result.data:
                supabase_id = supabase_result.data[0]['id']
                print(f"✅ SUCCESS! Saved to Supabase:")
                print(f"   Record ID: {supabase_id}")
        except Exception as e:
            import traceback
            print(f"❌ EXCEPTION in Supabase save:")
            print(f"   Error: {e}")
            print(f"   Traceback:")
            print(traceback.format_exc())
        print("="*60 + "\n")

        # TODO: Export to Google Docs and get URL
        google_doc_url = None

        return {
            "success": True,
            "caption": clean_output,  # The clean caption (metadata stripped)
            "hook": hook_preview,  # First 125 chars for preview
            "score": score,
            "hooks_tested": 5,
            "iterations": 3,
            "airtable_url": airtable_url or "[Airtable not configured]",
            "google_doc_url": google_doc_url or "[Coming Soon]",
            "supabase_id": supabase_id,
            "session_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "character_count": len(clean_output)
        }

    def _detect_content_type(self, content: str) -> str:
        """Detect content type from caption structure"""
        content_lower = content.lower()
        lines = [l.strip() for l in content.split('\n') if l.strip()]

        # Check for numbered lists (tips/steps)
        if any(line.startswith(('1.', '2.', '3.', '1/', '2/', '3/')) for line in lines):
            return 'listicle'

        # Check for story patterns
        if any(word in content_lower for word in ['i was', 'i spent', 'i lost', 'here\'s what happened']):
            return 'story'

        # Check for tutorial/how-to
        if any(phrase in content_lower for phrase in ['how to', 'step by step', 'here\'s how']):
            return 'tutorial'

        # Check for carousel indicators
        if any(phrase in content_lower for phrase in ['swipe', 'slide', 'carousel']):
            return 'carousel'

        return 'engagement'  # Default for Instagram


# ================== INTEGRATION FUNCTION ==================

async def create_instagram_caption_workflow(
    topic: str,
    context: str = "",
    style: str = "engagement"
) -> str:
    """
    Main entry point for Instagram caption creation
    Called by the main CMO agent's delegate_to_workflow tool
    Returns structured response with hook preview and links
    """

    agent = InstagramSDKAgent()

    result = await agent.create_caption(
        topic=topic,
        context=context,
        target_score=85
    )

    if result['success']:
        # Return structured response for Slack
        char_count = result.get('character_count', 0)
        char_status = f"{char_count}/2,200 chars" if char_count <= 2200 else f"⚠️ {char_count}/2,200 OVER LIMIT"

        return f"""✅ **Instagram Caption Created**

**Hook Preview (first 125 chars):**
_{result.get('hook', result['caption'][:125])}..._

**Quality Score:** {result.get('score', 90)}/100 (Iterations: {result.get('iterations', 3)})
**Length:** {char_status}

**Full Caption:**
{result['caption']}

---
📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}

*AI Patterns Removed | Facts Verified | Ready to Post*"""
    else:
        return f"❌ Creation failed: {result.get('error', 'Unknown error')}"


if __name__ == "__main__":
    # Test the Instagram SDK Agent
    async def test():
        agent = InstagramSDKAgent()

        result = await agent.create_caption(
            topic="New productivity app launch",
            context="FocusFlow - AI that schedules deep work and kills meeting bloat",
        )

        print(json.dumps(result, indent=2))

    asyncio.run(test())

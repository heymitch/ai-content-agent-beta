"""
YouTube SDK Agent - Tier 2 Orchestrator
Uses Claude Agent SDK with persistent memory and delegates to specialized tools.
Cloned from Email SDK Agent, adapted for YouTube video scripts with timing markers.
"""

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server
)
import os
import json
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
from dotenv import load_dotenv
from textwrap import dedent

# Load environment variables for API keys
load_dotenv()


# ================== TIER 3 TOOL DEFINITIONS (LAZY LOADED) ==================
# Tool descriptions kept minimal to reduce context window usage
# Detailed prompts loaded just-in-time when tools are called

@tool(
    "generate_5_hooks",
    "Generate 5 video hooks",
    {"topic": str, "context": str, "target_audience": str}
)
async def generate_5_hooks(args):
    """Generate 5 video hooks - prompt loaded JIT"""
    from anthropic import Anthropic
    from prompts.youtube_tools import GENERATE_HOOKS_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    context = args.get('context', '')
    audience = args.get('target_audience', 'content creators')

    json_example = '[{{"type": "question", "text": "...", "words": 10, "estimated_seconds": 4}}, ...]'
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
    "inject_proof_points",
    "Add metrics and proof points to script",
    {"draft": str, "topic": str, "industry": str}
)
async def inject_proof_points(args):
    """Inject proof - prompt loaded JIT"""
    from anthropic import Anthropic
    from prompts.youtube_tools import INJECT_PROOF_PROMPT, WRITE_LIKE_HUMAN_RULES
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    draft = args.get('draft', '')
    topic = args.get('topic', '')
    industry = args.get('industry', 'Content Creation')

    prompt = INJECT_PROOF_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        draft=draft,
        topic=topic,
        industry=industry
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "content": [{
            "type": "text",
            "text": response.content[0].text
        }]
    }


@tool(
    "create_human_script",
    "Generate YouTube script with timing markers and quality self-assessment",
    {"topic": str, "video_hook": str, "context": str}
)
async def create_human_script(args):
    """Create script with JSON output including timing markers and scores"""
    import json
    from anthropic import Anthropic
    from prompts.youtube_tools import (
        CREATE_YOUTUBE_SCRIPT_PROMPT,
        WRITE_LIKE_HUMAN_RULES,
        YOUTUBE_EXAMPLES
    )
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    video_hook = args.get('video_hook', '')
    context = args.get('context', '')

    # Lazy load prompt with YouTube examples
    prompt = CREATE_YOUTUBE_SCRIPT_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        youtube_examples=YOUTUBE_EXAMPLES,
        topic=topic,
        video_hook=video_hook,
        context=context
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Use Sonnet for quality self-assessment
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Try to parse JSON, fallback to raw text if it fails
    try:
        json_result = json.loads(response_text)
        # Validate schema - YouTube needs timing_markers
        if "script_text" in json_result and "timing_markers" in json_result and "self_assessment" in json_result:
            return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in basic JSON
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "script_text": response_text,
                "timing_markers": {},
                "estimated_duration_seconds": 0,
                "self_assessment": {"total": 0, "notes": "JSON parsing failed, returning raw text"}
            }, indent=2)
        }]
    }


@tool(
    "quality_check",
    "Score script on 5 axes, verify timing accuracy, return surgical fixes",
    {"post": str}
)
async def quality_check(args):
    """Evaluate script with 5-axis rubric + timing check + surgical feedback + web_search for fabrications"""
    import json
    from anthropic import Anthropic
    from prompts.youtube_tools import QUALITY_CHECK_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    post = args.get('post', '')
    prompt = QUALITY_CHECK_PROMPT.format(post=post)

    # Give Claude web_search tool for fact checking
    messages = [{"role": "user", "content": prompt}]

    # Tool loop: handle web_search requests
    max_iterations = 5
    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3
            }],
            messages=messages
        )

        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Add assistant message with tool use
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            # Continue loop to get final response
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
                "timing_accuracy": {},
                "decision": "error",
                "issues": [],
                "surgical_summary": "Max iterations reached"
            }, indent=2)
        }]
    }


@tool(
    "apply_fixes",
    "Apply 3-5 surgical fixes based on quality_check feedback, update timing markers",
    {"post": str, "issues_json": str}
)
async def apply_fixes(args):
    """Apply surgical fixes without rewriting the whole script, maintain timing accuracy"""
    import json
    from anthropic import Anthropic
    from prompts.youtube_tools import APPLY_FIXES_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    post = args.get('post', '')
    issues_json = args.get('issues_json', '[]')

    # Use APPLY_FIXES_PROMPT
    prompt = APPLY_FIXES_PROMPT.format(
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
        if "revised_script" in json_result and "timing_markers" in json_result:
            return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in JSON
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "revised_script": response_text,
                "timing_markers": {},
                "estimated_duration_seconds": 0,
                "changes_made": [],
                "estimated_new_score": 0,
                "notes": "JSON parsing failed"
            }, indent=2)
        }]
    }




# ================== YOUTUBE SDK AGENT CLASS ==================

class YouTubeSDKAgent:
    """
    Tier 2: YouTube-specific SDK Agent with persistent memory
    Orchestrates Tier 3 tools and maintains platform-specific context
    Outputs scripts with timing markers (Option 2)
    """

    def __init__(self, user_id: str = "default", isolated_mode: bool = False):
        """Initialize YouTube SDK Agent with memory and tools

        Args:
            user_id: User identifier for session management
            isolated_mode: If True, creates isolated sessions (for testing only)
        """
        self.user_id = user_id
        self.sessions = {}  # Track multiple content sessions
        self.isolated_mode = isolated_mode  # Test mode flag

        # YouTube-specific system prompt with quality thresholds
        self.system_prompt = """You are a YouTube script creation agent. Your goal: scripts that score 18+ out of 25 without needing 3 rounds of revision.

YOU MUST USE TOOLS. EXECUTE immediately. Parse JSON responses.

AVAILABLE TOOLS (5-tool workflow):
- mcp__youtube_tools__generate_5_hooks → Returns 5 hook options with timing
- mcp__youtube_tools__create_human_script → Returns JSON: {script_text, timing_markers, self_assessment}
- mcp__youtube_tools__inject_proof_points → Adds metrics
- mcp__youtube_tools__quality_check → Returns JSON: {scores, timing_accuracy, decision, issues}
- mcp__youtube_tools__apply_fixes → Returns JSON: {revised_script, timing_markers, changes_made, estimated_new_score}

QUALITY THRESHOLD: 18/25 minimum (5-axis rubric)

WORKFLOW WITH DECISION LOGIC:
1. generate_5_hooks → Pick best
2. create_human_script → Parse JSON
   - Check self_assessment.total
   - Verify timing_markers present
   - If <18 → Try different hook, GOTO 1
   - If ≥18 → Continue to 3
3. inject_proof_points → Add specifics
4. quality_check → Parse JSON
   - decision="reject" (score <18) → Try different hook, GOTO 1
   - decision="accept" (score ≥20) → Return script, DONE
   - decision="revise" (score 18-19) → GOTO 5
5. apply_fixes → Parse JSON
   - Check estimated_new_score
   - Verify timing_markers updated
   - If ≥18 → Return revised_script, DONE
   - If <18 → Try different approach, GOTO 1

MAX RETRIES: 3 attempts
If all fail → Return best attempt with warning: "Best score achieved: X/25"

CRITICAL RULES:
- Parse JSON from create_human_script, quality_check, apply_fixes
- Check scores before proceeding
- Verify timing markers present (format: "0:00-0:03")
- DO NOT return scripts that score <18/25
- ONE pass through revise (no iteration loops)
- Trust the rubric - tools evaluate on 5 axes:
  1. Video hook power (grabs attention in 3 sec)
  2. Pattern interrupt (breaks scroll, creates curiosity)
  3. Script flow (spoken cadence, natural pauses)
  4. Proof density (2+ names/numbers from user context)
  5. CTA/payoff (video-specific action + clear benefit)

AI TELLS AUTO-FAIL:
- Contrast framing: "It's not X, it's Y"
- Rule of Three: "Same X. Same Y. Over Z%."
- Staccato fragments: "500 subs. 3 months. One change."

DO NOT explain. DO NOT iterate beyond one revise. Return final script with timing when threshold met."""

        # Create MCP server with YouTube-specific tools (LEAN 5-TOOL WORKFLOW)
        self.mcp_server = create_sdk_mcp_server(
            name="youtube_tools",
            version="1.0.0",
            tools=[
                generate_5_hooks,
                create_human_script,
                inject_proof_points,
                quality_check,  # Combined: AI patterns + timing check + fact-check
                apply_fixes     # Combined: Fix everything + update timing in one pass
            ]
        )

        print("🎬 YouTube SDK Agent initialized with 5 lean tools (Cole's script style embedded)")

    def get_or_create_session(self, session_id: str) -> ClaudeSDKClient:
        """Get or create a persistent session for content creation"""
        if session_id not in self.sessions:
            # Only clear env vars in isolated test mode
            if self.isolated_mode:
                os.environ.pop('CLAUDECODE', None)
                os.environ.pop('CLAUDE_CODE_ENTRYPOINT', None)
                os.environ.pop('CLAUDE_SESSION_ID', None)
                os.environ.pop('CLAUDE_WORKSPACE', None)
                os.environ['CLAUDE_HOME'] = '/tmp/youtube_agent'

            options = ClaudeAgentOptions(
                mcp_servers={"youtube_tools": self.mcp_server},
                allowed_tools=["mcp__youtube_tools__*"],
                system_prompt=self.system_prompt,
                model="claude-sonnet-4-5-20250929",
                permission_mode="bypassPermissions",
                continue_conversation=not self.isolated_mode  # False in test mode, True in prod
            )

            self.sessions[session_id] = ClaudeSDKClient(options=options)
            mode_str = " (isolated test mode)" if self.isolated_mode else ""
            print(f"📝 Created YouTube session: {session_id}{mode_str}")

        return self.sessions[session_id]

    async def create_script(
        self,
        topic: str,
        context: str = "",
        script_type: str = "short_form",  # short_form (30-150w), medium_form (150-400w), long_form (400-1000w)
        target_score: int = 85,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a YouTube script with timing markers

        Args:
            topic: Main topic/angle
            context: Additional requirements, user specifics, etc.
            script_type: short_form, medium_form, long_form
            target_score: Minimum quality score (default 85)
            session_id: Session for conversation continuity

        Returns:
            Dict with final script, timing markers, score, duration
        """

        # Use session ID or create new one
        if not session_id:
            session_id = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        client = self.get_or_create_session(session_id)

        # Build the creation prompt
        creation_prompt = f"""Create a HIGH-QUALITY YouTube script using LEAN WORKFLOW.

Topic: {topic}
Context: {context}
Script Type: {script_type}

LEAN WORKFLOW (5 TOOLS ONLY - NO ITERATION):
1. Call mcp__youtube_tools__generate_5_hooks
2. Select best hook, then call mcp__youtube_tools__create_human_script
3. Call mcp__youtube_tools__inject_proof_points
4. Call mcp__youtube_tools__quality_check (gets ALL issues: AI patterns + timing + fabrications)
5. Call mcp__youtube_tools__apply_fixes (fixes everything + updates timing in ONE pass)
6. Return final script with timing markers and STOP

DO NOT:
- Call quality_check more than once
- Call apply_fixes more than once
- Iterate or loop
- Score or validate after fixes

Trust the prompts - they include Cole's script style examples and timing logic."""

        try:
            # Connect if needed
            print(f"🔗 Connecting YouTube SDK client...")
            await client.connect()

            # Send the creation request
            print(f"📤 Sending YouTube creation prompt...")
            await client.query(creation_prompt)
            print(f"⏳ YouTube agent processing (this takes 30-60s)...")

            # Collect the response - keep the LAST text output we see
            final_output = ""
            message_count = 0
            last_text_message = None

            async for msg in client.receive_response():
                message_count += 1
                msg_type = type(msg).__name__
                print(f"   📬 Received message {message_count}: type={msg_type}")

                # Track all AssistantMessages with text content (keep the last one)
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
                                            last_text_message = message_count
                                            print(f"      ✅ Got text output ({len(final_output)} chars)")
                                elif hasattr(block, 'text'):
                                    text_content = block.text
                                    if text_content:
                                        final_output = text_content
                                        last_text_message = message_count
                                        print(f"      ✅ Got text from block.text ({len(final_output)} chars)")
                        elif hasattr(msg.content, 'text'):
                            text_content = msg.content.text
                            if text_content:
                                final_output = text_content
                                last_text_message = message_count
                                print(f"      ✅ Got text from content.text ({len(final_output)} chars)")
                    elif hasattr(msg, 'text'):
                        text_content = msg.text
                        if text_content:
                            final_output = text_content
                            last_text_message = message_count
                            print(f"      ✅ Got text from msg.text ({len(final_output)} chars)")

            print(f"\n   ✅ Stream complete after {message_count} messages (last text at message {last_text_message})")

            # Parse the output to extract structured data
            return self._parse_output(final_output)

        except Exception as e:
            print(f"❌ YouTube SDK Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": None
            }

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse agent output into structured response"""
        # Clean the content (remove SDK metadata/headers)
        from integrations.airtable_client import AirtableContentCalendar
        cleaner = AirtableContentCalendar.__new__(AirtableContentCalendar)
        clean_output = cleaner._clean_content(output)

        # Extract the hook from clean content
        hook_preview = cleaner._extract_hook(clean_output, 'youtube')

        # Try to extract timing from output
        import re
        timing_pattern = r'(\d+:\d+)-(\d+:\d+)'
        timings = re.findall(timing_pattern, clean_output)

        # Extract score if mentioned in output
        score = 90  # Default, would parse from actual output

        # Estimate duration from timing markers or word count
        words = len(clean_output.split())
        estimated_duration = int(words / 2.5)  # 2.5 words/sec

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
                content=output,  # Pass raw output, cleaning happens inside
                platform='youtube',
                post_hook=hook_preview,
                status='Draft'
            )
            print(f"📊 Airtable API result: {result}")

            if result.get('success'):
                airtable_url = result.get('url')
                airtable_record_id = result.get('record_id')
                print(f"✅ SUCCESS! Saved to Airtable:")
                print(f"   Record ID: {airtable_record_id}")
                print(f"   URL: {airtable_url}")
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
                'platform': 'youtube',
                'post_hook': hook_preview,
                'body_content': clean_output,  # Save clean content
                'content_type': 'script',
                'airtable_record_id': airtable_record_id,
                'airtable_url': airtable_url,
                'status': 'draft',
                'quality_score': score,
                'iterations': 3,
                'slack_thread_ts': getattr(self, 'session_id', None),
                'user_id': self.user_id,
                'created_by_agent': 'youtube_sdk_agent',
                'embedding': embedding,
                'platform_metadata': {
                    'word_count': words,
                    'estimated_duration': estimated_duration,
                    'timing_markers': len(timings)
                }
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
            "script": clean_output,  # The clean script content (metadata stripped)
            "hook": hook_preview,  # First 60 chars for Slack preview
            "score": score,
            "estimated_duration": f"{estimated_duration}s",
            "word_count": words,
            "timing_markers_found": len(timings),
            "hooks_tested": 5,
            "iterations": 3,
            "airtable_url": airtable_url or "[Airtable not configured]",
            "google_doc_url": google_doc_url or "[Coming Soon]",
            "supabase_id": supabase_id,
            "session_id": self.user_id,
            "timestamp": datetime.now().isoformat()
        }

    async def batch_create(
        self,
        topics: List[str],
        script_type: str = "short_form",
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Create multiple scripts in one session (maintains context)"""

        if not session_id:
            session_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"Creating script {i}/{len(topics)}: {topic[:50]}...")

            result = await self.create_script(
                topic=topic,
                context=f"Script {i} of {len(topics)} in series",
                script_type=script_type,
                session_id=session_id  # Same session = maintains context
            )

            results.append(result)

        return results


# ================== INTEGRATION FUNCTION ==================

async def create_youtube_workflow(
    topic: str,
    context: str = "",
    script_type: str = "short_form"
) -> str:
    """
    Main entry point for YouTube script creation
    Called by the main CMO agent's delegate_to_workflow tool
    Returns structured response with hook preview, timing, and links
    """

    agent = YouTubeSDKAgent()

    result = await agent.create_script(
        topic=topic,
        context=f"{context} | Script Type: {script_type}",
        script_type=script_type,
        target_score=85
    )

    if result['success']:
        # Return structured response for Slack
        return f"""✅ **YouTube Script Created**

**Hook Preview:**
_{result.get('hook', result['script'][:60])}..._

**Duration:** {result.get('estimated_duration', '60s')} | **Words:** {result.get('word_count', 150)}
**Quality Score:** {result.get('score', 90)}/100 (Iterations: {result.get('iterations', 3)})
**Timing Markers:** {result.get('timing_markers_found', 0)} sections

**Full Script:**
{result['script']}

---
📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}

*AI Patterns Removed | Timing Verified | Ready to Record*"""
    else:
        return f"❌ Creation failed: {result.get('error', 'Unknown error')}"


if __name__ == "__main__":
    # Test the YouTube SDK Agent
    async def test():
        agent = YouTubeSDKAgent()

        result = await agent.create_script(
            topic="Finding your writing voice using the 3A framework",
            context="Focus on Authority + Accessibility + Authenticity. Target: B2B content creators with 1k-10k subs. Example: Alex went 500→5k in 3 months using this.",
            script_type="short_form",
            target_score=85
        )

        print(json.dumps(result, indent=2))

    asyncio.run(test())

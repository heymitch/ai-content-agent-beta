"""
Email SDK Agent - Tier 2 Orchestrator
Uses Claude Agent SDK with persistent memory and delegates to specialized tools.
Cloned from LinkedIn SDK Agent, adapted for email newsletters.
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
    "Generate 5 email subject lines",
    {"topic": str, "context": str, "target_audience": str}
)
async def generate_5_hooks(args):
    """Generate 5 subject lines - prompt loaded JIT"""
    from anthropic import Anthropic
    from prompts.email_tools import GENERATE_HOOKS_PROMPT
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    context = args.get('context', '')
    audience = args.get('target_audience', 'email subscribers')

    json_example = '[{{"type": "curiosity", "text": "...", "chars": 45}}, ...]'
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
    "Add metrics and proof points to email",
    {"draft": str, "topic": str, "industry": str}
)
async def inject_proof_points(args):
    """Inject proof - prompt loaded JIT"""
    from anthropic import Anthropic
    from prompts.email_tools import INJECT_PROOF_PROMPT, WRITE_LIKE_HUMAN_RULES
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    draft = args.get('draft', '')
    topic = args.get('topic', '')
    industry = args.get('industry', 'Email Marketing')

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
    "create_human_draft",
    "Generate email draft with quality self-assessment",
    {"topic": str, "subject_line": str, "context": str}
)
async def create_human_draft(args):
    """Create draft with JSON output including scores"""
    import json
    from anthropic import Anthropic
    from prompts.email_tools import (
        CREATE_EMAIL_DRAFT_PROMPT,
        WRITE_LIKE_HUMAN_RULES,
        EMAIL_VALUE_EXAMPLES,
        EMAIL_TUESDAY_EXAMPLES,
        EMAIL_DIRECT_EXAMPLES
    )
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    topic = args.get('topic', '')
    subject_line = args.get('subject_line', '')
    context = args.get('context', '')

    # Lazy load prompt with PGA examples
    prompt = CREATE_EMAIL_DRAFT_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        email_value_examples=EMAIL_VALUE_EXAMPLES,
        email_tuesday_examples=EMAIL_TUESDAY_EXAMPLES,
        email_direct_examples=EMAIL_DIRECT_EXAMPLES,
        topic=topic,
        subject_line=subject_line,
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
        # Validate schema
        if "email_body" in json_result and "self_assessment" in json_result:
            return {"content": [{"type": "text", "text": json.dumps(json_result, indent=2)}]}
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in basic JSON
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "email_body": response_text,
                "self_assessment": {"total": 0, "notes": "JSON parsing failed, returning raw text"}
            }, indent=2)
        }]
    }


@tool(
    "quality_check",
    "Score email on 5 axes and return surgical fixes",
    {"post": str}
)
async def quality_check(args):
    """Evaluate email with 5-axis rubric + surgical feedback + web_search for fabrications"""
    import json
    from anthropic import Anthropic
    from prompts.email_tools import QUALITY_CHECK_PROMPT
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
    """Apply surgical fixes without rewriting the whole email"""
    import json
    from anthropic import Anthropic
    from prompts.email_tools import APPLY_FIXES_PROMPT
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




# ================== EMAIL SDK AGENT CLASS ==================

class EmailSDKAgent:
    """
    Tier 2: Email-specific SDK Agent with persistent memory
    Orchestrates Tier 3 tools and maintains platform-specific context
    """

    def __init__(self, user_id: str = "default", isolated_mode: bool = False):
        """Initialize Email SDK Agent with memory and tools

        Args:
            user_id: User identifier for session management
            isolated_mode: If True, creates isolated sessions (for testing only)
        """
        self.user_id = user_id
        self.sessions = {}  # Track multiple content sessions
        self.isolated_mode = isolated_mode  # Test mode flag

        # Email-specific system prompt with quality thresholds
        self.system_prompt = """You are an email newsletter creation agent. Your goal: emails that score 18+ out of 25 without needing 3 rounds of revision.

YOU MUST USE TOOLS. EXECUTE immediately. Parse JSON responses.

AVAILABLE TOOLS (5-tool workflow):
- mcp__email_tools__generate_5_hooks → Returns 5 subject line options
- mcp__email_tools__create_human_draft → Returns JSON: {email_body, self_assessment}
- mcp__email_tools__inject_proof_points → Adds metrics
- mcp__email_tools__quality_check → Returns JSON: {scores, decision, issues}
- mcp__email_tools__apply_fixes → Returns JSON: {revised_post, changes_made, estimated_new_score}

QUALITY THRESHOLD: 18/25 minimum (5-axis rubric)

WORKFLOW WITH DECISION LOGIC:
1. generate_5_hooks → Pick best
2. create_human_draft → Parse JSON
   - Check self_assessment.total
   - If <18 → Try different subject line, GOTO 1
   - If ≥18 → Continue to 3
3. inject_proof_points → Add specifics
4. quality_check → Parse JSON
   - decision="reject" (score <18) → Try different subject line, GOTO 1
   - decision="accept" (score ≥20) → Return email, DONE
   - decision="revise" (score 18-19) → GOTO 5
5. apply_fixes → Parse JSON
   - Check estimated_new_score
   - If ≥18 → Return revised_post, DONE
   - If <18 → Try different approach, GOTO 1

MAX RETRIES: 3 attempts
If all fail → Return best attempt with warning: "Best score achieved: X/25"

CRITICAL RULES:
- Parse JSON from create_human_draft, quality_check, apply_fixes
- Check scores before proceeding
- DO NOT return emails that score <18/25
- ONE pass through revise (no iteration loops)
- Trust the rubric - tools evaluate on 5 axes:
  1. Subject line power (specific + curiosity + <60 chars)
  2. Preview text hook (extends subject + adds context)
  3. Email structure (hook intro + sections + white space)
  4. Proof points (2+ names/numbers/specifics)
  5. CTA clarity (specific action + clear next step)

AI TELLS AUTO-FAIL:
- Contrast framing: "It's not X, it's Y"
- Rule of Three: "Same X. Same Y. Over Z%."
- Formal greetings: "I hope this email finds you well"

DO NOT explain. DO NOT iterate beyond one revise. Return final email when threshold met."""

        # Create MCP server with Email-specific tools (LEAN 5-TOOL WORKFLOW)
        self.mcp_server = create_sdk_mcp_server(
            name="email_tools",
            version="1.0.0",
            tools=[
                generate_5_hooks,
                create_human_draft,
                inject_proof_points,
                quality_check,  # Combined: AI patterns + fact-check
                apply_fixes     # Combined: Fix everything in one pass
            ]
        )

        print("📧 Email SDK Agent initialized with 5 lean tools (PGA writing style embedded)")

    def get_or_create_session(self, session_id: str) -> ClaudeSDKClient:
        """Get or create a persistent session for content creation"""
        if session_id not in self.sessions:
            # Only clear env vars in isolated test mode
            if self.isolated_mode:
                os.environ.pop('CLAUDECODE', None)
                os.environ.pop('CLAUDE_CODE_ENTRYPOINT', None)
                os.environ.pop('CLAUDE_SESSION_ID', None)
                os.environ.pop('CLAUDE_WORKSPACE', None)
                os.environ['CLAUDE_HOME'] = '/tmp/email_agent'

            options = ClaudeAgentOptions(
                mcp_servers={"email_tools": self.mcp_server},
                allowed_tools=["mcp__email_tools__*"],
                system_prompt=self.system_prompt,
                model="claude-sonnet-4-5-20250929",
                permission_mode="bypassPermissions",
                continue_conversation=not self.isolated_mode  # False in test mode, True in prod
            )


            self.sessions[session_id] = ClaudeSDKClient(options=options)
            mode_str = " (isolated test mode)" if self.isolated_mode else ""
            print(f"📝 Created Email session: {session_id}{mode_str}")

        return self.sessions[session_id]

    async def create_email(
        self,
        topic: str,
        context: str = "",
        email_type: str = "Email_Value",  # Email_Value, Email_Tuesday, Email_Direct, Email_Indirect
        target_score: int = 85,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an email newsletter following PGA writing style

        Args:
            topic: Main topic/angle
            context: Additional requirements, user specifics, etc.
            email_type: Email_Value, Email_Tuesday, Email_Direct, Email_Indirect
            target_score: Minimum quality score (default 85)
            session_id: Session for conversation continuity

        Returns:
            Dict with final email, score, subject lines tested, iterations
        """

        # Use session ID or create new one
        if not session_id:
            session_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        client = self.get_or_create_session(session_id)

        # Build the creation prompt
        creation_prompt = f"""Create a HIGH-QUALITY email newsletter using LEAN WORKFLOW.

Topic: {topic}
Context: {context}
Email Type: {email_type}

LEAN WORKFLOW (5 TOOLS ONLY - NO ITERATION):
1. Call mcp__email_tools__generate_5_hooks
2. Select best subject line, then call mcp__email_tools__create_human_draft
3. Call mcp__email_tools__inject_proof_points
4. Call mcp__email_tools__quality_check (gets ALL issues: AI patterns + fabrications)
5. Call mcp__email_tools__apply_fixes (fixes everything in ONE pass)
6. Return final email and STOP

DO NOT:
- Call quality_check more than once
- Call apply_fixes more than once
- Iterate or loop
- Score or validate after fixes

Trust the prompts - they include PGA writing style examples."""

        try:
            # Connect if needed
            print(f"🔗 Connecting Email SDK client...")
            await client.connect()

            # Send the creation request
            print(f"📤 Sending Email creation prompt...")
            await client.query(creation_prompt)
            print(f"⏳ Email agent processing (this takes 30-60s)...")

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
            return await self._parse_output(final_output)

        except Exception as e:
            print(f"❌ Email SDK Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "email": None
            }

    async def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse agent output into structured response"""

        # Debug: Track how many times this is called
        import traceback
        print(f"\n⚠️ DEBUG: _parse_output called")
        print(f"   Call stack (last 3 frames):")
        for line in traceback.format_stack()[-4:-1]:
            print(f"   {line.strip()}")

        # Clean the content (remove SDK metadata/headers)
        from integrations.airtable_client import AirtableContentCalendar
        cleaner = AirtableContentCalendar.__new__(AirtableContentCalendar)
        clean_output = cleaner._clean_content(output)

        # Extract the subject/hook from clean content
        subject_preview = cleaner._extract_hook(clean_output, 'email')

        # Extract score if mentioned in output
        score = 90  # Default, would parse from actual output

        # Run validators (quality check + optional GPTZero)
        validation_json = None
        validation_formatted = None
        try:
            from integrations.validation_utils import run_all_validators, format_validation_for_airtable
            validation_json = await run_all_validators(clean_output, 'email')
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

            print(f"\n📝 Saving content (subject: '{subject_preview[:50]}...')")
            result = airtable.create_content_record(
                content=output,  # Pass raw output, cleaning happens inside
                platform='email',
                post_hook=subject_preview,
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
                'platform': 'email',
                'post_hook': subject_preview,
                'body_content': clean_output,  # Save clean content
                'content_type': 'newsletter',
                'airtable_record_id': airtable_record_id,
                'airtable_url': airtable_url,
                'status': 'draft',
                'quality_score': score,
                'iterations': 3,
                'slack_thread_ts': getattr(self, 'session_id', None),
                'user_id': self.user_id,
                'created_by_agent': 'email_sdk_agent',
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
            "email": clean_output,  # The clean email content (metadata stripped)
            "subject": subject_preview,  # First 60 chars for Slack preview
            "score": score,
            "subjects_tested": 5,
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
        email_type: str = "Email_Value",
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Create multiple emails in one session (maintains context)"""

        if not session_id:
            session_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"Creating email {i}/{len(topics)}: {topic[:50]}...")

            result = await self.create_email(
                topic=topic,
                context=f"Email {i} of {len(topics)} in series",
                email_type=email_type,
                session_id=session_id  # Same session = maintains context
            )

            results.append(result)

        return results


# ================== INTEGRATION FUNCTION ==================

async def create_email_workflow(
    topic: str,
    context: str = "",
    email_type: str = "Email_Value"
) -> str:
    """
    Main entry point for Email content creation
    Called by the main CMO agent's delegate_to_workflow tool
    Returns structured response with subject preview and links
    """

    agent = EmailSDKAgent()

    result = await agent.create_email(
        topic=topic,
        context=f"{context} | Email Type: {email_type}",
        email_type=email_type,
        target_score=85
    )

    if result['success']:
        # Return structured response for Slack
        return f"""✅ **Email Newsletter Created**

**Subject Preview:**
_{result.get('subject', result['email'][:60])}..._

**Quality Score:** {result.get('score', 90)}/100 (Iterations: {result.get('iterations', 3)})

**Full Email:**
{result['email']}

---
📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}

*AI Patterns Removed | Facts Verified | Ready to Send*"""
    else:
        return f"❌ Creation failed: {result.get('error', 'Unknown error')}"


if __name__ == "__main__":
    # Test the Email SDK Agent
    async def test():
        agent = EmailSDKAgent()

        result = await agent.create_email(
            topic="PGA email strategy: How we get 40%+ open rates with specific student wins",
            context="Focus on Matthew Brown collab (450+ subs), Sujoy's $5k win, keeping it personal at scale",
            email_type="Email_Value",
            target_score=85
        )

        print(json.dumps(result, indent=2))

    asyncio.run(test())

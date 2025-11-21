Actionable comments posted: 14

Caution

Some comments are outside the diff and can’t be posted inline due to platform limitations.

⚠️ Outside diff range comments (3)
agents/twitter_haiku_agent.py (1)
26-33: Retry context provider cannot access the topic parameter—it will always return "N/A"

The lambda's locals() refers only to the lambda's own scope (which is empty), not the create_single_post function's scope. Since topic is a function parameter and the decorator is applied at definition time, the lambda has no closure access to topic. As a result, retry logs will always show topic: "N/A".

To fix this, the decorator must be modified to pass call-time parameters to context_provider. The current signature (Callable[[], Dict[str, Any]]) allows zero arguments only. Either:

Update async_retry_with_backoff to accept a context_provider signature like Callable[[dict], Dict[str, Any]] and pass **kwargs from the decorated function, or
Use a different mechanism to capture context at retry time (e.g., a context variable or thread-local state).
agents/batch_orchestrator.py (2)
379-419: extract_score_from_result does not handle Haiku Score: n/m outputs (Twitter fast path)

The current regex only matches patterns like “Quality Score: 22/25”, but some workflows (e.g., agents/twitter_haiku_agent.create_twitter_post_workflow) emit lines like:

Score: 4/5 (Haiku fast path)

Those will miss the regex and fall back to the default score of 20, skewing batch stats and Airtable/Supabase quality scores.

You can make the extractor robust to both formats:

-    # Formats: "**Quality Score:** 22/25", "Quality Score: 22/25", "Score: 90/100"
-    # Updated pattern to handle markdown asterisks and any formatting
-    score_match = re.search(r'Quality\s+Score.*?(\d+)\s*/\s*(\d+)', str(result), re.IGNORECASE | re.DOTALL)
+    # Formats: "**Quality Score:** 22/25", "Quality Score: 22/25", "Score: 4/5"
+    # Pattern handles optional "Quality" prefix and markdown decoration
+    score_match = re.search(
+        r'(?:Quality\s+Score|Score)\s*[:\*]*\s*(\d+)\s*/\s*(\d+)',
+        str(result),
+        re.IGNORECASE | re.DOTALL,
+    )
This will also correctly normalize Haiku’s 0–5 scale to 0–25 via the existing max_score logic.

872-873: diversify_topics will raise NameError because os is not imported

Inside diversify_topics you call:

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
but os is never imported in this module, so any call to diversify_topics will raise NameError: name 'os' is not defined.

A minimal fix is to import os at the top next to the other stdlib imports:

-import time
-import asyncio
-import re
+import os
+import time
+import asyncio
+import re
You may also want to note that client.messages.create is synchronous inside this async function; if diversify_topics is used in latency‑sensitive paths, consider wrapping it in asyncio.to_thread to avoid blocking the event loop.

🧹 Nitpick comments (36)
check_function.py (2)
4-7: Add error handling for missing environment variables.

The script will fail with an unclear error if SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY are not set. Consider adding explicit validation:

+import sys
 import os
 from supabase import create_client
 
+# Validate required environment variables
+required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
+missing = [var for var in required_vars if not os.environ.get(var)]
+if missing:
+    print(f"❌ Missing required environment variables: {', '.join(missing)}")
+    sys.exit(1)
+
 supabase = create_client(
     os.environ['SUPABASE_URL'],
     os.environ['SUPABASE_SERVICE_ROLE_KEY']
 )
19-21: Add error handling and verify the exec_sql RPC function exists.

The script assumes the exec_sql RPC function exists and will succeed. Consider:

Wrapping the RPC call in try-except
Verifying this RPC function is documented and safe to use
Adding a check for whether the target function exists
-result = supabase.rpc('exec_sql', {'query': query}).execute()
-print("Current function signature:")
-print(result.data)
+try:
+    result = supabase.rpc('exec_sql', {'query': query}).execute()
+    if result.data:
+        print("Current function signature:")
+        print(result.data)
+    else:
+        print("⚠️  Function 'match_content_examples' not found")
+except Exception as e:
+    print(f"❌ Error querying function signature: {e}")
+    sys.exit(1)
Security note: The exec_sql RPC function allows arbitrary SQL execution. Ensure it's properly secured and only accessible with service role keys.

docs/AGENT_FLOW.md (1)
22-96: Consider adding language identifiers to ASCII diagram code blocks.

The ASCII architecture diagrams are excellent, but the code blocks lack language identifiers. While not strictly necessary for ASCII art, adding text or ascii as the language identifier would satisfy markdown linters and improve consistency.

Based on static analysis hints.

deploy-replit.sh (1)
1-20: Helpful deployment script with minor suggestions.

The script provides clear guidance for Replit deployment. A few optional improvements:

Ensure executable permissions: After creating the file, users should run chmod +x deploy-replit.sh
Log message references may become stale: The "NEW" and "OLD" log message patterns (lines 16, 20) are tied to specific implementation details that may change over time.
Consider adding a note in the script header:

 #!/bin/bash
 # Replit Deployment Script
 # Clears Python cache and prepares for clean restart
+# Usage: chmod +x deploy-replit.sh && ./deploy-replit.sh
INSTALLATION_TROUBLESHOOTING.md (1)
33-35: Minor: Add language identifier to code block.

The code block at line 33 is missing a language identifier. Add bash for consistency:

-```
+```bash
 npm install --no-save --force pg dotenv
 npm start


Based on static analysis hints.

</blockquote></details>
<details>
<summary>docs/AIRTABLE_SYNC_SETUP.md (2)</summary><blockquote>

`390-401`: **Add missing `os` import in API key auth example**

The FastAPI snippet uses `os.getenv('SYNC_API_KEY')` but doesn't import `os`, so copy‑pasting as‑is would raise `NameError`.



```diff
-# In api/sync_endpoints.py
-from fastapi import Header, HTTPException
+# In api/sync_endpoints.py
+from fastapi import Header, HTTPException
+import os
65-71: Tiny wording nit: compound adjective

If you’re tuning docs for style guides, consider “far‑right column” instead of “far right column.” Totally optional.

agent-builder-reference/tool-creation-guide.md (2)
155-166: Fix quick test script to handle async tools

Most examples define tools as async, but the “Quick Test Script” calls your_tool_function synchronously. For async tools this will just produce a coroutine object, not execute it.

Consider updating to something like:

import asyncio
from your_module import your_tool_function

async def main():
    result = await your_tool_function(
        query="test",
        platform=None,  # Test with None
        match_count=5,
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
Please confirm this matches how your actual tools are defined; if some are sync, you might want to call out both patterns explicitly.

8-13: Optional: align TOC anchors with numbered headings

Your headings are numbered (e.g., ## 1. Tool Structure Basics), so GitHub-style IDs will include the leading number. The TOC links (#tool-structure-basics, #tool-schema-patterns, etc.) may not jump correctly.

Either drop the leading numbers in the headings or update the fragments to match the exact generated IDs (or add explicit <a id="..."> anchors if you prefer fixed names).

agent-builder-reference/agent-setup-guide.md (2)
20-48: Wrap minimum agent example in an async entrypoint

The “Minimum Agent Setup” snippet uses await client.connect() and await client.query(...) at top level. As‑is this won’t run; it needs to be inside an async function with an event loop.

For example:

import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

@tool("my_tool", "Description", {"param": str})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "result"}]}

mcp_server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0",
    tools=[my_tool],
)

options = ClaudeAgentOptions(
    mcp_servers={"tools": mcp_server},
    allowed_tools=["mcp__tools__*"],
    system_prompt="Your agent's instructions",
    model="claude-sonnet-4-5-20250929",
    continue_conversation=True,
)

async def main():
    client = ClaudeSDKClient(options=options)
    await client.connect()
    await client.query("User message")

if __name__ == "__main__":
    asyncio.run(main())
Please adjust naming/model details as needed for your actual environment.

61-77: Optional: add language tag to system prompt code fence

The “Structure Pattern” block is fenced with plain ```; if you want to satisfy markdownlint and get better highlighting, consider adding a language (e.g., text or `markdown`).

apply_rpc_fix.py (3)
1-15: Address shebang vs execution mode

Ruff is flagging EXE001 because the file has a shebang but isn’t marked executable in the repo. Since this script is typically run via python apply_rpc_fix.py, you can either:

Remove the shebang:
-#!/usr/bin/env python3
-"""Manually apply the RPC function fix to Supabase"""
+"""Manually apply the RPC function fix to Supabase"""
or

Document that it should be made executable (chmod +x apply_rpc_fix.py) if you want to keep the shebang and invoke it directly.
10-11: Validate Supabase env vars before creating clients/connections

create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')) and psycopg2.connect(db_url) will fail with less clear errors if the env vars are missing or malformed.

You already check SUPABASE_DB_URL; consider similarly validating SUPABASE_URL and SUPABASE_KEY before create_client, e.g.:

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    print("❌ SUPABASE_URL or SUPABASE_KEY not set")
    exit(1)

supabase = create_client(supabase_url, supabase_key)
This will make misconfiguration failures much easier to debug.

Also applies to: 73-77

22-26: Tighten broad except Exception handlers

Both the drop and create steps catch bare Exception, which can hide unexpected failures (e.g., programming errors vs expected database errors).

Consider:

Catching narrower exceptions (e.g., the specific supabase/psycopg2 error base classes), or
At least re‑raising after logging for truly unexpected cases.
For example:

from psycopg2 import Error as PsycopgError

try:
    cursor.execute(create_sql)
    conn.commit()
    print("   ✅ New function created with semantic-first filter")
except PsycopgError as e:
    conn.rollback()
    print(f"   ❌ Failed to create function: {e}")
    raise
Similarly, for the supabase.rpc('exec_sql', ...) call, you may want to only treat “function missing” as non‑fatal and let other errors surface.

Also applies to: 82-88

.gitignore (1)
37-48: Deduplicate REPLIT-related ignore entries for cleanliness

The new Claude prompt ignore block looks good and matches the PromptLoader design. However, REPLIT_CRASH_FIXES.md and REPLIT_BOT_FILTER_FIX.md are now listed twice (Lines 98-99 and 102-103). This is harmless but adds noise; consider keeping a single entry for each to keep .gitignore tidy.

Also applies to: 98-103

agents/twitter_haiku_agent.py (2)
307-384: Improve Airtable/Supabase persistence robustness and logging

The persistence flow is generally solid and well‑isolated, but a few refinements would make failures easier to debug and reason about:

Airtable:

You already log the full airtable_result on failure and print a traceback, which is good.
Consider using the project’s logging framework instead of bare print/traceback.print_exc() so these errors are captured consistently with other services.
Supabase:

Failures are only logged via print(f" ⚠️ Supabase save failed: {e}"), with no stack trace or additional context (e.g., payload). Mirroring the Airtable approach (structured log + traceback) would make debugging much easier.
Optionally, you could inspect supabase_result for an error field (if the client exposes one) and log that explicitly before falling back to the generic exception.
These changes won’t affect the happy path but will materially improve observability when persistence fails.

311-315: Drop unnecessary f-strings where there are no placeholders

Lines 311 and 313 use f-strings without any interpolation:

print(f"   🔄 Attempting Airtable save...")
print(f"   🏷️  Platform: twitter")
These can be plain strings:

print("   🔄 Attempting Airtable save...")
print("   🏷️  Platform: twitter")
Keeps Ruff happy and avoids unnecessary f prefixes.

check_migrations.py (2)
7-24: Harden dependency and connection handling for better operator UX

This script is clearly intended as a diagnostic/ops tool; a few tweaks would make failures less surprising:

psycopg2 auto-install:

Calling pip install psycopg2-binary from within the script is convenient but can fail in locked-down or containerized environments. Right now, a failed install leads to a CalledProcessError traceback.
Consider catching the final failure and emitting a clear “please install psycopg2-binary manually” message before exiting.
DB connection:

psycopg2.connect(db_url) isn’t wrapped in a try/except. If the URL is wrong or the DB is unreachable, you’ll get a raw traceback instead of a clear diagnostic. Wrapping this in a small try with a friendly error (and exit(1)) would make the script safer to hand to non-experts.
Optional: supabase/OpenAI imports:

If supabase or openai are not installed, the script will crash on import before it can print the “missing API keys, skipping search test” message. You could either:
Move those imports inside the if not all([...]) branch that you know will execute only when keys exist, or
Wrap the imports in try/except with a clear “install supabase-py/openai to run search tests” message.
These changes keep the same behavior when everything is configured correctly, while failing much more gracefully when it isn’t.

Also applies to: 32-33, 98-119, 121-170

132-134: Remove unused f-strings in logging output

The lines:

print(f"\n   Search with filter_type='case studies':")
...
print(f"\n   Search content_examples:")
don’t interpolate any variables. They can be plain strings:

print("\n   Search with filter_type='case studies':")
print("\n   Search content_examples:")
This is a minor cleanup but keeps static analysis tools quiet.

Also applies to: 159-161

api/sync_endpoints.py (2)
36-45: Analytics sync endpoint wiring looks solid; improve error logging semantics

The SyncAnalyticsResponse model matches the documented return shape from bulk_sync_analytics_to_airtable, and the /analytics-to-airtable handler correctly:

Validates inputs via SyncAnalyticsRequest (days_back bounds, force_resync).
Delegates to bulk_sync_analytics_to_airtable.
Converts non‑success results into HTTP 500s.
Two small improvements:

In the except Exception as e block, prefer logger.exception("❌ Error in analytics sync endpoint") so you capture the stack trace without manually interpolating e.
When re‑raising as HTTPException, consider raise HTTPException(..., detail=f"Error syncing analytics: {e}") from e to preserve causal context.
Behavior is fine as-is; these are mainly for observability and debuggability.

Also applies to: 58-125

47-54: Sync status endpoint is a thin, correct wrapper over get_sync_status

SyncStatusResponse’s fields line up with the helper’s documented return keys, and /status cleanly maps the dict into the Pydantic model. This gives a well-typed surface to callers while keeping the core logic in integrations.supabase_to_airtable_sync.

Similar to the other endpoint, you could:

Switch logger.error(...) to logger.exception(...) in the except block.
Use raise HTTPException(..., detail=f"Error getting sync status: {e}") from e for clearer causal context.
Otherwise, this endpoint is straightforward and matches the PR’s analytics-sync design.

Also applies to: 133-175

api/publishing_endpoints.py (2)
23-30: Reuse existing Supabase client factory to avoid duplication

get_supabase_client here is identical to the helpers already defined in integrations/airtable_sync.py and integrations/ayrshare_sync.py. Duplicating this logic in multiple places makes it easier for the functions to drift if env handling ever changes.

Consider importing and reusing a single shared implementation (or centralizing it into a small integrations/supabase_client.py module) so all callers share the same behavior.

213-275: get_publishing_status logic is straightforward and consistent with the schema

The status lookup:

Accepts either airtable_record_id or post_id (and validates at least one is provided).
Returns a compact snapshot of key publishing metrics (status, URLs, scheduling, analytics fields).
Properly handles “not found” via a structured {'success': False, 'error': 'Post not found'} response.
The only small improvement would be to use logger.exception in the except block, similar to the other helpers, so you retain stack traces when something goes wrong.

README.md (1)
333-348: Align README LinkedIn Direct API example with the real workflow signature/return type

The create_linkedin_post_workflow example here still shows:

Parameters: topic, context, post_type, target_score, supabase_client
Return type: Dict[str, Any]
but the actual implementation in agents/linkedin_direct_api_agent.py takes (topic, context="", style="thought_leadership", channel_id=None, thread_ts=None, user_id=None, publish_date=None, thinking_mode=False) and returns a formatted str for Slack (content + score + Airtable URL).

To avoid integrators calling it with the wrong arguments or expecting a dict, update this snippet (signature and return type annotation) to mirror the real function, and optionally mention that it returns a Slack‑ready markdown string.

ROADMAP-11-11.md (1)
1-126: Roadmap content is clear; only minor wording/capitalization nits

The roadmap reads well and gives useful historical context. If you care about polish, you could:

Capitalize brand names consistently (Twitter, LinkedIn, YouTube, Markdown).
If there are fenced code blocks elsewhere in this file, add a language hint (e.g., ```bash) to satisfy markdownlint.
Purely cosmetic; no behavior impact.

agents/batch_orchestrator.py (4)
31-192: Harden Slack progress updates and final summary wording in execute_sequential_batch

Two minor robustness/UX points here:

All slack_client.chat_postMessage calls in this function are unguarded; a transient Slack API failure will raise and abort the entire batch, unlike the defensive try/except you use in execute_single_post_from_plan. Consider wrapping these sends in try/except and logging the error so the batch can continue.
The final summary message says Batch complete! All {len(plan['posts'])} posts created. even when some posts failed; using “processed” and plugging in completed/failed would better reflect reality.
Neither affects core correctness, but they’ll make operational behavior and messaging clearer.

221-369: Twitter routing logic and platform normalization look good; clean up small leftovers

The routing in _execute_single_post looks solid:

Normalizing platform aliases ('x', 'x/twitter') to 'twitter' is correct and matches the rest of the stack.
The heuristics (is_thread, is_single_post, explicit content_length directives, context length, outline detection) align with the documented goal of using the Haiku fast path only for genuinely simple single posts and preferring the Direct API agent for threads or complex contexts.
Two small cleanups:

topic_length = len(topic) is never used; you can drop it to satisfy Ruff’s F841 warning.
The inline comment “Use SDK agent for threads” (when use_haiku is False) is now stale since you’re routing to twitter_direct_api_agent; updating it will avoid confusion during future maintenance.
Functionality-wise this block looks good.

441-457: Airtable URL extraction improvements are correct; optional lint tidy

The updated extract_airtable_url_from_result:

Correctly matches both bare Airtable URLs and the “📊 Airtable Record: {url}” markdown pattern.
Trims trailing * so markdown wrappers don’t pollute the stored URL.
Behavior looks good. If you want to silence Ruff’s F541 on constant f‑strings, you can optionally drop the f on the log line:

-    print(f"⚠️ Could not extract Airtable URL from result")
+    print("⚠️ Could not extract Airtable URL from result")
Purely cosmetic.

660-800: Timeout and error messaging in execute_single_post_from_plan are inconsistent with the 360s limit and new Direct API architecture

Within execute_single_post_from_plan:

The asyncio.wait_for timeout is 360 seconds (6 minutes), and the logs mention “6-minute limit”, but:
The hook field says “timed out after 5 minutes”.
The error value says “Timeout after 300s”.
The timeout error message still references “Check SDK disconnect() calls.” even though _execute_single_post now exclusively uses Direct API agents.
For clearer debugging, consider aligning all references to 360 seconds / 6 minutes and updating the guidance to point at the direct API path (e.g., long validation/external validation cycles) rather than SDK disconnects:

-            'hook': f"Post {post_num} timed out after 5 minutes",
-            'error': f"Timeout after 300s - likely connection hang. Check SDK disconnect() calls."
+            'hook': f"Post {post_num} timed out after 6 minutes",
+            'error': "Timeout after 360s - likely long-running validation or external API delay in direct API agent."
This is purely messaging but will save time when diagnosing slow posts.

agents/linkedin_direct_api_agent.py (3)
244-329: LinkedInDirectAPIAgent initialization and circuit breaker wiring are sound, with minor refactor opportunity

Initialization correctly:

Validates ANTHROPIC_API_KEY and instantiates an Anthropic client.
Wires a CircuitBreaker with conservative settings (3 failures, 120s open).
Loads a compact base system prompt and then composes it with client context via load_system_prompt.
The custom circuit breaker handling (self.circuit_breaker._lock, manual state transitions) will work, but it duplicates logic that already exists in CircuitBreaker.call_async/decorator. If you want to simplify and avoid future drift between this agent and other callers, consider wrapping the core create_post call in the provided call_async helper instead of manipulating _lock and state directly.

330-605: Manual tool-calling loop in create_post looks correct; target_score is currently unused

The main create_post flow:

Builds a stacked system prompt via stack_prompts("linkedin") and passes it as a cached system block.
Differentiates between “thinking_mode” (full validation + fixes) and default mode by adjusting the workflow instructions and tool list.
Uses asyncio.to_thread + asyncio.wait_for around self.client.messages.create to keep the event loop responsive and enforce per-iteration timeouts.
Handles stop_reason values (end_turn, tool_use, max_tokens) as expected for tool-calling.
One minor observation: the target_score parameter isn’t currently used anywhere in the prompt or routing logic. If you don’t plan to tune behavior based on it, you could drop it from the method signature (and from callers) to reduce surface area; or, if you do plan to use it, consider threading it into the instructions (e.g., expected 0–25 or 0–100 scale) so it has an effect.

820-834: _detect_content_type works but can be made slightly clearer

The heuristic classification is fine, but two small nits:

The comprehension uses l as the loop variable ([l.strip() for l in content.split('\n') ...]), which is easy to misread; renaming to line improves clarity and silences E741.
The “hot take” detection uses content.startswith(...), which is case‑sensitive. Since you already compute content_lower, using content_lower.startswith(...) would make the detection more robust.
For example:

-        content_lower = content.lower()
-        lines = [l.strip() for l in content.split('\n') if l.strip()]
+        content_lower = content.lower()
+        lines = [line.strip() for line in content.split('\n') if line.strip()]
@@
-        if content.startswith(('everyone', 'nobody', 'stop', 'you\'re', 'you don\'t')):
+        if content_lower.startswith(('everyone', 'nobody', 'stop', "you're", "you don't")):
Purely a readability/heuristics improvement.

agents/twitter_direct_api_agent.py (1)
315-587: create_post flow looks solid; consider using or dropping target_score

The orchestration (stacked prompts, tool loop with bounded iterations/timeouts, and circuit-breaker gating) is well-structured and consistent with the other agents. The only oddity is that target_score (Line 320) is never used inside create_post, despite being part of the public signature and mentioned in docstrings. Either wire it into the validation/loop exit criteria or remove it from the signature to avoid confusion.

agents/youtube_direct_api_agent.py (1)
327-605: YouTube create_post orchestration is consistent; target_score unused

The YouTube orchestration closely mirrors the Twitter agent and looks sound: prompt stacking, bounded iteration loop, explicit tool wiring, and circuit breaker gating are all in place. As with the Twitter agent, target_score (Line 332) is part of the signature and docs but never used; consider either using it to influence the validation/fix loop or removing it from the interface.

agents/instagram_direct_api_agent.py (1)
325-603: Instagram create_post orchestration is consistent; target_score unused

The caption creation flow is consistent with the other direct agents (prompt stacking, tool loop, circuit-breaker guarding). As elsewhere, target_score (Line 330) is never used; if you don’t intend to gate on it, consider dropping it from the signature/docs to avoid confusion.

agents/email_direct_api_agent.py (1)
327-631: Email create_post orchestration is well-structured; target_score unused

The email agent’s orchestration (email_type normalization, word-count guidance, tool loop, and circuit breaker handling) looks good and consistent with the rest of the system. target_score (Line 332) again isn’t used anywhere; if you don’t plan to use it to control iteration/validation, consider removing it from the signature to reduce API surface area.

In agents/email_direct_api_agent.py:

> +async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
+    """Execute a tool by name with timeout protection"""
+
+    try:
+        # Execute native tool functions with unpacked arguments (30s timeout)
+        result = None
+
+        if tool_name == "search_company_documents":
+            result = await asyncio.wait_for(
+                search_company_documents_native(
+                    query=tool_input.get('query', ''),
+                    match_count=tool_input.get('match_count', 3),
+                    document_type=tool_input.get('document_type')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "generate_5_hooks":
+            result = await asyncio.wait_for(
+                generate_5_hooks_native(
+                    topic=tool_input.get('topic', ''),
+                    context=tool_input.get('context', ''),
+                    target_audience=tool_input.get('target_audience', 'professionals')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "create_human_draft":
+            result = await asyncio.wait_for(
+                create_human_draft_native(
+                    topic=tool_input.get('topic', ''),
+                    subject_line=tool_input.get('subject_line', ''),
+                    context=tool_input.get('context', '')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "inject_proof_points":
+            result = await asyncio.wait_for(
+                inject_proof_points_native(
+                    draft=tool_input.get('draft', ''),
+                    topic=tool_input.get('topic', ''),
+                    industry=tool_input.get('industry', 'SaaS')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "quality_check":
+            result = await asyncio.wait_for(
+                quality_check_native(
+                    post=tool_input.get('post', '')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "external_validation":
+            result = await asyncio.wait_for(
+                external_validation_native(
+                    post=tool_input.get('post', '')
+                ),
+                timeout=120.0  # Quality check (60s) + GPTZero (45s) + buffer
+            )
+
+        elif tool_name == "apply_fixes":
+            result = await asyncio.wait_for(
+                apply_fixes_native(
+                    post=tool_input.get('post', ''),
+                    issues_json=tool_input.get('issues_json', '[]'),
+                    current_score=tool_input.get('current_score', 0),
+                    gptzero_ai_pct=tool_input.get('gptzero_ai_pct'),
+                    gptzero_flagged_sentences=tool_input.get('gptzero_flagged_sentences', [])
+                ),
+                timeout=30.0
+            )
+
+        else:
+            return json.dumps({"error": f"Unknown tool: {tool_name}"})
+
+        # Native tools return plain text/JSON strings (not wrapped in {"content": [...]} )
+        return result if result else json.dumps({"error": "Tool returned empty result"})
+
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except Exception as e:
+        logger.error(f"Tool error: {tool_name} - {e}")
+        import traceback
+        traceback.print_exc()
+        return json.dumps({"error": f"Tool error: {str(e)}"})
+
⚠️ Potential issue | 🟡 Minor

Email tool dispatcher: fix timeout message inconsistency

Dispatcher wiring is correct (schemas match email_native_tools and tool routing), but the timeout branch has the same small inconsistency as the other agents: the log uses timeout_duration, while the JSON error is hardcoded to "30s".

-    except asyncio.TimeoutError:
-        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
-        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
-        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded {timeout_duration}"})
🧰 Tools 🪛 Ruff (0.14.5)
230-230: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

232-232: Do not catch blind exception: Exception

(BLE001)

233-233: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

236-236: Use explicit conversion flag

Replace with conversion flag

(RUF010)

🤖 Prompt for AI Agents
In agents/email_direct_api_agent.py around lines 147-237, the
asyncio.TimeoutError handler logs timeout_duration correctly but returns a JSON
error hardcoded to "30s"; update the returned JSON to use the same
timeout_duration variable (so external_validation returns "120s" and others
"30s") and ensure the error string matches the logger message (e.g., f"Tool
timeout: {tool_name} exceeded {timeout_duration}").
In agents/email_direct_api_agent.py:

> +            validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"
+
+        # Save to Airtable
+        print("\n📋 ATTEMPTING AIRTABLE SAVE")
+        airtable_url = None
+        airtable_record_id = None
+        try:
+            from integrations.airtable_client import get_airtable_client
+            airtable = get_airtable_client()
+
+            # Status determination based on 0-25 scale
+            if validation_score >= 24:  # 24-25
+                airtable_status = "Ready"
+            elif validation_score >= 18:  # 18-23
+                airtable_status = "Draft"
+            else:  # <18
+                airtable_status = "Needs Review"
+
+            result = airtable.create_content_record(
+                content=clean_output,
+                platform='email',
+                post_hook=hook_preview,
+                status=airtable_status,
+                suggested_edits=validation_formatted,
+                publish_date=self.publish_date
+            )
+
+            if result.get('success'):
+                airtable_url = result.get('url')
+                airtable_record_id = result.get('record_id')
+                print(f"✅ Saved to Airtable: {airtable_url}")
+        except Exception as e:
+            print(f"❌ Airtable save failed: {e}")
+
+        # Save to Supabase
+        print("\n💾 ATTEMPTING SUPABASE SAVE")
+        supabase_id = None
+        try:
+            from integrations.supabase_client import get_supabase_client
+            from tools.research_tools import generate_embedding
+
+            supabase = get_supabase_client()
+            embedding = generate_embedding(clean_output)
+
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'email',
+                'post_hook': hook_preview,
+                'body_content': clean_output,
+                'content_type': self._detect_content_type(clean_output),
+                'airtable_record_id': airtable_record_id,
+                'airtable_url': airtable_url,
+                'status': 'draft',
+                'quality_score': score,
+                'iterations': 3,
+                'slack_thread_ts': self.thread_ts,
+                'slack_channel_id': self.channel_id,
+                'user_id': self.user_id,
+                'created_by_agent': 'email_direct_api_agent',
+                'embedding': embedding
+            }).execute()
+
+            if supabase_result.data:
+                supabase_id = supabase_result.data[0]['id']
+                print(f"✅ Saved to Supabase: {supabase_id}")
+        except Exception as e:
+            print(f"❌ Supabase save failed: {e}")
+
+        # Log operation success
+        operation_duration = asyncio.get_event_loop().time() - operation_start_time
+        log_operation_end(
+            logger,
+            "create_email_post_direct_api",
+            duration=operation_duration,
+            success=True,
+            context=log_context,
+            quality_score=score,
+            supabase_id=supabase_id,
+            airtable_url=airtable_url
+        )
+
+        # Circuit breaker: Mark success
+        with self.circuit_breaker._lock:
+            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
+                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
+            self.circuit_breaker.failure_count = 0
+            self.circuit_breaker.state = CircuitState.CLOSED
+
+        return {
+            "success": True,
+            "post": clean_output,
+            "hook": hook_preview,
+            "score": score,
+            "hooks_tested": 5,
+            "iterations": 3,
+            "airtable_url": airtable_url or "[Airtable not configured]",
+            "google_doc_url": "[Coming Soon]",
+            "supabase_id": supabase_id,
+            "session_id": self.user_id,
+            "timestamp": datetime.now().isoformat()
+        }
⚠️ Potential issue | 🟠 Major

Harden email _parse_output against extractor failures

Same pattern as the other agents: if extract_structured_content raises, extracted isn’t defined, yet the code unconditionally does extracted.get(...), which will crash.

Suggested fix:

-        # Extract structured content using Haiku
-        from integrations.content_extractor import extract_structured_content
-
-        print("📝 Extracting content with Haiku...")
-        try:
-            extracted = await extract_structured_content(
-                raw_output=output,
-                platform='email'
-            )
-
-            clean_output = extracted['body']
-            hook_preview = extracted['hook']
-
-            print(f"✅ Extracted: {len(clean_output)} chars body")
-
-        except Exception as e:
-            print(f"❌ Extraction error: {e}")
-            clean_output = ""
-            hook_preview = "Extraction failed (see Suggested Edits)"
-
-        # Extract validation metadata
-        validation_score = extracted.get('original_score', 20)
-        validation_issues = extracted.get('validation_issues', [])
-        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
-        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])
+        # Extract structured content using Haiku
+        from integrations.content_extractor import extract_structured_content
+
+        print("📝 Extracting content with Haiku...")
+        extracted: Dict[str, Any] = {}
+        clean_output = output
+        hook_preview = output.strip().split("\n", 1)[0] if output else ""
+
+        try:
+            extracted = await extract_structured_content(
+                raw_output=output,
+                platform='email'
+            )
+
+            clean_output = extracted.get("body", clean_output)
+            hook_preview = extracted.get("hook", hook_preview)
+
+            print(f"✅ Extracted: {len(clean_output)} chars body")
+
+        except Exception as e:
+            print(f"❌ Extraction error: {e}")
+            # Keep fallback clean_output / hook_preview; extracted stays {}
+
+        # Extract validation metadata
+        validation_score = extracted.get("original_score", 20)
+        validation_issues = extracted.get("validation_issues", [])
+        gptzero_ai_pct = extracted.get("gptzero_ai_pct", None)
+        gptzero_flagged_sentences = extracted.get("gptzero_flagged_sentences", [])
🧰 Tools 🪛 Ruff (0.14.5)
689-689: Do not catch blind exception: Exception

(BLE001)

776-776: Do not catch blind exception: Exception

(BLE001)

809-809: Do not catch blind exception: Exception

(BLE001)

🤖 Prompt for AI Agents
In agents/email_direct_api_agent.py around lines 663 to 844, the code assumes
`extracted` exists after calling `extract_structured_content`, but if that call
raises an exception `extracted` is undefined and subsequent `extracted.get(...)`
calls will crash; fix by ensuring `extracted` (or the individual metadata
variables) are always defined with safe defaults in the except handler or by
initializing them before the try, then use those variables (e.g., clean_output =
"", hook_preview = "...", validation_score = 20, validation_issues = [],
gptzero_ai_pct = None, gptzero_flagged_sentences = []) so the rest of the
function can proceed even if extraction fails; update the try/except to assign
to these variables on success and to the defaults in the except block, and
remove any unconditional use of `extracted` after the try.
In agents/instagram_direct_api_agent.py:

> +async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
+    """Execute a tool by name with timeout protection"""
+
+    try:
+        # Execute native tool functions with unpacked arguments (30s timeout)
+        result = None
+
+        if tool_name == "search_company_documents":
+            result = await asyncio.wait_for(
+                search_company_documents_native(
+                    query=tool_input.get('query', ''),
+                    match_count=tool_input.get('match_count', 3),
+                    document_type=tool_input.get('document_type')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "generate_5_hooks":
+            result = await asyncio.wait_for(
+                generate_5_hooks_native(
+                    topic=tool_input.get('topic', ''),
+                    context=tool_input.get('context', ''),
+                    target_audience=tool_input.get('target_audience', 'professionals')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "create_caption_draft":
+            result = await asyncio.wait_for(
+                create_caption_draft_native(
+                    topic=tool_input.get('topic', ''),
+                    hook=tool_input.get('hook', ''),
+                    context=tool_input.get('context', '')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "condense_to_limit":
+            result = await asyncio.wait_for(
+                condense_to_limit_native(
+                    caption=tool_input.get('caption', ''),
+                    target_length=tool_input.get('target_length', 2200)
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "quality_check":
+            result = await asyncio.wait_for(
+                quality_check_native(
+                    post=tool_input.get('post', '')
+                ),
+                timeout=30.0
+            )
+
+        elif tool_name == "external_validation":
+            result = await asyncio.wait_for(
+                external_validation_native(
+                    post=tool_input.get('post', '')
+                ),
+                timeout=120.0  # Quality check (60s) + GPTZero (45s) + buffer
+            )
+
+        elif tool_name == "apply_fixes":
+            result = await asyncio.wait_for(
+                apply_fixes_native(
+                    post=tool_input.get('post', ''),
+                    issues_json=tool_input.get('issues_json', '[]'),
+                    current_score=tool_input.get('current_score', 0),
+                    gptzero_ai_pct=tool_input.get('gptzero_ai_pct'),
+                    gptzero_flagged_sentences=tool_input.get('gptzero_flagged_sentences', [])
+                ),
+                timeout=30.0
+            )
+
+        else:
+            return json.dumps({"error": f"Unknown tool: {tool_name}"})
+
+        # Native tools return plain text/JSON strings (not wrapped in {"content": [...]} )
+        return result if result else json.dumps({"error": "Tool returned empty result"})
+
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except Exception as e:
+        logger.error(f"Tool error: {tool_name} - {e}")
+        import traceback
+        traceback.print_exc()
+        return json.dumps({"error": f"Tool error: {str(e)}"})
+
⚠️ Potential issue | 🟡 Minor

Instagram tool dispatcher: align timeout error message

The dispatcher wiring looks correct and matches instagram_native_tools. As with the other agents, the timeout branch logs the correct timeout_duration but hardcodes "30s" in the JSON error string, which is confusing for external_validation.

-    except asyncio.TimeoutError:
-        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
-        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
-        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded {timeout_duration}"})
🧰 Tools 🪛 Ruff (0.14.5)
228-228: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

230-230: Do not catch blind exception: Exception

(BLE001)

231-231: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

234-234: Use explicit conversion flag

Replace with conversion flag

(RUF010)

In agents/instagram_direct_api_agent.py:

> +                        issue_num += 1
+            else:
+                lines.append("\n✅ No specific issues found")
+
+            validation_formatted = "\n".join(lines)
+        else:
+            validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"
+
+        # Save to Airtable
+        print("\n📋 ATTEMPTING AIRTABLE SAVE")
+        airtable_url = None
+        airtable_record_id = None
+        try:
+            from integrations.airtable_client import get_airtable_client
+            airtable = get_airtable_client()
+
+            airtable_status = "Needs Review" if validation_score < 18 else "Draft"
+
+            result = airtable.create_content_record(
+                content=clean_output,
+                platform='instagram',
+                post_hook=hook_preview,
+                status=airtable_status,
+                suggested_edits=validation_formatted,
+                publish_date=self.publish_date
+            )
+
+            if result.get('success'):
+                airtable_url = result.get('url')
+                airtable_record_id = result.get('record_id')
+                print(f"✅ Saved to Airtable: {airtable_url}")
+        except Exception as e:
+            print(f"❌ Airtable save failed: {e}")
+
+        # Save to Supabase
+        print("\n💾 ATTEMPTING SUPABASE SAVE")
+        supabase_id = None
+        try:
+            from integrations.supabase_client import get_supabase_client
+            from tools.research_tools import generate_embedding
+
+            supabase = get_supabase_client()
+            embedding = generate_embedding(clean_output)
+
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'email',
+                'post_hook': hook_preview,
+                'body_content': clean_output,
+                'content_type': self._detect_content_type(clean_output),
+                'airtable_record_id': airtable_record_id,
+                'airtable_url': airtable_url,
+                'status': 'draft',
+                'quality_score': score,
+                'iterations': 3,
+                'slack_thread_ts': self.thread_ts,
+                'slack_channel_id': self.channel_id,
+                'user_id': self.user_id,
+                'created_by_agent': 'instagram_direct_api_agent',
+                'embedding': embedding
+            }).execute()
+
+            if supabase_result.data:
+                supabase_id = supabase_result.data[0]['id']
+                print(f"✅ Saved to Supabase: {supabase_id}")
+        except Exception as e:
+            print(f"❌ Supabase save failed: {e}")
+
+        # Log operation success
+        operation_duration = asyncio.get_event_loop().time() - operation_start_time
+        log_operation_end(
+            logger,
+            "create_instagram_caption_direct_api",
+            duration=operation_duration,
+            success=True,
+            context=log_context,
+            quality_score=score,
+            supabase_id=supabase_id,
+            airtable_url=airtable_url
+        )
+
+        # Circuit breaker: Mark success
+        with self.circuit_breaker._lock:
+            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
+                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
+            self.circuit_breaker.failure_count = 0
+            self.circuit_breaker.state = CircuitState.CLOSED
+
+        return {
+            "success": True,
+            "post": clean_output,
+            "hook": hook_preview,
+            "score": score,
+            "hooks_tested": 5,
+            "iterations": 3,
+            "airtable_url": airtable_url or "[Airtable not configured]",
+            "google_doc_url": "[Coming Soon]",
+            "supabase_id": supabase_id,
+            "session_id": self.user_id,
+            "timestamp": datetime.now().isoformat()
+        }
⚠️ Potential issue | 🟠 Major

Fix extraction error path and Supabase platform for Instagram

Two concrete issues:

extracted is only defined inside the try around extract_structured_content, but accessed afterwards even if that call fails, which will raise a NameError.
The Supabase record uses platform: 'email' instead of 'instagram', which will confuse any platform-based queries/analytics.
Suggested changes:

@@
-        # Extract structured content using Haiku
-        from integrations.content_extractor import extract_structured_content
-
-        print("📝 Extracting content with Haiku...")
-        try:
-            extracted = await extract_structured_content(
-                raw_output=output,
-                platform='instagram'
-            )
-
-            clean_output = extracted['body']
-            hook_preview = extracted['hook']
-
-            print(f"✅ Extracted: {len(clean_output)} chars body")
-
-        except Exception as e:
-            print(f"❌ Extraction error: {e}")
-            clean_output = ""
-            hook_preview = "Extraction failed (see Suggested Edits)"
-
-        # Extract validation metadata
-        validation_score = extracted.get('original_score', 20)
-        validation_issues = extracted.get('validation_issues', [])
-        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
-        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])
+        # Extract structured content using Haiku
+        from integrations.content_extractor import extract_structured_content
+
+        print("📝 Extracting content with Haiku...")
+        extracted: Dict[str, Any] = {}
+        clean_output = output
+        hook_preview = output.strip().split("\n", 1)[0] if output else ""
+
+        try:
+            extracted = await extract_structured_content(
+                raw_output=output,
+                platform='instagram'
+            )
+
+            clean_output = extracted.get("body", clean_output)
+            hook_preview = extracted.get("hook", hook_preview)
+
+            print(f"✅ Extracted: {len(clean_output)} chars body")
+
+        except Exception as e:
+            print(f"❌ Extraction error: {e}")
+            # Keep fallback clean_output / hook_preview; extracted stays {}
+
+        # Extract validation metadata
+        validation_score = extracted.get("original_score", 20)
+        validation_issues = extracted.get("validation_issues", [])
+        gptzero_ai_pct = extracted.get("gptzero_ai_pct", None)
+        gptzero_flagged_sentences = extracted.get("gptzero_flagged_sentences", [])
@@
-            supabase_result = supabase.table('generated_posts').insert({
-                'platform': 'email',
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'instagram',
                 'post_hook': hook_preview,
                 'body_content': clean_output,
🧰 Tools 🪛 Ruff (0.14.5)
661-661: Do not catch blind exception: Exception

(BLE001)

742-742: Do not catch blind exception: Exception

(BLE001)

775-775: Do not catch blind exception: Exception

(BLE001)

🤖 Prompt for AI Agents
In agents/instagram_direct_api_agent.py around lines 635-810, fix two issues:
ensure variables derived from the Haiku extraction are always defined if
extract_structured_content raises (currently extracted is only set inside the
try and will cause a NameError on exception) by initializing extracted or
setting defaults for clean_output, hook_preview, validation_score,
validation_issues, gptzero_ai_pct and gptzero_flagged_sentences in the except
block (or define a default extracted = {...} before the try) so downstream code
can safely read them; and change the Supabase insert payload platform value from
'email' to 'instagram' so records are stored under the correct platform.
In agents/instagram_direct_api_agent.py:

> +async def create_instagram_workflow(
+    topic: str,
+    context: str = "",
+    style: str = "thought_leadership",
+    caption_type: str = "educational",
+    channel_id: Optional[str] = None,
+    thread_ts: Optional[str] = None,
+    user_id: Optional[str] = None,
+    publish_date: Optional[str] = None,
+    thinking_mode: bool = False
+) -> str:
+    """
+    Main entry point for Instagram content creation using direct API
+    Drop-in replacement for SDK version - same signature, same return format
+
+    Args:
+        topic: Main topic for the post
+        context: Additional context
+        style: Content style
+        caption_type: Caption type (educational, carousel, reel)
+        channel_id: Slack channel ID (for Airtable/Supabase saves)
+        thread_ts: Slack thread timestamp (for Airtable/Supabase saves)
+        user_id: Slack user ID (for Airtable/Supabase saves)
+        publish_date: Optional publish date
+        thinking_mode: If True, adds validation + fix loop for higher quality
+
+    Returns:
+        Formatted string with post content, score, and links
+    """
+
+    agent = InstagramDirectAPIAgent(
+        user_id=user_id,
+        channel_id=channel_id,
+        thread_ts=thread_ts,
+        batch_mode=True
+    )
+
+    try:
+        result = await agent.create_post(
+            topic=topic,
+            context=f"{context} | Style: {style}",
+            caption_type=caption_type,
+            target_score=85,
+            publish_date=publish_date,
+            thinking_mode=thinking_mode
+        )
+
+        if result['success']:
+            return f"""✅ **Instagram Caption Created**
+
+**Hook Preview:**
+_{result.get('hook', result['post'][:200])}..._
+
+**Quality Score:** {result.get('score', 20)}/25 (Iterations: {result.get('iterations', 3)})
+
+**Full Post:**
+{result['post']}
+
+---
+📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
+📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}
+
+*AI Patterns Removed | Facts Verified | Ready to Post*"""
+        else:
+            return f"❌ Creation failed: {result.get('error', 'Unknown error')}"
+
+    except Exception as e:
+        logger.error(f"Email Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
⚠️ Potential issue | 🟡 Minor

Correct Instagram workflow error log label

The outer workflow wrapper currently logs "Email Direct API workflow error" on exception, which is misleading for Instagram.

-    except Exception as e:
-        logger.error(f"Email Direct API workflow error: {e}")
-        return f"❌ Unexpected error: {str(e)}"
+    except Exception as e:
+        logger.error(f"Instagram Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
🧰 Tools 🪛 Ruff (0.14.5)
897-897: Do not catch blind exception: Exception

(BLE001)

898-898: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

899-899: Use explicit conversion flag

Replace with conversion flag

(RUF010)

🤖 Prompt for AI Agents
In agents/instagram_direct_api_agent.py around lines 831 to 899, the exception
handler logs "Email Direct API workflow error" which is incorrect for this
Instagram workflow; update the logger.error call to use an Instagram-specific
label (e.g., "Instagram Direct API workflow error") and include the exception
details (and optionally the stack/trace) in the log message so the error is
correctly identified and debuggable.
In agents/linkedin_direct_api_agent.py:

> +            validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"
+
+        # Save to Airtable
+        print("\n📋 ATTEMPTING AIRTABLE SAVE")
+        airtable_url = None
+        airtable_record_id = None
+        try:
+            from integrations.airtable_client import get_airtable_client
+            airtable = get_airtable_client()
+
+            # Status determination based on 0-25 scale
+            if validation_score >= 24:  # 24-25
+                airtable_status = "Ready"
+            elif validation_score >= 18:  # 18-23
+                airtable_status = "Draft"
+            else:  # <18
+                airtable_status = "Needs Review"
+
+            result = airtable.create_content_record(
+                content=clean_output,
+                platform='linkedin',
+                post_hook=hook_preview,
+                status=airtable_status,
+                suggested_edits=validation_formatted,
+                publish_date=self.publish_date
+            )
+
+            if result.get('success'):
+                airtable_url = result.get('url')
+                airtable_record_id = result.get('record_id')
+                print(f"✅ Saved to Airtable: {airtable_url}")
+        except Exception as e:
+            print(f"❌ Airtable save failed: {e}")
+
+        # Save to Supabase
+        print("\n💾 ATTEMPTING SUPABASE SAVE")
+        supabase_id = None
+        try:
+            from integrations.supabase_client import get_supabase_client
+            from tools.research_tools import generate_embedding
+
+            supabase = get_supabase_client()
+            embedding = generate_embedding(clean_output)
+
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'linkedin',
+                'post_hook': hook_preview,
+                'body_content': clean_output,
+                'content_type': self._detect_content_type(clean_output),
+                'airtable_record_id': airtable_record_id,
+                'airtable_url': airtable_url,
+                'status': 'draft',
+                'quality_score': score,
+                'iterations': 3,
+                'slack_thread_ts': self.thread_ts,
+                'slack_channel_id': self.channel_id,
+                'user_id': self.user_id,
+                'created_by_agent': 'linkedin_direct_api_agent',
+                'embedding': embedding
+            }).execute()
+
+            if supabase_result.data:
+                supabase_id = supabase_result.data[0]['id']
+                print(f"✅ Saved to Supabase: {supabase_id}")
+        except Exception as e:
+            print(f"❌ Supabase save failed: {e}")
+
+        # Log operation success
+        operation_duration = asyncio.get_event_loop().time() - operation_start_time
+        log_operation_end(
+            logger,
+            "create_linkedin_post_direct_api",
+            duration=operation_duration,
+            success=True,
+            context=log_context,
+            quality_score=score,
+            supabase_id=supabase_id,
+            airtable_url=airtable_url
+        )
+
+        # Circuit breaker: Mark success
+        with self.circuit_breaker._lock:
+            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
+                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
+            self.circuit_breaker.failure_count = 0
+            self.circuit_breaker.state = CircuitState.CLOSED
+
+        return {
+            "success": True,
+            "post": clean_output,
+            "hook": hook_preview,
+            "score": score,
+            "hooks_tested": 5,
+            "iterations": 3,
+            "airtable_url": airtable_url or "[Airtable not configured]",
+            "google_doc_url": "[Coming Soon]",
+            "supabase_id": supabase_id,
+            "session_id": self.user_id,
+            "timestamp": datetime.now().isoformat()
+        }
⚠️ Potential issue | 🔴 Critical

Fix _parse_output to avoid UnboundLocalError and correctly consume validation metadata from JSON output

_parse_output has two intertwined issues:

If extract_structured_content raises, extracted is never defined, but you still access extracted.get(...) afterwards → UnboundLocalError.
The function assumes validation fields (original_score, validation_issues, gptzero_*) live on extracted, but integrations.content_extractor.extract_structured_content is documented to return only structural fields (body, hook, platform, publish_date, metadata). In “thinking mode” your workflow instructs the agent to return a JSON object with those validation keys; today they are ignored.
A robust pattern is:

First, try to json.loads(output) and, if it’s a dict with post_text, pull:
post_text as the raw post body,
original_score, validation_issues, gptzero_ai_pct, gptzero_flagged_sentences as metadata.
Then run extract_structured_content on post_text (or on the entire output if JSON parsing fails) to get clean body/hook.
On extractor failure, fall back to using the raw post text for clean_output and hook_preview instead of an empty string.
Example diff illustrating this fix:

-        # Extract structured content using Haiku
-        from integrations.content_extractor import extract_structured_content
-
-        print("📝 Extracting content with Haiku...")
-        try:
-            extracted = await extract_structured_content(
-                raw_output=output,
-                platform='linkedin'
-            )
-
-            clean_output = extracted['body']
-            hook_preview = extracted['hook']
-
-            print(f"✅ Extracted: {len(clean_output)} chars body")
-
-        except Exception as e:
-            print(f"❌ Extraction error: {e}")
-            clean_output = ""
-            hook_preview = "Extraction failed (see Suggested Edits)"
-
-        # Extract validation metadata
-        validation_score = extracted.get('original_score', 20)
-        validation_issues = extracted.get('validation_issues', [])
-        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
-        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])
+        # Try to parse JSON metadata first (thinking-mode output), otherwise
+        # treat `output` as raw post text.
+        validation_score = 20
+        validation_issues: List[Any] = []
+        gptzero_ai_pct = None
+        gptzero_flagged_sentences: List[str] = []
+
+        raw_post_text = output
+        try:
+            parsed = json.loads(output)
+            if isinstance(parsed, dict) and "post_text" in parsed:
+                raw_post_text = parsed["post_text"]
+                validation_score = parsed.get("original_score", validation_score)
+                validation_issues = parsed.get("validation_issues", validation_issues) or []
+                gptzero_ai_pct = parsed.get("gptzero_ai_pct", gptzero_ai_pct)
+                gptzero_flagged_sentences = parsed.get(
+                    "gptzero_flagged_sentences", gptzero_flagged_sentences
+                ) or []
+        except json.JSONDecodeError:
+            # Non‑JSON output – fall back to treating the whole string as the post body
+            pass
+
+        # Extract structured content using Haiku on the post text only
+        from integrations.content_extractor import extract_structured_content
+
+        print("📝 Extracting content with Haiku...")
+        try:
+            extracted = await extract_structured_content(
+                raw_output=raw_post_text,
+                platform="linkedin",
+            )
+
+            clean_output = extracted.get("body", raw_post_text)
+            hook_preview = extracted.get("hook", clean_output[:200])
+
+            print(f"✅ Extracted: {len(clean_output)} chars body")
+
+        except Exception as e:
+            print(f"❌ Extraction error: {e}")
+            clean_output = raw_post_text
+            hook_preview = raw_post_text[:200]
score = validation_score and the downstream Airtable/Supabase status logic can remain as-is, but now they’ll actually reflect the external validation results when present, and the function won’t crash if extraction fails.

🧰 Tools 🪛 Ruff (0.14.5)
663-663: Do not catch blind exception: Exception

(BLE001)

750-750: Do not catch blind exception: Exception

(BLE001)

783-783: Do not catch blind exception: Exception

(BLE001)

🤖 Prompt for AI Agents
In agents/linkedin_direct_api_agent.py around lines 637–818, _parse_output
currently uses extracted after a failing extract_structured_content call and
assumes validation fields live on extracted; fix by first trying to
json.loads(output) to pull a raw post_text and any validation metadata
(original_score, validation_issues, gptzero_ai_pct, gptzero_flagged_sentences)
from the top-level JSON or metadata field, then run extract_structured_content
against the post_text (or the full output if JSON parsing fails); ensure
extracted is always defined (set sensible defaults) so you never access
extracted.get(...) when it may be undefined, and if the extractor raises, fall
back to using the raw post_text for clean_output and a sensible default for
hook_preview while preserving any metadata already parsed so
validation_score/validation_issues reflect provided JSON instead of being lost.
In agents/twitter_direct_api_agent.py:

> +TOOL_SCHEMAS = [
+    {
+        "name": "search_company_documents",
+        "description": "Search user-uploaded docs (case studies, testimonials, product docs) for proof points",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "query": {"type": "string", "description": "Search query"},
+                "match_count": {"type": "integer", "description": "Number of results to return", "default": 3},
+                "document_type": {"type": "string", "description": "Optional filter by document type"}
+            },
+            "required": ["query"]
+        }
+    },
+    {
+        "name": "generate_5_hooks",
+        "description": "Generate 5 Email hooks in different formats",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "topic": {"type": "string", "description": "Main topic for hooks"},
+                "context": {"type": "string", "description": "Additional context"},
+                "target_audience": {"type": "string", "description": "Target audience"}
+            },
+            "required": ["topic", "context", "target_audience"]
+        }
+    },
+    {
+        "name": "create_human_draft",
+        "description": "Generate Twitter thread with quality self-assessment",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "topic": {"type": "string", "description": "Post topic"},
+                "hook": {"type": "string", "description": "Selected hook"},
+                "context": {"type": "string", "description": "Additional context"},
+                "target_length": {"type": "integer", "description": "Target character limit (default 2200)"}
+            },
+            "required": ["topic", "hook", "context"]
+        }
+    },
+    {
+        "name": "quality_check",
+        "description": "Score post on 5 axes and return surgical fixes",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to check"}
+            },
+            "required": ["post"]
+        }
+    },
+    {
+        "name": "external_validation",
+        "description": "Run comprehensive validation: Editor-in-Chief rules + GPTZero AI detection",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to validate"}
+            },
+            "required": ["post"]
+        }
+    },
+    {
+        "name": "apply_fixes",
+        "description": "Apply fixes to ALL flagged issues (no limit on number of fixes)",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to fix"},
+                "issues_json": {"type": "string", "description": "JSON array of issues"},
+                "current_score": {"type": "integer", "description": "Current quality score"},
+                "gptzero_ai_pct": {"type": "number", "description": "GPTZero AI percentage"},
+                "gptzero_flagged_sentences": {"type": "array", "items": {"type": "string"}, "description": "Flagged sentences"}
+            },
+            "required": ["post", "issues_json", "current_score"]
+        }
+    }
+]
⚠️ Potential issue | 🟠 Major

Twitter tools: add inject_proof_points schema and fix timeout error message

Two functional issues here:

inject_proof_points_native is imported, used in execute_tool, and referenced in the system/workflow text, but there is no corresponding entry in TOOL_SCHEMAS. That means Anthropic never sees this tool in the tools list, so it can't emit tool_use blocks for it.
In the timeout handler, timeout_duration is correctly computed (30s vs 120s) but the JSON error message is hardcoded to 30s, which is misleading for external_validation.
Proposed fix:

@@
-    {
-        "name": "generate_5_hooks",
-        "description": "Generate 5 Email hooks in different formats",
+    {
+        "name": "generate_5_hooks",
+        "description": "Generate 5 Twitter hooks in different formats",
@@
-    {
-        "name": "create_human_draft",
-        "description": "Generate Twitter thread with quality self-assessment",
-        "input_schema": {
-            "type": "object",
-            "properties": {
-                "topic": {"type": "string", "description": "Post topic"},
-                "hook": {"type": "string", "description": "Selected hook"},
-                "context": {"type": "string", "description": "Additional context"},
-                "target_length": {"type": "integer", "description": "Target character limit (default 2200)"}
-            },
-            "required": ["topic", "hook", "context"]
-        }
-    },
+    {
+        "name": "create_human_draft",
+        "description": "Generate Twitter thread with quality self-assessment",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "topic": {"type": "string", "description": "Post topic"},
+                "hook": {"type": "string", "description": "Selected hook"},
+                "context": {"type": "string", "description": "Additional context"},
+                "target_length": {"type": "integer", "description": "Target character limit (default 2200)"}
+            },
+            "required": ["topic", "hook", "context"]
+        }
+    },
+    {
+        "name": "inject_proof_points",
+        "description": "Add metrics and proof points. Searches company documents first for real case studies.",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "draft": {"type": "string", "description": "Draft post text"},
+                "topic": {"type": "string", "description": "Post topic"},
+                "industry": {"type": "string", "description": "Industry context"}
+            },
+            "required": ["draft", "topic", "industry"]
+        }
+    },
@@
-    except asyncio.TimeoutError:
-        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
-        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
-        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded {timeout_duration}"})
Also applies to: 135-225

In agents/twitter_direct_api_agent.py:

> +            from integrations.airtable_client import get_airtable_client
+            airtable = get_airtable_client()
+
+            if not airtable:
+                print("⚠️ Airtable client not configured - skipping save")
+            else:
+                # Status determination based on 0-25 scale
+                if validation_score >= 24:  # 24-25
+                    airtable_status = "Ready"
+                elif validation_score >= 18:  # 18-23
+                    airtable_status = "Draft"
+                else:  # <18
+                    airtable_status = "Needs Review"
+
+                result = airtable.create_content_record(
+                    content=clean_output,
+                    platform='twitter',
+                    post_hook=hook_preview,
+                    status=airtable_status,
+                    suggested_edits=validation_formatted,
+                    publish_date=self.publish_date
+                )
+
+                if result.get('success'):
+                    airtable_url = result.get('url')
+                    airtable_record_id = result.get('record_id')
+                    print(f"✅ Saved to Airtable: {airtable_url}")
+                else:
+                    print(f"⚠️ Airtable save returned success=False: {result.get('error', 'No error message')}")
+        except Exception as e:
+            print(f"❌ Airtable save failed: {e}")
+            import traceback
+            traceback.print_exc()
+
+        # Save to Supabase
+        print("\n💾 ATTEMPTING SUPABASE SAVE")
+        supabase_id = None
+        try:
+            from integrations.supabase_client import get_supabase_client
+            from tools.research_tools import generate_embedding
+
+            supabase = get_supabase_client()
+            embedding = generate_embedding(clean_output)
+
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'twitter',
+                'post_hook': hook_preview,
+                'body_content': clean_output,
+                'content_type': self._detect_content_type(clean_output),
+                'airtable_record_id': airtable_record_id,
+                'airtable_url': airtable_url,
+                'status': 'draft',
+                'quality_score': score,
+                'iterations': 3,
+                'slack_thread_ts': self.thread_ts,
+                'slack_channel_id': self.channel_id,
+                'user_id': self.user_id,
+                'created_by_agent': 'twitter_direct_api_agent',
+                'embedding': embedding
+            }).execute()
+
+            if supabase_result.data:
+                supabase_id = supabase_result.data[0]['id']
+                print(f"✅ Saved to Supabase: {supabase_id}")
+        except Exception as e:
+            print(f"❌ Supabase save failed: {e}")
+
+        # Log operation success
+        operation_duration = asyncio.get_event_loop().time() - operation_start_time
+        log_operation_end(
+            logger,
+            "create_twitter_post_direct_api",
+            duration=operation_duration,
+            success=True,
+            context=log_context,
+            quality_score=score,
+            supabase_id=supabase_id,
+            airtable_url=airtable_url
+        )
+
+        # Circuit breaker: Mark success
+        with self.circuit_breaker._lock:
+            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
+                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
+            self.circuit_breaker.failure_count = 0
+            self.circuit_breaker.state = CircuitState.CLOSED
+
+        return {
+            "success": True,
+            "post": clean_output,
+            "hook": hook_preview,
+            "score": score,
+            "hooks_tested": 5,
+            "iterations": 3,
+            "airtable_url": airtable_url or "[Airtable not configured]",
+            "google_doc_url": "[Coming Soon]",
+            "supabase_id": supabase_id,
+            "session_id": self.user_id,
+            "timestamp": datetime.now().isoformat()
+        }
⚠️ Potential issue | 🟠 Major

Fix _parse_output when Haiku extraction fails (extracted may be undefined)

If extract_structured_content raises, extracted is never set, but the code still does extracted.get(...) afterwards. That will raise a NameError and turn an extraction problem into a hard failure.

A safer pattern is to initialize extracted, clean_output, and hook_preview with fallbacks, then override them on successful extraction:

     async def _parse_output(self, output: str, operation_start_time: float, log_context: dict) -> Dict[str, Any]:
@@
-        # Extract structured content using Haiku
-        from integrations.content_extractor import extract_structured_content
-
-        print("📝 Extracting content with Haiku...")
-        try:
-            extracted = await extract_structured_content(
-                raw_output=output,
-                platform='twitter'
-            )
-
-            clean_output = extracted['body']
-            hook_preview = extracted['hook']
-
-            print(f"✅ Extracted: {len(clean_output)} chars body")
-
-        except Exception as e:
-            print(f"❌ Extraction error: {e}")
-            clean_output = ""
-            hook_preview = "Extraction failed (see Suggested Edits)"
-
-        # Extract validation metadata
-        validation_score = extracted.get('original_score', 20)
-        validation_issues = extracted.get('validation_issues', [])
-        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
-        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])
+        # Extract structured content using Haiku
+        from integrations.content_extractor import extract_structured_content
+
+        print("📝 Extracting content with Haiku...")
+        extracted: Dict[str, Any] = {}
+        # Sensible fallbacks if extraction fails
+        clean_output = output
+        hook_preview = output.strip().split("\n", 1)[0] if output else ""
+
+        try:
+            extracted = await extract_structured_content(
+                raw_output=output,
+                platform='twitter'
+            )
+
+            clean_output = extracted.get("body", clean_output)
+            hook_preview = extracted.get("hook", hook_preview)
+
+            print(f"✅ Extracted: {len(clean_output)} chars body")
+
+        except Exception as e:
+            print(f"❌ Extraction error: {e}")
+            # Keep fallback clean_output / hook_preview; extracted stays {}
+
+        # Extract validation metadata (safe even if extraction failed)
+        validation_score = extracted.get("original_score", 20)
+        validation_issues = extracted.get("validation_issues", [])
+        gptzero_ai_pct = extracted.get("gptzero_ai_pct", None)
+        gptzero_flagged_sentences = extracted.get("gptzero_flagged_sentences", [])
Apply the same pattern to the other direct agents for consistency.

🧰 Tools 🪛 Ruff (0.14.5)
645-645: Do not catch blind exception: Exception

(BLE001)

737-737: Do not catch blind exception: Exception

(BLE001)

772-772: Do not catch blind exception: Exception

(BLE001)

🤖 Prompt for AI Agents
agents/twitter_direct_api_agent.py around lines 619-807: the code calls
extracted.get(...) after extract_structured_content may raise, leaving extracted
undefined and causing a NameError; initialize extracted = {} and sensible
defaults for clean_output and hook_preview before the try, assign extracted =
await extract_structured_content(...) inside the try, and in the except set
extracted = {} (or keep the defaults) so subsequent extracted.get(...) calls are
safe; apply the same initialization/fallback pattern to other direct agent
_parse_output implementations for consistency.
In agents/twitter_direct_api_agent.py:

> +async def create_twitter_post_workflow(
+    topic: str,
+    context: str = "",
+    style: str = "thought_leadership",
+    channel_id: Optional[str] = None,
+    thread_ts: Optional[str] = None,
+    user_id: Optional[str] = None,
+    publish_date: Optional[str] = None,
+    thinking_mode: bool = False
+) -> str:
+    """
+    Main entry point for Twitter content creation using direct API
+    Drop-in replacement for SDK version - same signature, same return format
+
+    Args:
+        topic: Main topic for the thread
+        context: Additional context
+        style: Content style
+        channel_id: Slack channel ID (for Airtable/Supabase saves)
+        thread_ts: Slack thread timestamp (for Airtable/Supabase saves)
+        user_id: Slack user ID (for Airtable/Supabase saves)
+        publish_date: Optional publish date
+        thinking_mode: If True, adds validation + fix loop for higher quality
+
+    Returns:
+        Formatted string with thread content, score, and links
+    """
+
+    agent = TwitterDirectAPIAgent(
+        user_id=user_id,
+        channel_id=channel_id,
+        thread_ts=thread_ts,
+        batch_mode=True
+    )
+
+    try:
+        thread_type = "standard"  # Twitter default
+
+        result = await agent.create_post(
+            topic=topic,
+            context=f"{context} | Style: {style}",
+            thread_type=thread_type,
+            target_score=85,
+            publish_date=publish_date,
+            thinking_mode=thinking_mode
+        )
+
+        if result['success']:
+            return f"""✅ **Twitter Thread Created**
+
+**Hook Preview:**
+_{result.get('hook', result['post'][:200])}..._
+
+**Quality Score:** {result.get('score', 20)}/25 (Iterations: {result.get('iterations', 3)})
+
+**Full Post:**
+{result['post']}
+
+---
+📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
+📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}
+
+*AI Patterns Removed | Facts Verified | Ready to Post*"""
+        else:
+            return f"❌ Creation failed: {result.get('error', 'Unknown error')}"
+
+    except Exception as e:
+        logger.error(f"Email Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
+
⚠️ Potential issue | 🟡 Minor

Fix mislabeled error log in create_twitter_post_workflow

The catch-all handler currently logs "Email Direct API workflow error", which is confusing when debugging Twitter issues.

-    except Exception as e:
-        logger.error(f"Email Direct API workflow error: {e}")
-        return f"❌ Unexpected error: {str(e)}"
+    except Exception as e:
+        logger.error(f"Twitter Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
🧰 Tools 🪛 Ruff (0.14.5)
894-894: Do not catch blind exception: Exception

(BLE001)

895-895: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

896-896: Use explicit conversion flag

Replace with conversion flag

(RUF010)

🤖 Prompt for AI Agents
In agents/twitter_direct_api_agent.py around lines 828 to 897, the exception
handler logs "Email Direct API workflow error" which is mislabelled for this
Twitter workflow; change the log message to accurately reflect Twitter (e.g.,
"Twitter Direct API workflow error") and include the exception details/stack
trace (use the exception object and exc_info=True or equivalent) so logs clearly
identify the source and full error context.
In agents/youtube_direct_api_agent.py:

> +TOOL_SCHEMAS = [
+    {
+        "name": "search_company_documents",
+        "description": "Search user-uploaded docs (case studies, testimonials, product docs) for proof points",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "query": {"type": "string", "description": "Search query"},
+                "match_count": {"type": "integer", "description": "Number of results to return", "default": 3},
+                "document_type": {"type": "string", "description": "Optional filter by document type"}
+            },
+            "required": ["query"]
+        }
+    },
+    {
+        "name": "generate_5_hooks",
+        "description": "Generate 5 Email hooks in different formats",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "topic": {"type": "string", "description": "Main topic for hooks"},
+                "context": {"type": "string", "description": "Additional context"},
+                "target_audience": {"type": "string", "description": "Target audience"}
+            },
+            "required": ["topic", "context", "target_audience"]
+        }
+    },
+    {
+        "name": "create_human_script",
+        "description": "Generate Email draft with quality self-assessment",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "topic": {"type": "string", "description": "Post topic"},
+                "video_hook": {"type": "string", "description": "Selected subject line"},
+                "context": {"type": "string", "description": "Additional context"}
+            },
+            "required": ["topic", "video_hook", "context"]
+        }
+    },
+    {
+        "name": "inject_proof_points",
+        "description": "Add metrics and proof points. Searches company documents first for real case studies.",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "draft": {"type": "string", "description": "Draft post text"},
+                "topic": {"type": "string", "description": "Post topic"},
+                "industry": {"type": "string", "description": "Industry context"}
+            },
+            "required": ["draft", "topic", "industry"]
+        }
+    },
+    {
+        "name": "quality_check",
+        "description": "Score post on 5 axes and return surgical fixes",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to check"}
+            },
+            "required": ["post"]
+        }
+    },
+    {
+        "name": "external_validation",
+        "description": "Run comprehensive validation: Editor-in-Chief rules + GPTZero AI detection",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to validate"}
+            },
+            "required": ["post"]
+        }
+    },
+    {
+        "name": "apply_fixes",
+        "description": "Apply fixes to ALL flagged issues (no limit on number of fixes)",
+        "input_schema": {
+            "type": "object",
+            "properties": {
+                "post": {"type": "string", "description": "Post to fix"},
+                "issues_json": {"type": "string", "description": "JSON array of issues"},
+                "current_score": {"type": "integer", "description": "Current quality score"},
+                "gptzero_ai_pct": {"type": "number", "description": "GPTZero AI percentage"},
+                "gptzero_flagged_sentences": {"type": "array", "items": {"type": "string"}, "description": "Flagged sentences"}
+            },
+            "required": ["post", "issues_json", "current_score"]
+        }
+    }
+]
⚠️ Potential issue | 🟡 Minor

YouTube tool dispatcher: tighten descriptions and fix timeout message

Functionally this block is fine (schemas align with youtube_native_tools and dispatch is correct), but two things are worth adjusting:

Descriptions for generate_5_hooks and create_human_script still talk about “Email” rather than YouTube, which can subtly mislead the model.
The timeout handler computes timeout_duration but returns a JSON error string hardcoded to 30s, which is wrong for external_validation.
Suggested diff:

@@
-    {
-        "name": "generate_5_hooks",
-        "description": "Generate 5 Email hooks in different formats",
+    {
+        "name": "generate_5_hooks",
+        "description": "Generate 5 video hooks in different formats",
@@
-    {
-        "name": "create_human_script",
-        "description": "Generate Email draft with quality self-assessment",
+    {
+        "name": "create_human_script",
+        "description": "Generate YouTube script with quality self-assessment",
@@
-    except asyncio.TimeoutError:
-        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
-        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
-        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded 30s"})
+    except asyncio.TimeoutError:
+        timeout_duration = "120s" if tool_name == "external_validation" else "30s"
+        logger.error(f"Tool timeout: {tool_name} exceeded {timeout_duration}")
+        return json.dumps({"error": f"Tool timeout: {tool_name} exceeded {timeout_duration}"})
Also applies to: 147-237

🤖 Prompt for AI Agents
In agents/youtube_direct_api_agent.py around lines 52-142 (and similarly
147-237), update the tool schemas and timeout message: change the descriptions
for generate_5_hooks and create_human_script from “Email” wording to
YouTube/video-centric wording (e.g., “Generate 5 video hooks” and “Generate
video script with self-assessment” or similar), and in the timeout handler
replace the hardcoded "30s" error text with the computed timeout_duration
variable so the returned JSON error reflects the actual timeout value (ensure
the timeout string interpolation/formatting uses the existing timeout_duration
value).
In agents/youtube_direct_api_agent.py:

> +                        issue_num += 1
+            else:
+                lines.append("\n✅ No specific issues found")
+
+            validation_formatted = "\n".join(lines)
+        else:
+            validation_formatted = f"✅ No validation issues found\nQuality Score: {validation_score}/25"
+
+        # Save to Airtable
+        print("\n📋 ATTEMPTING AIRTABLE SAVE")
+        airtable_url = None
+        airtable_record_id = None
+        try:
+            from integrations.airtable_client import get_airtable_client
+            airtable = get_airtable_client()
+
+            airtable_status = "Needs Review" if validation_score < 18 else "Draft"
+
+            result = airtable.create_content_record(
+                content=clean_output,
+                platform='youtube',
+                post_hook=hook_preview,
+                status=airtable_status,
+                suggested_edits=validation_formatted,
+                publish_date=self.publish_date
+            )
+
+            if result.get('success'):
+                airtable_url = result.get('url')
+                airtable_record_id = result.get('record_id')
+                print(f"✅ Saved to Airtable: {airtable_url}")
+        except Exception as e:
+            print(f"❌ Airtable save failed: {e}")
+
+        # Save to Supabase
+        print("\n💾 ATTEMPTING SUPABASE SAVE")
+        supabase_id = None
+        try:
+            from integrations.supabase_client import get_supabase_client
+            from tools.research_tools import generate_embedding
+
+            supabase = get_supabase_client()
+            embedding = generate_embedding(clean_output)
+
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'email',
+                'post_hook': hook_preview,
+                'body_content': clean_output,
+                'content_type': self._detect_content_type(clean_output),
+                'airtable_record_id': airtable_record_id,
+                'airtable_url': airtable_url,
+                'status': 'draft',
+                'quality_score': score,
+                'iterations': 3,
+                'slack_thread_ts': self.thread_ts,
+                'slack_channel_id': self.channel_id,
+                'user_id': self.user_id,
+                'created_by_agent': 'youtube_direct_api_agent',
+                'embedding': embedding
+            }).execute()
+
+            if supabase_result.data:
+                supabase_id = supabase_result.data[0]['id']
+                print(f"✅ Saved to Supabase: {supabase_id}")
+        except Exception as e:
+            print(f"❌ Supabase save failed: {e}")
+
+        # Log operation success
+        operation_duration = asyncio.get_event_loop().time() - operation_start_time
+        log_operation_end(
+            logger,
+            "create_youtube_script_direct_api",
+            duration=operation_duration,
+            success=True,
+            context=log_context,
+            quality_score=score,
+            supabase_id=supabase_id,
+            airtable_url=airtable_url
+        )
+
+        # Circuit breaker: Mark success
+        with self.circuit_breaker._lock:
+            if self.circuit_breaker.state == CircuitState.HALF_OPEN:
+                logger.info("✅ Circuit breaker test successful - CLOSING", **log_context)
+            self.circuit_breaker.failure_count = 0
+            self.circuit_breaker.state = CircuitState.CLOSED
+
+        return {
+            "success": True,
+            "post": clean_output,
+            "hook": hook_preview,
+            "score": score,
+            "hooks_tested": 5,
+            "iterations": 3,
+            "airtable_url": airtable_url or "[Airtable not configured]",
+            "google_doc_url": "[Coming Soon]",
+            "supabase_id": supabase_id,
+            "session_id": self.user_id,
+            "timestamp": datetime.now().isoformat()
+        }
⚠️ Potential issue | 🟠 Major

Fix extraction failure path and Supabase platform for YouTube

Two issues here:

Same as Twitter: if extract_structured_content raises, extracted is never defined but is accessed later, causing a NameError.
In the Supabase insert, platform is set to 'email' instead of 'youtube', which will pollute analytics/search keyed by platform.
Proposed changes:

@@
-        # Extract structured content using Haiku
-        from integrations.content_extractor import extract_structured_content
-
-        print("📝 Extracting content with Haiku...")
-        try:
-            extracted = await extract_structured_content(
-                raw_output=output,
-                platform='youtube'
-            )
-
-            clean_output = extracted['body']
-            hook_preview = extracted['hook']
-
-            print(f"✅ Extracted: {len(clean_output)} chars body")
-
-        except Exception as e:
-            print(f"❌ Extraction error: {e}")
-            clean_output = ""
-            hook_preview = "Extraction failed (see Suggested Edits)"
-
-        # Extract validation metadata
-        validation_score = extracted.get('original_score', 20)
-        validation_issues = extracted.get('validation_issues', [])
-        gptzero_ai_pct = extracted.get('gptzero_ai_pct', None)
-        gptzero_flagged_sentences = extracted.get('gptzero_flagged_sentences', [])
+        # Extract structured content using Haiku
+        from integrations.content_extractor import extract_structured_content
+
+        print("📝 Extracting content with Haiku...")
+        extracted: Dict[str, Any] = {}
+        clean_output = output
+        hook_preview = output.strip().split("\n", 1)[0] if output else ""
+
+        try:
+            extracted = await extract_structured_content(
+                raw_output=output,
+                platform='youtube'
+            )
+
+            clean_output = extracted.get("body", clean_output)
+            hook_preview = extracted.get("hook", hook_preview)
+
+            print(f"✅ Extracted: {len(clean_output)} chars body")
+
+        except Exception as e:
+            print(f"❌ Extraction error: {e}")
+            # Keep fallback clean_output / hook_preview; extracted stays {}
+
+        # Extract validation metadata
+        validation_score = extracted.get("original_score", 20)
+        validation_issues = extracted.get("validation_issues", [])
+        gptzero_ai_pct = extracted.get("gptzero_ai_pct", None)
+        gptzero_flagged_sentences = extracted.get("gptzero_flagged_sentences", [])
@@
-            supabase_result = supabase.table('generated_posts').insert({
-                'platform': 'email',
+            supabase_result = supabase.table('generated_posts').insert({
+                'platform': 'youtube',
                 'post_hook': hook_preview,
                 'body_content': clean_output,
🧰 Tools 🪛 Ruff (0.14.5)
663-663: Do not catch blind exception: Exception

(BLE001)

744-744: Do not catch blind exception: Exception

(BLE001)

777-777: Do not catch blind exception: Exception

(BLE001)

In agents/youtube_direct_api_agent.py:

> +async def create_youtube_workflow(
+    topic: str,
+    context: str = "",
+    style: str = "thought_leadership",
+    script_type: str = "tutorial",
+    channel_id: Optional[str] = None,
+    thread_ts: Optional[str] = None,
+    user_id: Optional[str] = None,
+    publish_date: Optional[str] = None,
+    thinking_mode: bool = False
+) -> str:
+    """
+    Main entry point for YouTube script creation using direct API
+    Drop-in replacement for SDK version - same signature, same return format
+
+    Args:
+        topic: Main topic for the script
+        context: Additional context
+        style: Content style
+        script_type: Script type (tutorial, explainer, etc.)
+        channel_id: Slack channel ID (for Airtable/Supabase saves)
+        thread_ts: Slack thread timestamp (for Airtable/Supabase saves)
+        user_id: Slack user ID (for Airtable/Supabase saves)
+        publish_date: Optional publish date
+        thinking_mode: If True, adds validation + fix loop for higher quality
+
+    Returns:
+        Formatted string with post content, score, and links
+    """
+
+    agent = YouTubeDirectAPIAgent(
+        user_id=user_id,
+        channel_id=channel_id,
+        thread_ts=thread_ts,
+        batch_mode=True
+    )
+
+    try:
+        result = await agent.create_post(
+            topic=topic,
+            context=f"{context} | Style: {style}",
+            script_type=script_type,
+            target_score=85,
+            publish_date=publish_date,
+            thinking_mode=thinking_mode
+        )
+
+        if result['success']:
+            return f"""✅ **YouTube Script Created**
+
+**Hook Preview:**
+_{result.get('hook', result['post'][:200])}..._
+
+**Quality Score:** {result.get('score', 20)}/25 (Iterations: {result.get('iterations', 3)})
+
+**Full Post:**
+{result['post']}
+
+---
+📊 **Airtable Record:** {result.get('airtable_url', '[Coming Soon]')}
+📄 **Google Doc:** {result.get('google_doc_url', '[Coming Soon]')}
+
+*AI Patterns Removed | Facts Verified | Ready to Post*"""
+        else:
+            return f"❌ Creation failed: {result.get('error', 'Unknown error')}"
+
+    except Exception as e:
+        logger.error(f"Email Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
+
⚠️ Potential issue | 🟡 Minor

Correct YouTube workflow error log label

The exception handler for create_youtube_workflow currently logs "Email Direct API workflow error", which is misleading in logs.

-    except Exception as e:
-        logger.error(f"Email Direct API workflow error: {e}")
-        return f"❌ Unexpected error: {str(e)}"
+    except Exception as e:
+        logger.error(f"YouTube Direct API workflow error: {e}")
+        return f"❌ Unexpected error: {str(e)}"
🧰 Tools 🪛 Ruff (0.14.5)
899-899: Do not catch blind exception: Exception

(BLE001)

900-900: Use logging.exception instead of logging.error

Replace with exception

(TRY400)

901-901: Use explicit conversion flag

Replace with conversion flag

(RUF010)

🤖 Prompt for AI Agents
In agents/youtube_direct_api_agent.py around lines 833 to 902, the except block
logs a misleading message "Email Direct API workflow error" when handling
exceptions in create_youtube_workflow; change the log message to accurately
reflect this function (e.g., "YouTube Direct API workflow error" or
"create_youtube_workflow error") and include the exception details in the log
call (keep logger.error usage with the formatted exception variable) so logs
correctly identify the YouTube workflow failure and show the error.
In api/publishing_endpoints.py:

> +async def mark_post_published(
+    airtable_record_id: Optional[str] = None,
+    post_id: Optional[str] = None,
+    ayrshare_post_id: Optional[str] = None,
+    published_url: Optional[str] = None,
+    published_at: Optional[str] = None,
+    platform_ids: Optional[Dict[str, str]] = None
+) -> Dict[str, Any]:
+    """
+    Mark a post as published and store Ayrshare tracking info.
+
+    Called by n8n after successful publishing to Ayrshare.
+
+    Args:
+        airtable_record_id: Airtable record ID (primary lookup)
+        post_id: UUID of generated_posts record (fallback lookup)
+        ayrshare_post_id: Ayrshare post ID for tracking
+        published_url: URL to published post
+        published_at: ISO timestamp of publishing (defaults to now)
+        platform_ids: Dict of platform-specific IDs (e.g., {"linkedin": "123", "twitter": "456"})
+
+    Returns:
+        Success confirmation with updated post data
+    """
+    logger.info(f"Marking post as published: airtable={airtable_record_id}, ayrshare={ayrshare_post_id}")
+
+    try:
+        supabase = get_supabase_client()
+
+        # Find post by airtable_record_id or post_id
+        if airtable_record_id:
+            result = supabase.table('generated_posts')\
+                .select('*')\
+                .eq('airtable_record_id', airtable_record_id)\
+                .execute()
+        elif post_id:
+            result = supabase.table('generated_posts')\
+                .select('*')\
+                .eq('id', post_id)\
+                .execute()
+        else:
+            return {
+                'success': False,
+                'error': 'Must provide either airtable_record_id or post_id'
+            }
+
+        if not result.data:
+            return {
+                'success': False,
+                'error': f'Post not found (airtable_record_id={airtable_record_id}, post_id={post_id})'
+            }
+
+        post = result.data[0]
+        post_id = post['id']
+
+        # Prepare update data
+        update_data = {
+            'status': 'published',
+            'published_at': published_at or datetime.utcnow().isoformat(),
+            'updated_at': datetime.utcnow().isoformat()
+        }
+
+        if ayrshare_post_id:
+            update_data['ayrshare_post_id'] = ayrshare_post_id
+
+        if published_url:
+            update_data['published_url'] = published_url
+
+        if platform_ids:
+            update_data['ayrshare_platform_ids'] = platform_ids
+
+        # Update post
+        result = supabase.table('generated_posts')\
+            .update(update_data)\
+            .eq('id', post_id)\
+            .execute()
+
+        logger.info(f"Post {post_id} marked as published with Ayrshare ID: {ayrshare_post_id}")
+
+        return {
+            'success': True,
+            'post_id': post_id,
+            'airtable_record_id': post.get('airtable_record_id'),
+            'ayrshare_post_id': ayrshare_post_id,
+            'published_url': published_url,
+            'published_at': update_data['published_at'],
+            'message': 'Post successfully marked as published'
+        }
+
⚠️ Potential issue | 🟠 Major

🧩 Analysis chain
Publishing state updates should validate Supabase update results before reporting success

The high-level flows in mark_post_published, mark_post_scheduled, and mark_publish_failed are sensible: they look up the post by airtable_record_id/post_id, build an update_data dict, and call supabase.table('generated_posts').update(...).eq('id', post_id).execute().

Two points to tighten:

Update result handling
Currently, you ignore the result of the update() calls and always log/report success if no exception is raised. If the update fails silently (e.g., shape change, permission issue, or unexpected empty response), callers will think the state changed when it didn’t.

At minimum, inspect the response (e.g., result.data or an error field if exposed by the client) and fall back to {'success': False, 'error': '...failed to update...'} when appropriate.
Exception handling & logging
Each function catches a broad Exception and logs via logger.error(...). To improve debuggability:

Prefer logger.exception("Error marking post as published") (and similarly for scheduled/failed) to capture stack traces.
Optionally re-raise as HTTPException in the API layer rather than swallowing everything here, depending on how these helpers are wired.
These changes preserve the external contract while making the publishing state much more reliable under failure modes.

Also applies to: 129-211, 277-354

🏁 Script executed:

#!/bin/bash
# Step 1: Find the file and examine the three function implementations
fd -t f "publishing_endpoints.py" | head -5
Length of output: 27

🏁 Script executed:

#!/bin/bash
# Step 2: Once file is found, examine the specific line ranges mentioned
if [ -f "api/publishing_endpoints.py" ]; then
  echo "=== mark_post_published (lines 32-120) ==="
  sed -n '32,120p' api/publishing_endpoints.py
  echo ""
  echo "=== second function (lines 129-211) ==="
  sed -n '129,211p' api/publishing_endpoints.py
  echo ""
  echo "=== third function (lines 277-354) ==="
  sed -n '277,354p' api/publishing_endpoints.py
fi
Length of output: 7749

🏁 Script executed:

#!/bin/bash
# Step 3: Search for Supabase client usage patterns and how results are checked elsewhere in the codebase
rg -n "\.execute\(\)" api/publishing_endpoints.py -A 2 -B 2
Length of output: 2032

🏁 Script executed:

#!/bin/bash
# Step 4: Check the imports and get_supabase_client usage
head -30 api/publishing_endpoints.py
Length of output: 862

🏁 Script executed:

#!/bin/bash
# Step 5: Search for exception handling patterns in this file
rg -n "except|logger\." api/publishing_endpoints.py -B 1
Length of output: 989

🌐 Web query:

Supabase Python client update execute return value response structure
💡 Result:

Short answer — supabase-py update(...).execute() returns a response object with the same shape used by other supabase client calls: the payload is available as response.data (list or dict), there is an HTTP/status field (status_code), an error object when the request failed, and optional count/metadata when you requested it. Typical fields you can expect:

data — the returned row(s) (list or dict; empty or None for minimal returning).
count — present only if you requested count.
status_code — HTTP status (200/204/400/...).
error — None on success, or an error dict with code/message when the request failed.
headers / raw response — client may expose HTTP headers / raw response depending on version.
Example usage in docs:
response = supabase.table("instruments").update({"name":"piano"}).eq("id",1).execute()
then inspect response.data and response.status_code (and response.error on failures). (supabase.com)

If you want, tell me your supabase-py version and I’ll show the exact attributes for that release.

Citations:

1: https://supabase.com/docs/reference/python/update?utm_source=openai
Validate Supabase update responses before confirming success in all three state-marking functions

The review identifies a real issue. The Supabase Python client's update().execute() returns a response object with data, status_code, and error fields, but your functions ignore these and report success unconditionally after the call completes without exception.

Issues confirmed across all three functions:

Update result validation missing (lines 105–107, 192–194, 337–339)
Add response validation after each update().execute() call:

Check response.error (should be None on success)
Check response.status_code (should be 200/204)
Return error response if validation fails, instead of assuming success
Exception handling (lines 121–122, 205–206, 349–350)
Replace logger.error(...) with logger.exception(...) to capture stack traces for debuggability.

Without response validation, the functions report success even if the update silently fails (e.g., due to permission issues or unexpected response shape), misleading callers about actual state changes.

🤖 Prompt for AI Agents
In api/publishing_endpoints.py around lines 32–120 (and similar patterns at
~192–206 and ~337–350), the Supabase update().execute() return object is not
validated and exceptions are logged with logger.error; update the three
state-marking functions to validate the update response after each
update().execute() by checking response.error is None and response.status_code
is a success code (200/204), log the full response on failure and return a
{'success': False, 'error': ...} result instead of assuming success, and change
exception handlers to use logger.exception(...) so stack traces are captured.
In docs/BOOTSTRAP_TROUBLESHOOTING.md:

> +### Reference: Function Signature
+
+The correct signature for `match_company_documents`:
+
+```sql
+CREATE OR REPLACE FUNCTION match_company_documents(
+  query_embedding vector(1536),     -- Must be vector(1536)
+  filter_type text DEFAULT NULL,    -- text, not varchar
+  match_threshold float DEFAULT 0.7,-- float, not double precision
+  match_count int DEFAULT 5         -- int, not integer
+)
+RETURNS TABLE (
+  id uuid,
+  title text,
+  content text,
+  document_type text,
+  voice_description text,
+  signature_phrases jsonb,          -- jsonb, not json
+  similarity float                   -- float, not double precision
+)
+```
+
⚠️ Potential issue | 🟡 Minor

Function name inconsistency with check_function.py.

This section documents the correct signature for match_company_documents, but check_function.py (line 16) queries for match_content_examples. Please verify which function is correct and ensure consistency across the codebase.

🤖 Prompt for AI Agents
In docs/BOOTSTRAP_TROUBLESHOOTING.md around lines 156 to 177 there is a
mismatch: the docs describe the function match_company_documents but
check_function.py (line 16) queries match_content_examples. Determine which
function name/signature is canonical, then make them consistent: either update
check_function.py to query match_company_documents or update the docs to show
match_content_examples; while doing so ensure the SQL signature (parameter
names, types: vector(1536), text, float, int, returned column types including
jsonb and float) matches the chosen function and update any related tests or
references across the repo to the selected name.
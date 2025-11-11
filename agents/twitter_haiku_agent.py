"""
Twitter Haiku Fast Path Agent
Fast single-post generation using Haiku for rapid iteration (1-5 posts)
Bypasses multi-agent process for speed while maintaining quality
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from anthropic import Anthropic, RateLimitError
from utils.anthropic_client import get_anthropic_client
from utils.retry_decorator import async_retry_with_backoff

# Load WRITE_LIKE_HUMAN_RULES and editor-in-chief rules
from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

# Load editor-in-chief rules
EDITOR_FILE_PATH = Path(__file__).parent.parent / "editor-in-chief.md"
try:
    with open(EDITOR_FILE_PATH, 'r', encoding='utf-8') as f:
        EDITOR_IN_CHIEF_RULES = f.read()
except FileNotFoundError:
    print(f"⚠️ Warning: Could not load {EDITOR_FILE_PATH}")
    EDITOR_IN_CHIEF_RULES = "# Editor-in-Chief standards not available"

# Import search functions
from tools.template_search import search_templates_agentic, get_template_by_name
from tools.search_tools import search_content_examples


@async_retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=8.0,
    backoff_factor=2.0,
    exceptions=(ConnectionError, TimeoutError, OSError, RateLimitError),
    context_provider=lambda: {"topic": topic if 'topic' in locals() else "N/A"}
)
async def create_single_post(
    topic: str,
    context: str = "",
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None,
    publish_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a single Twitter post using Haiku fast path

    Args:
        topic: Post topic
        context: Additional context/requirements
        channel_id: Slack channel ID (for tracking)
        thread_ts: Slack thread timestamp (for tracking)
        user_id: Slack user ID (for tracking)
        publish_date: Optional publish date

    Returns:
        Dict with:
            - success: bool
            - post: str (clean post content, no emojis)
            - hook: str (hook preview)
            - score: int (Haiku self-assessment 0-5)
            - error: str (if failed)
    """
    try:
        # Input validation
        if not topic or not topic.strip():
            return {
                'success': False,
                'error': 'Topic cannot be empty',
                'post': '',
                'hook': '',
                'score': 0
            }

        topic = topic.strip()
        print(f"🚀 Twitter Haiku Fast Path: Creating post about '{topic}'")
        
        # Step 1: Search templates with timeout protection
        print("   📚 Searching templates...")
        template_context = ""
        template_names = []

        try:
            # Wrap synchronous search in asyncio with timeout
            template_search_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    search_templates_agentic,
                    topic,
                    3  # max_results
                ),
                timeout=10.0  # 10 second timeout for template search
            )
        except asyncio.TimeoutError:
            print("   ⚠️ Template search timed out after 10s, using defaults")
            template_search_result = None
        except Exception as e:
            print(f"   ⚠️ Template search failed: {e}")
            template_search_result = None

        # Extract template structure from search result with robust parsing
        # Try multiple patterns to extract template names
        if template_search_result:
            lines = template_search_result.split('\n')
            for line in lines:
                # Pattern 1: **1. Template Name**
                if '**' in line and '.' in line:
                    try:
                        # Extract content between ** markers
                        import re
                        matches = re.findall(r'\*\*([^*]+)\*\*', line)
                        if matches:
                            # Try to extract name after number
                            name_part = matches[0]
                            if '. ' in name_part:
                                name = name_part.split('. ', 1)[1]
                            else:
                                name = name_part
                            template_names.append(name.strip())
                    except:
                        pass

                # Pattern 2: Just template names without formatting
                elif 'template' in line.lower() and len(line) < 100:
                    # Might be a plain template name
                    name = line.strip().strip('-').strip('•').strip()
                    if name and name not in template_names:
                        template_names.append(name)

        # Get full template structures for top match if found
        if template_names:
            try:
                template_json = get_template_by_name(template_names[0])
                template_data = json.loads(template_json)
                template_context = f"""
TEMPLATE STRUCTURE:
Name: {template_data.get('name', 'N/A')}
Description: {template_data.get('description', 'N/A')}
Use When: {', '.join(template_data.get('use_when', [])[:3])}
Structure: {json.dumps(template_data.get('structure', {}), indent=2)}
"""
            except Exception as e:
                # Fallback: Use the search result summary
                print(f"   ⚠️ Could not parse template details: {e}")
                template_context = f"Template suggestions:\n{template_search_result[:500]}"
        else:
            # No templates found - use search result or default
            if template_search_result and len(template_search_result) > 50:
                template_context = f"Template guidance:\n{template_search_result[:500]}"
            else:
                template_context = "No specific template found - use general Twitter best practices"
        
        # Step 2: Search content examples with timeout protection
        print("   🔍 Searching content examples...")
        examples_context = ""

        try:
            # Wrap synchronous search in asyncio with timeout
            examples_json = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    search_content_examples,
                    topic,  # query
                    "Twitter",  # platform
                    5  # match_count
                ),
                timeout=10.0  # 10 second timeout for content search
            )
            examples_data = json.loads(examples_json)
        except asyncio.TimeoutError:
            print("   ⚠️ Content examples search timed out after 10s, using defaults")
            examples_data = {'success': False, 'matches': []}
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Failed to parse content examples JSON: {e}")
            examples_data = {'success': False, 'matches': []}
        except Exception as e:
            print(f"   ⚠️ Content examples search failed: {e}")
            examples_data = {'success': False, 'matches': []}

        if examples_data.get('success') and examples_data.get('matches'):
            examples_context = "\nCONTENT EXAMPLES (90-100% human scores):\n"
            for i, match in enumerate(examples_data['matches'][:5], 1):
                examples_context += f"""
Example {i}:
Hook: {match.get('hook', 'N/A')}
Content: {match.get('content', '')[:200]}...
Content Type: {match.get('content_type', 'N/A')}
Human Score: {match.get('human_score', 'N/A')}
"""
        else:
            examples_context = "No specific examples found - use general Twitter best practices"
        
        # Step 3: Build Haiku prompt
        prompt = f"""You are writing a single Twitter post (<280 chars) using proven templates and examples.

WRITE_LIKE_HUMAN_RULES:
{WRITE_LIKE_HUMAN_RULES}

EDITOR-IN-CHIEF RULES:
{EDITOR_IN_CHIEF_RULES}

{template_context}

{examples_context}

TOPIC: {topic}
CONTEXT: {context}

TASK:
Write ONE tweet following the template structure and matching the example patterns.
Apply WRITE_LIKE_HUMAN_RULES strictly to avoid AI tells.
Apply EDITOR-IN-CHIEF RULES to avoid contrast framing, rule of three, and other AI patterns.

CRITICAL REQUIREMENTS:
- Maximum 280 characters
- No markdown formatting (**bold**, *italic*, ##headers)
- No emojis in the post content
- No numbering (1/, 2/, etc.) - this is a single post
- Natural, conversational tone
- Specific and concrete (use numbers/dates if available)
- Hook should grab attention immediately

Return ONLY the tweet text (no numbering, no markdown, no emojis, no explanations).
Just the clean post content."""

        # Step 4: Call Haiku with timeout protection (CRITICAL)
        print("   ⚡ Calling Haiku for generation...")
        client = get_anthropic_client()

        try:
            # CRITICAL: Add 30-second timeout to prevent indefinite hanging
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=500,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )
                ),
                timeout=30.0  # 30 second timeout for Haiku API
            )

            if not response or not response.content or not response.content[0].text:
                raise ValueError("Empty response from Haiku API")

            post_content = response.content[0].text.strip()
        except asyncio.TimeoutError:
            print("   ❌ Haiku API timed out after 30s")
            return {
                'success': False,
                'error': 'Haiku API timed out after 30 seconds',
                'post': '',
                'hook': '',
                'score': 0
            }
        except Exception as e:
            print(f"   ❌ Haiku API call failed: {e}")
            return {
                'success': False,
                'error': f'Haiku API error: {str(e)}',
                'post': '',
                'hook': '',
                'score': 0
            }
        
        # Clean up post content (remove any markdown, numbering, etc.)
        # Remove markdown formatting
        post_content = post_content.replace('**', '').replace('*', '').replace('#', '')
        # Remove numbering like "1/ " or "1. "
        import re
        post_content = re.sub(r'^\d+[/.]\s*', '', post_content, flags=re.MULTILINE)
        # Remove any emojis (basic check)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        post_content = emoji_pattern.sub('', post_content)
        post_content = post_content.strip()
        
        # Validate character limit
        if len(post_content) > 280:
            print(f"   ⚠️ Post exceeds 280 chars ({len(post_content)}), truncating...")
            post_content = post_content[:277] + "..."
        
        # Extract hook (first sentence or first 100 chars)
        hook_preview = post_content.split('.')[0] if '.' in post_content else post_content[:100]
        if len(hook_preview) > 100:
            hook_preview = hook_preview[:97] + "..."
        
        # Simple self-assessment (character-based heuristic)
        # Longer posts with specific details score higher
        char_count = len(post_content)
        has_numbers = bool(re.search(r'\d+', post_content))
        score = 3  # Base score
        if char_count > 200:
            score += 1
        if has_numbers:
            score += 1
        if char_count < 150:
            score -= 1

        print(f"   ✅ Generated post ({len(post_content)} chars, score: {score}/5)")

        # Save to Airtable
        airtable_url = None
        airtable_record_id = None
        try:
            print(f"   🔄 Attempting Airtable save...")
            print(f"   📝 Post length: {len(post_content)} chars")
            print(f"   🏷️  Platform: twitter")
            print(f"   📅 Publish date: {publish_date}")

            from integrations.airtable_client import get_airtable_client
            airtable = get_airtable_client()

            # Determine status based on score
            if score >= 4:
                airtable_status = "Ready"
            elif score >= 3:
                airtable_status = "Draft"
            else:
                airtable_status = "Needs Review"

            print(f"   ✏️  Status: {airtable_status} (score: {score}/5)")

            airtable_result = airtable.create_content_record(
                content=post_content,
                platform='twitter',
                post_hook=hook_preview,
                status=airtable_status,
                suggested_edits=f"Score: {score}/5 (Haiku fast path)",
                publish_date=publish_date
            )

            print(f"   📊 Airtable result: success={airtable_result.get('success')}, keys={list(airtable_result.keys())}")

            if airtable_result.get('success'):
                airtable_url = airtable_result.get('url')
                airtable_record_id = airtable_result.get('record_id')  # Fixed: was 'id', should be 'record_id'
                print(f"   ✅ Saved to Airtable: {airtable_url}")
                print(f"   📋 Airtable record ID: {airtable_record_id}")
            else:
                print(f"   ⚠️ Airtable save failed: {airtable_result.get('error', 'Unknown error')}")
                print(f"   🔍 Full Airtable result: {airtable_result}")
        except Exception as e:
            print(f"   ⚠️ Airtable save failed: {e}")
            import traceback
            traceback.print_exc()

        # Save to Supabase
        supabase_id = None
        try:
            from integrations.supabase_client import get_supabase_client
            from tools.research_tools import generate_embedding

            supabase = get_supabase_client()
            embedding = generate_embedding(post_content)

            supabase_result = supabase.table('generated_posts').insert({
                'platform': 'twitter',
                'post_hook': hook_preview,
                'body_content': post_content,
                'content_type': 'twitter_single',
                'airtable_record_id': airtable_record_id,
                'airtable_url': airtable_url,
                'status': 'draft',
                'quality_score': (score / 5) * 100,  # Convert to 0-100 scale
                'iterations': 1,
                'slack_thread_ts': thread_ts,
                'slack_channel_id': channel_id,
                'user_id': user_id,
                'created_by_agent': 'twitter_haiku_agent',
                'embedding': embedding
            }).execute()

            if supabase_result.data:
                supabase_id = supabase_result.data[0]['id']
                print(f"   ✅ Saved to Supabase: {supabase_id}")
        except Exception as e:
            print(f"   ⚠️ Supabase save failed: {e}")

        return {
            'success': True,
            'post': post_content,
            'hook': hook_preview,
            'score': score,
            'platform': 'twitter',
            'publish_date': publish_date,
            'channel_id': channel_id,
            'thread_ts': thread_ts,
            'user_id': user_id,
            'airtable_url': airtable_url,
            'supabase_id': supabase_id
        }
        
    except Exception as e:
        import traceback
        print(f"   ❌ Error in Haiku fast path: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'post': '',
            'hook': '',
            'score': 0
        }


async def create_twitter_post_workflow(
    topic: str,
    context: str = "",
    style: str = "thought_leadership",
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None,
    publish_date: Optional[str] = None
) -> str:
    """
    Main entry point for Twitter single post creation (Haiku fast path)
    Called by routing logic when single post is detected
    
    Returns:
        Formatted string for Slack (clean post, no emoji indicators)
    """
    result = await create_single_post(
        topic=topic,
        context=f"{context} | Style: {style}",
        channel_id=channel_id,
        thread_ts=thread_ts,
        user_id=user_id,
        publish_date=publish_date
    )
    
    if result['success']:
        # Return clean format for Slack (no emoji indicators in post)
        return f"""✅ Twitter Post Generated

{result['post']}

Hook: {result['hook']}
Score: {result['score']}/5 (Haiku fast path)"""
    else:
        return f"❌ Creation failed: {result.get('error', 'Unknown error')}"


"""
Batch Orchestrator for Sequential Content Execution
Implements Anthropic-aligned sequential execution with context building

Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
"""

import time
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from agents.context_manager import ContextManager

# Global registry of context managers (plan_id -> ContextManager)
_context_managers: Dict[str, ContextManager] = {}

# Global registry of batch plans (plan_id -> plan dict)
_batch_plans: Dict[str, Dict[str, Any]] = {}


async def execute_sequential_batch(
    plan: Dict[str, Any],
    slack_client,
    channel: str,
    thread_ts: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Orchestrates sequential execution of N-post plan with context building
    Uses direct API agent workflows (eliminates SDK hanging issues)

    Args:
        plan: {
            'id': str,
            'count': int,
            'posts': [{
                'topic': str,
                'platform': str,  # linkedin, twitter, email, youtube, instagram
                'context': str,
                'style': str
            }]
        }
        slack_client: Slack WebClient instance
        channel: Slack channel ID
        thread_ts: Thread timestamp for replies
        user_id: User who requested the batch

    Returns:
        {
            'success': bool,
            'completed': int,
            'failed': int,
            'total_time': int (minutes),
            'avg_score': float,
            'quality_trend': str
        }
    """
    context_mgr = ContextManager(plan['id'], plan)
    start_time = time.time()

    completed = 0
    failed = 0

    print(f"\n🚀 Starting batch execution: {len(plan['posts'])} posts (sequential)")
    print(f"📋 Plan ID: {plan['id']}")

    for i, post_spec in enumerate(plan['posts']):
        post_num = i + 1

        # Send progress update to Slack
        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"⏳ Creating post {post_num}/{len(plan['posts'])}...\n"
                 f"Platform: *{post_spec['platform'].capitalize()}*\n"
                 f"Topic: {post_spec['topic'][:100]}",
            mrkdwn=True
        )

        # Get context from strategic outline (NO learning accumulation)
        strategic_context = context_mgr.get_context_for_post(i)

        print(f"\n📝 Post {post_num}/{len(plan['posts'])}")
        print(f"   Platform: {post_spec['platform']}")
        print(f"   Strategic context: {len(strategic_context)} chars")

        # Call direct API agent workflow (NO learning injection)
        try:
            result = await _execute_single_post(
                platform=post_spec['platform'],
                topic=post_spec['topic'],
                context=strategic_context,  # Strategic outline + optional strategy memory
                style=post_spec.get('style', ''),
                learnings='',  # NO LEARNINGS - deprecated parameter
                target_score=18,  # Fixed threshold (no "improving on average")
                publish_date=post_spec.get('publish_date')  # Pass publish date from post spec
            )

            # Extract metadata from SDK agent result
            score = extract_score_from_result(result)
            airtable_url = extract_airtable_url_from_result(result)
            hook = extract_hook_from_result(result)

            # Update context manager
            await context_mgr.add_post_summary({
                'post_num': post_num,
                'score': score,
                'hook': hook,
                'platform': post_spec['platform'],
                'airtable_url': airtable_url,
                'what_worked': f"Score: {score}/25"
            })

            # Send completion update to Slack
            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"✅ Post {post_num}/{len(plan['posts'])} complete!\n"
                     f"📊 <{airtable_url}|View in Airtable>\n"
                     f"🎯 Quality Score: *{score}/25*",
                mrkdwn=True
            )

            completed += 1
            print(f"   ✅ Success: Score {score}/25")

        except Exception as e:
            # Handle errors gracefully - continue with remaining posts
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"⚠️ Post {post_num} failed: {str(e)[:200]}\n\n"
                     f"Continuing with remaining posts...",
                mrkdwn=True
            )

            failed += 1
            continue

        # Checkpoint every 10 posts (or at end if < 10 remaining)
        if post_num % 10 == 0 and post_num < len(plan['posts']):
            stats = context_mgr.get_stats()

            checkpoint_msg = (
                f"✅ *Checkpoint: Posts {post_num-9}-{post_num} complete!*\n\n"
                f"📊 Stats:\n"
                f"- Average score: *{stats['avg_score']:.1f}/25*\n"
                f"- Quality trend: *{stats['quality_trend']}*\n"
                f"- Score range: {stats['lowest_score']}-{stats['highest_score']}\n"
                f"- Recent scores: {stats['recent_scores']}\n\n"
                f"⏳ *{len(plan['posts']) - post_num} posts remaining.* Continuing..."
            )

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=checkpoint_msg,
                mrkdwn=True
            )

            print(f"\n📊 Checkpoint {post_num}")
            print(f"   Avg score: {stats['avg_score']:.1f}")
            print(f"   Trend: {stats['quality_trend']}")

    # Final summary
    elapsed = int((time.time() - start_time) / 60)
    final_stats = context_mgr.get_stats()

    final_msg = (
        f"🎉 *Batch complete! All {len(plan['posts'])} posts created.*\n\n"
        f"📊 *Final Stats:*\n"
        f"- ✅ Completed: *{completed}/{len(plan['posts'])}*\n"
        f"- ❌ Failed: *{failed}*\n"
        f"- ⏱️ Total time: *{elapsed} minutes*\n"
        f"- 📈 Average score: *{final_stats['avg_score']:.1f}/25*\n"
        f"- 📊 Quality trend: *{final_stats['quality_trend']}*\n"
        f"- 🎯 Score range: {final_stats['lowest_score']}-{final_stats['highest_score']}\n\n"
        f"📅 *View all posts in Airtable* (filter by Created Today)\n\n"
        f"🚀 Your content is ready to schedule!"
    )

    slack_client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=final_msg,
        mrkdwn=True
    )

    print(f"\n🎉 Batch execution complete!")
    print(f"   Completed: {completed}/{len(plan['posts'])}")
    print(f"   Time: {elapsed} minutes")

    return {
        'success': failed == 0,
        'completed': completed,
        'failed': failed,
        'total_time': elapsed,
        'avg_score': final_stats['avg_score'],
        'quality_trend': final_stats['quality_trend']
    }


async def _execute_single_post(
    platform: str,
    topic: str,
    context: str,
    style: str,
    learnings: str,
    target_score: int,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None,
    publish_date: Optional[str] = None
) -> str:
    """
    Execute one post using direct API agent workflows
    Eliminates SDK hanging issues (#288, #294)

    Args:
        platform: linkedin, twitter, email, youtube, instagram
        topic: Post topic
        context: Additional context
        style: Content style
        learnings: Compacted learnings from previous posts (deprecated)
        target_score: Target quality score
        channel_id: Slack channel ID (for Airtable/Supabase)
        thread_ts: Slack thread timestamp (for Airtable/Supabase)
        user_id: Slack user ID (for Airtable/Supabase)

    Returns:
        Result string from direct API agent (contains post, score, Airtable URL)
    """
    # Context already contains strategic outline + optional strategy memory
    # NO learning injection - deprecated parameter ignored

    # Normalize platform aliases
    platform_lower = platform.lower()
    if platform_lower in ['x', 'x/twitter']:
        platform = 'twitter'
    else:
        platform = platform_lower

    # Call appropriate direct API agent workflow with Slack metadata
    if platform == "linkedin":
        from agents.linkedin_direct_api_agent import create_linkedin_post_workflow
        result = await create_linkedin_post_workflow(
            topic=topic,
            context=context,  # Strategic outline + optional strategy memory
            style=style or 'thought_leadership',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
            publish_date=publish_date
        )

    elif platform == "twitter":
        # Intelligent routing: Check if this should be a single post (Haiku fast path) or thread (SDK agent)
        # Check context for content_length directive or keywords
        content_length = "auto"
        context_lower = context.lower() if context else ""
        topic_lower = topic.lower() if topic else ""

        # Detect thread keywords (expanded list, includes X/Twitter aliases)
        thread_keywords = ["thread", "thread of", "twitter thread", "x thread", "long thread", "short thread", "a thread", "an x thread", "an twitter thread"]
        is_thread = any(keyword in context_lower or keyword in topic_lower for keyword in thread_keywords)

        # Detect single post keywords (expanded list, includes X/Twitter aliases)
        single_post_keywords = ["single post", "one tweet", "twitter post", "x post", "single tweet", "a tweet", "an x post", "an x tweet", "one x post", "a twitter post", "standalone post", "one post"]
        is_single_post = any(keyword in context_lower or keyword in topic_lower for keyword in single_post_keywords)

        # Check for explicit content_length in context
        if "content_length" in context_lower:
            if "single_post" in context_lower:
                content_length = "single_post"
            elif "short_thread" in context_lower or "long_thread" in context_lower:
                content_length = "thread"

        # IMPROVED ROUTING LOGIC: Use context length and complexity heuristics
        # Context > 500 chars suggests detailed outline → likely needs thread/complex handling → use Direct API
        context_length = len(context) if context else 0
        topic_length = len(topic) if topic else 0

        # Detect narrative/outline indicators (bullet points, numbered lists, multiple paragraphs)
        has_outline = any(indicator in context for indicator in ['\n-', '\n*', '\n1.', '\n2.', '\n•']) if context else False
        has_multiple_paragraphs = context.count('\n\n') >= 2 if context else False

        # Routing decision with smarter defaults
        use_haiku = False
        if is_thread:
            use_haiku = False  # Use SDK agent for threads
        elif is_single_post:
            use_haiku = True  # Use Haiku for single posts
        elif content_length == "single_post":
            use_haiku = True
        elif content_length in ["short_thread", "long_thread"]:
            use_haiku = False
        elif context_length > 500 or has_outline or has_multiple_paragraphs:
            # Complex context suggests need for Direct API agent (better research, validation)
            use_haiku = False
        elif context_length < 100 and topic_length < 100:
            # Very short/vague context → simple post → use Haiku fast path
            use_haiku = True
        else:
            # Default: Use Direct API agent for batch workflows (better quality control)
            # Haiku is reserved for truly simple, short single posts
            use_haiku = False
        
        if use_haiku:
            # Use Haiku fast path for single posts
            from agents.twitter_haiku_agent import create_twitter_post_workflow
            result = await create_twitter_post_workflow(
                topic=topic,
                context=context,
                style=style or 'tactical',
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
                publish_date=publish_date
            )
        else:
            # Use direct API agent for threads
            from agents.twitter_direct_api_agent import create_twitter_post_workflow
            result = await create_twitter_post_workflow(
                topic=topic,
                context=context,  # Strategic outline + optional strategy memory
                style=style or 'tactical',
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
                publish_date=publish_date
            )

    elif platform == "email":
        from agents.email_direct_api_agent import create_email_workflow
        result = await create_email_workflow(
            topic=topic,
            context=context,  # Strategic outline + optional strategy memory
            email_type=style or 'Email_Value',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
            publish_date=publish_date
        )

    elif platform == "youtube":
        from agents.youtube_direct_api_agent import create_youtube_script_workflow
        result = await create_youtube_script_workflow(
            topic=topic,
            context=context,  # Strategic outline + optional strategy memory
            script_type=style or 'educational',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
            publish_date=publish_date
        )

    elif platform == "instagram":
        from agents.instagram_direct_api_agent import create_instagram_workflow
        result = await create_instagram_workflow(
            topic=topic,
            context=context,  # Strategic outline + optional strategy memory
            style=style or 'inspirational',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
            publish_date=publish_date
        )

    else:
        raise ValueError(f"Unknown platform: {platform}")

    return result


# ============= Helper Functions for Extracting Data from SDK Agent Results =============

def extract_score_from_result(result) -> int:
    """
    Extract quality score from SDK agent result

    SDK agents can return either:
    - A dict with 'score' key (when in isolated mode)
    - A formatted string with "Quality Score: 22/25"

    Args:
        result: Result from SDK agent (dict or string)

    Returns:
        Score as integer (0-25)
    """
    # Handle dict result (SDK agents in isolated mode)
    if isinstance(result, dict):
        return result.get('score', 20)

    # Handle string result (workflow functions)
    # Formats: "**Quality Score:** 22/25", "Quality Score: 22/25", "Score: 90/100"
    # Updated pattern to handle markdown asterisks and any formatting
    score_match = re.search(r'Quality\s+Score.*?(\d+)\s*/\s*(\d+)', str(result), re.IGNORECASE | re.DOTALL)

    if score_match:
        score = int(score_match.group(1))
        max_score = int(score_match.group(2))

        # Normalize to 25-point scale
        if max_score == 100:
            score = int(score / 4)  # Convert 100-point to 25-point
        elif max_score != 25:
            # Unexpected max score - normalize proportionally
            score = int((score / max_score) * 25)

        return min(25, max(0, score))

    # Fallback: Default to 20 if not found
    result_preview = str(result)[:200] if result else "Empty result"
    print(f"⚠️ Could not extract score from result (first 200 chars): {result_preview}...")
    print(f"   Defaulting to 20/25")
    return 20


def extract_airtable_url_from_result(result) -> str:
    """
    Extract Airtable URL from SDK agent result

    SDK agents can return either:
    - A dict with 'airtable_url' key
    - A formatted string with the URL

    Args:
        result: Result from SDK agent (dict or string)

    Returns:
        Airtable URL or placeholder
    """
    # Handle dict result
    if isinstance(result, dict):
        return result.get('airtable_url')

    # Handle string result - try to find Airtable URL
    url_match = re.search(r'https://airtable\.com/[^\s\)]+', str(result))

    if url_match:
        return url_match.group(0)

    # Fallback: Return placeholder
    print(f"⚠️ Could not extract Airtable URL from result")
    return "https://airtable.com/[record_not_found]"


def extract_hook_from_result(result) -> str:
    """
    Extract post hook from SDK agent result

    SDK agents can return either:
    - A dict with 'hook' key
    - A formatted string with hook preview

    Args:
        result: Result from SDK agent (dict or string)

    Returns:
        Hook text (first 100 chars)
    """
    # Handle dict result
    if isinstance(result, dict):
        hook = result.get('hook', '')
        if not hook:
            # Fallback to post/thread/caption content
            hook = result.get('post', result.get('thread', result.get('caption', '')))[:200]
        return hook[:100] if hook else "No hook found"

    # Handle string result - try to find hook preview section
    hook_match = re.search(r'Hook Preview[:\s]+([^\n]+)', str(result), re.IGNORECASE)

    if hook_match:
        hook = hook_match.group(1).strip()
        # Remove markdown formatting
        hook = re.sub(r'[_*`]', '', hook)
        return hook[:100]

    # Fallback: Try to find "Full Post:" and extract first line
    post_match = re.search(r'Full Post[:\s]+([^\n]+)', str(result), re.IGNORECASE)
    if post_match:
        hook = post_match.group(1).strip()
        hook = re.sub(r'[_*`]', '', hook)
        return hook[:100]

    # Last fallback: Extract first 100 chars of result
    clean_result = re.sub(r'[_*`#]', '', result)
    return clean_result[:100]


# ============= CMO Agent Tool Helper Functions =============

def create_batch_plan(
    posts: List[Dict[str, Any]],
    description: str,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None,
    slack_client=None  # NEW: Slack client for progress updates
) -> Dict[str, Any]:
    """
    Create a batch plan and store it in the global registry with RICH context preservation

    Args:
        posts: List of post specs [{"platform": "...", "topic": "...", "context": "...", "detailed_outline": "..."}]
        description: High-level description of the batch
        channel_id: Slack channel ID (for saving to Airtable)
        thread_ts: Slack thread timestamp (for saving to Airtable)
        user_id: Slack user ID (for saving to Airtable)

    Returns:
        Plan dict with ID and context_quality assessment
    """
    plan_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Validate context richness for each post
    for i, post in enumerate(posts):
        # Check for detailed_outline or rich context
        outline = post.get('detailed_outline', '')
        context = post.get('context', '')
        combined_length = len(outline) + len(context)

        if combined_length < 200:
            print(f"⚠️ WARNING: Post {i+1} has sparse context ({combined_length} chars)")
            print(f"   Topic: {post.get('topic', 'Unknown')}")
            print(f"   Consider adding 'detailed_outline' field with full strategic narrative")

    # NEW: Analyze context quality across all posts (including detailed_outline)
    context_lengths = [
        len(p.get('detailed_outline', '')) + len(p.get('context', ''))
        for p in posts
    ]
    avg_context = sum(context_lengths) / len(context_lengths) if context_lengths else 0

    # Determine context quality level (adjusted for detailed_outline support)
    if avg_context < 50:
        context_quality = "sparse"  # Minimal context, use thought leadership
    elif avg_context < 150:
        context_quality = "medium"  # Some context, blend proof + opinion
    else:
        context_quality = "rich"  # Rich context with detailed outline, full proof posts

    plan = {
        'id': plan_id,
        'description': description,
        'posts': posts,  # Now includes detailed_outline field
        'context_quality': context_quality,
        'avg_context_length': avg_context,  # NEW: Track average context length
        'detailed_outlines': [p.get('detailed_outline', '') for p in posts],  # NEW: Extract all outlines
        'created_at': datetime.now().isoformat(),
        # Store Slack metadata for SDK agents to use when saving to Airtable
        'slack_metadata': {
            'channel_id': channel_id,
            'thread_ts': thread_ts,
            'user_id': user_id,
            'slack_client': slack_client  # NEW: Store slack_client reference for progress updates
        }
    }

    # Store plan in global registry
    _batch_plans[plan_id] = plan

    # Create context manager for this plan (pass plan so it can extract detailed_outlines)
    _context_managers[plan_id] = ContextManager(plan_id, plan)

    print(f"📋 Created batch plan: {plan_id} with {len(posts)} posts (context: {context_quality})")

    return plan


async def execute_single_post_from_plan(plan_id: str, post_index: int) -> Dict[str, Any]:
    """
    Execute a single post from a batch plan

    Args:
        plan_id: ID from create_batch_plan
        post_index: Which post to create (0-indexed)

    Returns:
        {
            'success': bool,
            'score': int,
            'platform': str,
            'hook': str,
            'airtable_url': str,
            'error': str (if failed)
        }
    """
    # Get plan from registry
    plan = _batch_plans.get(plan_id)
    if not plan:
        return {
            'success': False,
            'error': f"Plan {plan_id} not found",
            'platform': 'unknown',
            'score': 0,
            'hook': '',
            'airtable_url': None
        }

    # Get context manager
    context_mgr = _context_managers.get(plan_id)
    if not context_mgr:
        return {
            'success': False,
            'error': f"Context manager not found for plan {plan_id}",
            'platform': 'unknown',
            'score': 0,
            'hook': '',
            'airtable_url': None
        }

    # Validate post index
    if post_index < 0 or post_index >= len(plan['posts']):
        return {
            'success': False,
            'error': f"Invalid post_index {post_index}. Plan has {len(plan['posts'])} posts.",
            'platform': 'unknown',
            'score': 0,
            'hook': '',
            'airtable_url': None
        }

    post_spec = plan['posts'][post_index]

    # NEW: Get context quality from plan
    context_quality = plan.get('context_quality', 'medium')

    # NEW: Get Slack metadata from plan
    slack_metadata = plan.get('slack_metadata', {})
    channel_id = slack_metadata.get('channel_id')
    thread_ts = slack_metadata.get('thread_ts')
    user_id = slack_metadata.get('user_id')

    # Get strategic context for this post (NO learning accumulation)
    strategic_context = context_mgr.get_context_for_post(post_index)

    # Get slack_client from plan metadata for progress updates
    slack_client = slack_metadata.get('slack_client')
    total_posts = len(plan['posts'])
    post_num = post_index + 1

    print(f"\n📝 Executing post {post_num}/{total_posts}", flush=True)
    print(f"   Platform: {post_spec['platform']}", flush=True)
    print(f"   Strategic context: {len(strategic_context)} chars", flush=True)
    print(f"   Slack context: channel={channel_id}, thread={thread_ts}, user={user_id}", flush=True)

    # Send batch start notification for first post only
    if post_index == 0 and slack_client and channel_id and thread_ts:
        try:
            batch_start_message = (
                f"🚀 *Starting batch execution*\n"
                f"📋 Plan: `{plan_id}`\n"
                f"📝 {total_posts} post{'s' if total_posts > 1 else ''} queued\n"
                f"⏳ Creating posts sequentially..."
            )
            slack_client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=batch_start_message,
                mrkdwn=True
            )
            print(f"   ✅ Sent batch start notification to Slack", flush=True)
        except Exception as e:
            # Log but don't crash batch if Slack update fails
            print(f"   ⚠️ Failed to send batch start notification: {e}", flush=True)

    # Helper function to send progress updates (non-blocking, no user tag)
    # Only sends updates for batches with more than 1 post
    def _send_progress_update(message: str):
        """Send progress update to Slack (non-blocking, no user tag) - only for batches > 1"""
        if total_posts > 1 and slack_client and channel_id and thread_ts:
            try:
                # Send asynchronously without blocking
                slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=message,  # NO user tag - silent progress update
                    mrkdwn=True
                )
            except Exception as e:
                # Log but don't crash batch if Slack update fails
                print(f"   ⚠️ Failed to send progress update: {e}", flush=True)

    try:
        # Execute post using SDK agent with strategic context AND Slack metadata
        # Hard timeout wrapper: Prevent infinite hangs (belt + suspenders with SDK disconnect())
        result = await asyncio.wait_for(
            _execute_single_post(
                platform=post_spec['platform'],
                topic=post_spec['topic'],
                context=strategic_context,  # Strategic outline + optional strategy memory
                style=post_spec.get('style', ''),
                learnings='',  # NO LEARNINGS - deprecated parameter
                target_score=18,  # Fixed threshold
                # Pass Slack metadata for Airtable/Supabase saves
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id
            ),
            timeout=360  # 6 minutes max per post (allows for validation-heavy posts with GPTZero)
        )

        # CRITICAL: Force cleanup to prevent connection exhaustion
        # This fixes the Post 6+ hang issue by ensuring all resources are freed
        await asyncio.sleep(3)  # Increased from 2 to 3 seconds for connection cleanup

        # Force garbage collection to clean up any lingering connections
        import gc
        gc.collect()

        # Additional cleanup delay after GC
        await asyncio.sleep(1)

        print(f"   ✅ Post {post_index + 1} cleanup complete (GC forced), ready for next post", flush=True)

        # Extract metadata
        score = extract_score_from_result(result)
        airtable_url = extract_airtable_url_from_result(result)
        hook = extract_hook_from_result(result)

        # NEW: Check strategic alignment if outline was provided
        if post_spec.get('detailed_outline'):
            context_mgr.add_strategic_context(post_index, post_spec['detailed_outline'])
            # Handle both dict and string results
            if isinstance(result, dict):
                content = result.get('content', result.get('post', ''))
            else:
                content = str(result)
            alignment = context_mgr.check_alignment(post_index, content)

            if alignment < 0.5:
                print(f"   ⚠️ Post {post_num} has low strategic alignment: {alignment:.1%}")
                print(f"      Consider reviewing if content matches intended outline")
            else:
                print(f"   ✅ Post {post_num} strategic alignment: {alignment:.1%}")

        # Update context manager
        await context_mgr.add_post_summary({
            'post_num': post_num,
            'score': score,
            'hook': hook,
            'platform': post_spec['platform'],
            'airtable_url': airtable_url
        })

        print(f"   ✅ Success: Score {score}/25")

        # Send "Post X complete" message AFTER success (non-blocking, no user tag)
        # Only for batches with more than 1 post
        if total_posts > 1:
            completion_message = (
                f"✅ Post {post_num}/{total_posts} complete! "
                f"Score: *{score}/25*"
            )
            if airtable_url:
                completion_message += f" | <{airtable_url}|View>"
            _send_progress_update(completion_message)

        return {
            'success': True,
            'score': score,
            'platform': post_spec['platform'],
            'hook': hook,
            'airtable_url': airtable_url,
            'full_result': result  # Include full SDK agent result for single-post display
        }

    except asyncio.TimeoutError:
        # Hard timeout hit - post took >6 minutes (likely connection hang or validation loop)
        print(f"   ⏱️ TIMEOUT: Post {post_num} exceeded 6-minute limit")
        print(f"   This usually means validation took too long (GPTZero + multiple iterations)")

        # Send timeout progress update (non-blocking, no user tag) - only for batches > 1
        if total_posts > 1:
            timeout_message = (
                f"⚠️ Post {post_num}/{total_posts} timed out (6 min limit). Continuing..."
            )
            _send_progress_update(timeout_message)

        return {
            'success': False,
            'score': 0,
            'platform': post_spec['platform'],
            'hook': f"Post {post_num} timed out after 5 minutes",
            'airtable_url': None,
            'error': f"Timeout after 300s - likely connection hang. Check SDK disconnect() calls."
        }

    except Exception as e:
        print(f"   ❌ Post creation error: {e}")
        import traceback
        traceback.print_exc()

        # Return structured error so batch can continue
        # Include enough info for user to see what went wrong
        error_msg = str(e)[:300]  # Truncate long errors

        # Send error progress update (non-blocking, no user tag) - only for batches > 1
        if total_posts > 1:
            error_update_message = (
                f"⚠️ Post {post_num}/{total_posts} failed: {error_msg[:100]}... Continuing..."
            )
            _send_progress_update(error_update_message)

        return {
            'success': False,
            'score': 0,
            'platform': post_spec['platform'],
            'hook': f"Post {post_num} failed - {error_msg[:50]}...",
            'airtable_url': None,
            'error': error_msg
        }


def get_context_manager(plan_id: str) -> Optional[ContextManager]:
    """
    Get context manager for a plan

    Args:
        plan_id: ID from create_batch_plan

    Returns:
        ContextManager instance or None
    """
    return _context_managers.get(plan_id)


async def diversify_topics(
    topic: str,
    count: int,
    platform: str = "linkedin"
) -> List[Dict[str, Any]]:
    """
    Expand vague topic into N unique angles (thought leadership approach)

    Used when user has NO company docs AND skips context questions

    Distribution:
    - 40% Thought Leadership (contrarian takes, opinions, predictions)
    - 35% Tactical/Educational (how-to, frameworks, common mistakes)
    - 25% Story-Based (personal experiences, lessons learned)

    Args:
        topic: Vague topic (e.g., "AI", "blockchain", "remote work")
        count: Number of unique angles to generate
        platform: Target platform (default "linkedin")

    Returns:
        List of post specs with diversified angles:
        [
            {"platform": "linkedin", "topic": "Why AI isn't a bubble", "context": "Type: thought_leadership...", "style": "thought_leadership"},
            {"platform": "linkedin", "topic": "AI agents vs chatbots", "context": "Type: educational...", "style": "educational"},
            ...
        ]
    """
    from anthropic import Anthropic
    import json

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Calculate distribution
    thought_leadership_count = int(count * 0.40)
    tactical_count = int(count * 0.35)
    story_count = count - thought_leadership_count - tactical_count  # Remainder

    prompt = f"""Expand "{topic}" into {count} unique {platform} post angles.

IMPORTANT: User has NO company documents and chose thought leadership approach.
Posts will be 800-1000 chars, idea-driven, opinion-based (NO proof claims).

Distribution:
- {thought_leadership_count} Thought Leadership: Contrarian takes, bold opinions, predictions, observations
- {tactical_count} Tactical/Educational: How-tos, frameworks, common mistakes, lessons
- {story_count} Story-Based: Hypothetical experiences, lessons learned, journey observations

Return JSON array with this structure:
[
  {{
    "angle": "Why AI isn't a bubble (contrarian take)",
    "type": "thought_leadership"
  }},
  {{
    "angle": "5 AI tools most people ignore",
    "type": "tactical"
  }},
  {{
    "angle": "My journey from AI skeptic to believer",
    "type": "story"
  }}
]

CRITICAL RULES:
- Each angle must be SPECIFIC and UNIQUE
- Avoid generic angles like "The future of AI" or "AI trends"
- Focus on OPINIONS and IDEAS (not data/proof)
- Angles should spark curiosity or challenge assumptions

Generate {count} unique angles now:"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Find JSON array in response
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1

        if start_idx == -1 or end_idx == 0:
            # Fallback: couldn't parse JSON
            print(f"⚠️ Could not parse JSON from diversify_topics response")
            angles = _generate_fallback_angles(topic, count)
        else:
            json_str = response_text[start_idx:end_idx]
            angles = json.loads(json_str)

        # Build post specs
        diversified = []
        for i, angle_spec in enumerate(angles[:count]):  # Limit to exact count
            post_type = angle_spec.get('type', 'thought_leadership')

            diversified.append({
                "platform": platform,
                "topic": angle_spec['angle'],
                "context": f"""Type: {post_type}

**Thought Leadership Style:**
- 800-1000 chars (shorter than proof posts)
- Idea-driven, opinion-based
- "I believe X because Y" framing
- NO hallucinated stats or fake examples
- Focus on frameworks, predictions, contrarian takes

This is post {i+1}/{count} in the batch.""",
                "style": "thought_leadership"
            })

        print(f"✅ Diversified '{topic}' into {len(diversified)} unique angles")
        return diversified

    except Exception as e:
        print(f"❌ Error diversifying topics: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to simple angle generation
        return _generate_fallback_angles(topic, count, platform)


def _generate_fallback_angles(topic: str, count: int, platform: str = "linkedin") -> List[Dict[str, Any]]:
    """
    Fallback angle generation if LLM call fails

    Generates simple angles like:
    - "The future of [topic]"
    - "Why [topic] matters"
    - "Common [topic] mistakes"
    """
    angle_templates = [
        f"Why {topic} isn't what you think",
        f"The {topic} productivity paradox",
        f"{topic}: Contrarian take",
        f"5 {topic} mistakes everyone makes",
        f"How to actually use {topic}",
        f"The {topic} framework nobody talks about",
        f"My {topic} journey (lessons learned)",
        f"When NOT to use {topic}",
        f"{topic} ethics without the buzzwords",
        f"The future of {topic} (prediction)",
    ]

    fallback = []
    for i in range(count):
        template_idx = i % len(angle_templates)
        fallback.append({
            "platform": platform,
            "topic": angle_templates[template_idx],
            "context": f"""Type: thought_leadership

**Thought Leadership Style:**
- 800-1000 chars
- Idea-driven, opinion-based
- NO hallucinated stats or fake examples

This is post {i+1}/{count} in the batch.""",
            "style": "thought_leadership"
        })

    return fallback

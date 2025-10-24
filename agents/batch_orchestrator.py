"""
Batch Orchestrator for Sequential Content Execution
Implements Anthropic-aligned sequential execution with context building

Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
"""

import time
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
    Uses EXISTING SDK agent workflows (NO CHANGES to SDK agents required)

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
    context_mgr = ContextManager(plan['id'])
    start_time = time.time()

    completed = 0
    failed = 0

    print(f"\n🚀 Starting batch execution: {len(plan['posts'])} posts")
    print(f"📋 Plan ID: {plan['id']}")

    for i, post_spec in enumerate(plan['posts']):
        post_num = i + 1

        # Send progress update to Slack
        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"⏳ Creating post {post_num}/{len(plan['posts'])}...\n"
                 f"Platform: **{post_spec['platform'].capitalize()}**\n"
                 f"Topic: {post_spec['topic'][:100]}"
        )

        # Get compacted learnings from previous posts
        learnings = context_mgr.get_compacted_learnings()

        # Calculate target score (improve on average)
        target_score = context_mgr.get_target_score()

        print(f"\n📝 Post {post_num}/{len(plan['posts'])}")
        print(f"   Platform: {post_spec['platform']}")
        print(f"   Target score: {target_score}+")
        print(f"   Learnings: {len(learnings)} chars")

        # Call EXISTING SDK agent workflow (NO CHANGES to SDK agents)
        try:
            result = await _execute_single_post(
                platform=post_spec['platform'],
                topic=post_spec['topic'],
                context=post_spec.get('context', ''),
                style=post_spec.get('style', ''),
                learnings=learnings,
                target_score=target_score
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
                     f"🎯 Quality Score: **{score}/25**"
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
                     f"Continuing with remaining posts..."
            )

            failed += 1
            continue

        # Checkpoint every 10 posts (or at end if < 10 remaining)
        if post_num % 10 == 0 and post_num < len(plan['posts']):
            stats = context_mgr.get_stats()

            checkpoint_msg = (
                f"✅ **Checkpoint: Posts {post_num-9}-{post_num} complete!**\n\n"
                f"📊 Stats:\n"
                f"- Average score: **{stats['avg_score']:.1f}/25**\n"
                f"- Quality trend: **{stats['quality_trend']}**\n"
                f"- Score range: {stats['lowest_score']}-{stats['highest_score']}\n"
                f"- Recent scores: {stats['recent_scores']}\n\n"
                f"📝 Key learnings (last 10 posts):\n"
                f"{stats['learnings'][:500]}...\n\n"
                f"⏳ **{len(plan['posts']) - post_num} posts remaining.** Continuing..."
            )

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=checkpoint_msg
            )

            print(f"\n📊 Checkpoint {post_num}")
            print(f"   Avg score: {stats['avg_score']:.1f}")
            print(f"   Trend: {stats['quality_trend']}")

    # Final summary
    elapsed = int((time.time() - start_time) / 60)
    final_stats = context_mgr.get_stats()

    final_msg = (
        f"🎉 **Batch complete! All {len(plan['posts'])} posts created.**\n\n"
        f"📊 **Final Stats:**\n"
        f"- ✅ Completed: **{completed}/{len(plan['posts'])}**\n"
        f"- ❌ Failed: **{failed}**\n"
        f"- ⏱️ Total time: **{elapsed} minutes**\n"
        f"- 📈 Average score: **{final_stats['avg_score']:.1f}/25**\n"
        f"- 📊 Quality trend: **{final_stats['quality_trend']}**\n"
        f"- 🎯 Score range: {final_stats['lowest_score']}-{final_stats['highest_score']}\n\n"
        f"📅 **View all posts in Airtable** (filter by Created Today)\n\n"
        f"🚀 Your content is ready to schedule!"
    )

    slack_client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=final_msg
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
    target_score: int
) -> str:
    """
    Execute one post using EXISTING SDK agent workflows
    Passes learnings via context parameter (SDK agents already accept this)

    Args:
        platform: linkedin, twitter, email, youtube, instagram
        topic: Post topic
        context: Additional context
        style: Content style
        learnings: Compacted learnings from previous posts
        target_score: Target quality score

    Returns:
        Result string from SDK agent (contains post, score, Airtable URL)
    """
    # Build enhanced context with learnings and target
    enhanced_context = f"""{context}

**Learnings from previous posts in this batch:**
{learnings}

**Target quality score:** {target_score}+ out of 25

Apply the learnings above to improve this post. Focus on what worked well in previous posts."""

    # Call appropriate SDK agent workflow
    if platform == "linkedin":
        from agents.linkedin_sdk_agent import create_linkedin_post_workflow
        result = await create_linkedin_post_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'thought_leadership'
        )

    elif platform == "twitter":
        from agents.twitter_sdk_agent import create_twitter_thread_workflow
        result = await create_twitter_thread_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'tactical'
        )

    elif platform == "email":
        from agents.email_sdk_agent import create_email_workflow
        result = await create_email_workflow(
            topic=topic,
            context=enhanced_context,
            email_type=style or 'Email_Value'
        )

    elif platform == "youtube":
        from agents.youtube_sdk_agent import create_youtube_workflow
        result = await create_youtube_workflow(
            topic=topic,
            context=enhanced_context,
            script_type=style or 'educational'
        )

    elif platform == "instagram":
        from agents.instagram_sdk_agent import create_instagram_post_workflow
        result = await create_instagram_post_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'inspirational'
        )

    else:
        raise ValueError(f"Unknown platform: {platform}")

    return result


# ============= Helper Functions for Extracting Data from SDK Agent Results =============

def extract_score_from_result(result: str) -> int:
    """
    Extract quality score from SDK agent result string

    SDK agents return formatted strings like:
    "Quality Score: 22/100" or "Quality Score: 22/25"

    Args:
        result: Result string from SDK agent

    Returns:
        Score as integer (0-25 or 0-100, normalized to 25)
    """
    # Try to find score pattern
    score_match = re.search(r'Quality Score[:\s]+(\d+)(?:/(\d+))?', result, re.IGNORECASE)

    if score_match:
        score = int(score_match.group(1))
        max_score = int(score_match.group(2)) if score_match.group(2) else 25

        # Normalize to 25-point scale
        if max_score == 100:
            score = int(score / 4)  # Convert 100-point to 25-point

        return min(25, max(0, score))

    # Fallback: Default to 20 if not found
    print(f"⚠️ Could not extract score from result, defaulting to 20")
    return 20


def extract_airtable_url_from_result(result: str) -> str:
    """
    Extract Airtable URL from SDK agent result string

    SDK agents include URLs like:
    "Airtable Record: https://airtable.com/app.../rec..."

    Args:
        result: Result string from SDK agent

    Returns:
        Airtable URL or placeholder
    """
    # Try to find Airtable URL
    url_match = re.search(r'https://airtable\.com/[^\s\)]+', result)

    if url_match:
        return url_match.group(0)

    # Fallback: Return placeholder
    print(f"⚠️ Could not extract Airtable URL from result")
    return "https://airtable.com/[record_not_found]"


def extract_hook_from_result(result: str) -> str:
    """
    Extract post hook from SDK agent result string

    SDK agents include hook preview like:
    "Hook Preview: [hook text]"

    Args:
        result: Result string from SDK agent

    Returns:
        Hook text (first 100 chars)
    """
    # Try to find hook preview section
    hook_match = re.search(r'Hook Preview[:\s]+([^\n]+)', result, re.IGNORECASE)

    if hook_match:
        hook = hook_match.group(1).strip()
        # Remove markdown formatting
        hook = re.sub(r'[_*`]', '', hook)
        return hook[:100]

    # Fallback: Try to find "Full Post:" and extract first line
    post_match = re.search(r'Full Post[:\s]+([^\n]+)', result, re.IGNORECASE)
    if post_match:
        hook = post_match.group(1).strip()
        hook = re.sub(r'[_*`]', '', hook)
        return hook[:100]

    # Last fallback: Extract first 100 chars of result
    clean_result = re.sub(r'[_*`#]', '', result)
    return clean_result[:100]


# ============= CMO Agent Tool Helper Functions =============

def create_batch_plan(posts: List[Dict[str, Any]], description: str) -> Dict[str, Any]:
    """
    Create a batch plan and store it in the global registry

    Args:
        posts: List of post specs [{"platform": "...", "topic": "...", "context": "..."}]
        description: High-level description of the batch

    Returns:
        Plan dict with ID
    """
    plan_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    plan = {
        'id': plan_id,
        'description': description,
        'posts': posts,
        'created_at': datetime.now().isoformat()
    }

    # Store plan in global registry
    _batch_plans[plan_id] = plan

    # Create context manager for this plan
    _context_managers[plan_id] = ContextManager(plan_id)

    print(f"📋 Created batch plan: {plan_id} with {len(posts)} posts")

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
            'learnings_summary': str,
            'error': str (if failed)
        }
    """
    # Get plan from registry
    plan = _batch_plans.get(plan_id)
    if not plan:
        return {'error': f"Plan {plan_id} not found"}

    # Get context manager
    context_mgr = _context_managers.get(plan_id)
    if not context_mgr:
        return {'error': f"Context manager not found for plan {plan_id}"}

    # Validate post index
    if post_index < 0 or post_index >= len(plan['posts']):
        return {'error': f"Invalid post_index {post_index}. Plan has {len(plan['posts'])} posts."}

    post_spec = plan['posts'][post_index]

    # Get learnings from previous posts
    learnings = context_mgr.get_compacted_learnings()
    target_score = context_mgr.get_target_score()

    print(f"\n📝 Executing post {post_index + 1}/{len(plan['posts'])}")
    print(f"   Platform: {post_spec['platform']}")
    print(f"   Target score: {target_score}+")

    try:
        # Execute post using SDK agent
        result = await _execute_single_post(
            platform=post_spec['platform'],
            topic=post_spec['topic'],
            context=post_spec.get('context', ''),
            style=post_spec.get('style', ''),
            learnings=learnings,
            target_score=target_score
        )

        # Extract metadata
        score = extract_score_from_result(result)
        airtable_url = extract_airtable_url_from_result(result)
        hook = extract_hook_from_result(result)

        # Update context manager
        await context_mgr.add_post_summary({
            'post_num': post_index + 1,
            'score': score,
            'hook': hook,
            'platform': post_spec['platform'],
            'airtable_url': airtable_url,
            'what_worked': f"Score: {score}/25"
        })

        # Get learnings summary
        stats = context_mgr.get_stats()
        learnings_summary = f"Average score: {stats['avg_score']:.1f}/25. Recent scores: {stats['recent_scores']}"

        print(f"   ✅ Success: Score {score}/25")

        return {
            'success': True,
            'score': score,
            'platform': post_spec['platform'],
            'hook': hook,
            'airtable_url': airtable_url,
            'learnings_summary': learnings_summary
        }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e)
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

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
    target_score: int,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None
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
        channel_id: Slack channel ID (for Airtable/Supabase)
        thread_ts: Slack thread timestamp (for Airtable/Supabase)
        user_id: Slack user ID (for Airtable/Supabase)

    Returns:
        Result string from SDK agent (contains post, score, Airtable URL)
    """
    # Build enhanced context with learnings and target
    enhanced_context = f"""{context}

**Learnings from previous posts in this batch:**
{learnings}

**Target quality score:** {target_score}+ out of 25

Apply the learnings above to improve this post. Focus on what worked well in previous posts."""

    # Call appropriate SDK agent workflow with Slack metadata
    if platform == "linkedin":
        from agents.linkedin_sdk_agent import create_linkedin_post_workflow
        result = await create_linkedin_post_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'thought_leadership',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
        )

    elif platform == "twitter":
        from agents.twitter_sdk_agent import create_twitter_thread_workflow
        result = await create_twitter_thread_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'tactical',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
        )

    elif platform == "email":
        from agents.email_sdk_agent import create_email_workflow
        result = await create_email_workflow(
            topic=topic,
            context=enhanced_context,
            email_type=style or 'Email_Value',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
        )

    elif platform == "youtube":
        from agents.youtube_sdk_agent import create_youtube_workflow
        result = await create_youtube_workflow(
            topic=topic,
            context=enhanced_context,
            script_type=style or 'educational',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
        )

    elif platform == "instagram":
        from agents.instagram_sdk_agent import create_instagram_post_workflow
        result = await create_instagram_post_workflow(
            topic=topic,
            context=enhanced_context,
            style=style or 'inspirational',
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
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
    # Try to find score pattern - handle multiple formats
    # Formats: "Quality Score: 22/25", "Score: 90/100", "score:22/25"
    score_match = re.search(r'(?:Quality\s+)?Score[:\s]*(\d+)\s*/\s*(\d+)', result, re.IGNORECASE)

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
    print(f"⚠️ Could not extract score from result (first 200 chars): {result[:200]}...")
    print(f"   Defaulting to 20/25")
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

def create_batch_plan(
    posts: List[Dict[str, Any]],
    description: str,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a batch plan and store it in the global registry

    Args:
        posts: List of post specs [{"platform": "...", "topic": "...", "context": "..."}]
        description: High-level description of the batch
        channel_id: Slack channel ID (for saving to Airtable)
        thread_ts: Slack thread timestamp (for saving to Airtable)
        user_id: Slack user ID (for saving to Airtable)

    Returns:
        Plan dict with ID and context_quality assessment
    """
    plan_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # NEW: Analyze context quality across all posts
    total_context_chars = sum(len(p.get('context', '')) for p in posts)
    avg_context = total_context_chars / len(posts) if posts else 0

    # Determine context quality level
    if avg_context < 100:
        context_quality = "sparse"  # Minimal context, use thought leadership
    elif avg_context < 300:
        context_quality = "medium"  # Some context, blend proof + opinion
    else:
        context_quality = "rich"  # Rich context, full proof posts

    plan = {
        'id': plan_id,
        'description': description,
        'posts': posts,
        'context_quality': context_quality,  # NEW: Track for SDK agents
        'created_at': datetime.now().isoformat(),
        # Store Slack metadata for SDK agents to use when saving to Airtable
        'slack_metadata': {
            'channel_id': channel_id,
            'thread_ts': thread_ts,
            'user_id': user_id
        }
    }

    # Store plan in global registry
    _batch_plans[plan_id] = plan

    # Create context manager for this plan
    _context_managers[plan_id] = ContextManager(plan_id)

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

    # NEW: Get context quality from plan
    context_quality = plan.get('context_quality', 'medium')

    # NEW: Get Slack metadata from plan
    slack_metadata = plan.get('slack_metadata', {})
    channel_id = slack_metadata.get('channel_id')
    thread_ts = slack_metadata.get('thread_ts')
    user_id = slack_metadata.get('user_id')

    # Get learnings from previous posts
    learnings = context_mgr.get_compacted_learnings()
    target_score = context_mgr.get_target_score()

    # NEW: Adjust target score based on context quality
    if context_quality == "sparse":
        target_score = min(20, target_score)  # Lower expectations for thought leadership
        content_type_hint = "Thought Leadership (idea-driven, 800-1000 chars, opinion-based)"
    else:
        content_type_hint = "Proof Post (specific examples, 1200-1500 chars, data-driven)"

    print(f"\n📝 Executing post {post_index + 1}/{len(plan['posts'])}")
    print(f"   Platform: {post_spec['platform']}")
    print(f"   Context quality: {context_quality}")
    print(f"   Target score: {target_score}+")
    print(f"   Slack context: channel={channel_id}, thread={thread_ts}, user={user_id}")

    # Build enhanced context with quality indicator and learnings
    enhanced_context = f"""{post_spec.get('context', '')}

**Content Type:** {content_type_hint}

**Learnings from previous posts:**
{learnings}

**Target quality score:** {target_score}+/25"""

    try:
        # Execute post using SDK agent with enhanced context AND Slack metadata
        result = await _execute_single_post(
            platform=post_spec['platform'],
            topic=post_spec['topic'],
            context=enhanced_context,  # Enhanced with quality hints + learnings
            style=post_spec.get('style', ''),
            learnings=learnings,
            target_score=target_score,
            # Pass Slack metadata for Airtable/Supabase saves
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
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
        print(f"   ❌ Post creation error: {e}")
        import traceback
        traceback.print_exc()

        # Return structured error so batch can continue
        # Include enough info for user to see what went wrong
        error_msg = str(e)[:300]  # Truncate long errors

        return {
            'success': False,
            'score': 0,
            'platform': post_spec['platform'],
            'hook': f"Post {post_index + 1} failed - {error_msg[:50]}...",
            'airtable_url': None,
            'learnings_summary': f"❌ Error (post {post_index + 1}): {error_msg}",
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

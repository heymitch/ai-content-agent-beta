"""
Slack message formatters for content agent
Formats quality scores, content previews, and action buttons
"""

def format_quality_score(score: int) -> str:
    """Format quality score with emoji indicator"""
    if score >= 90:
        return f"🟢 {score}/100 (Excellent)"
    elif score >= 80:
        return f"🟡 {score}/100 (Good - Ready to ship)"
    elif score >= 70:
        return f"🟠 {score}/100 (Fair - Could improve)"
    else:
        return f"🔴 {score}/100 (Needs work)"


def format_content_result(result: dict, platform: str, airtable_url: str = None) -> str:
    """
    Format workflow result for Slack display

    Args:
        result: Workflow execution result dict
        platform: Platform name (linkedin, twitter, email)
        airtable_url: Optional Airtable URL for scheduled content

    Returns:
        Formatted Slack message with blocks
    """
    draft = result.get('draft', '')
    grading = result.get('grading', {})
    score = grading.get('score', 0)
    iterations = result.get('iterations', 0)

    # Build message sections
    sections = []

    # Header with quality score
    sections.append(f"✨ *{platform.upper()} Content Created*")
    sections.append(f"📊 Quality Score: {format_quality_score(score)}")
    sections.append(f"🔄 Revisions: {iterations}")
    sections.append("")

    # Content preview (with length limit for Slack)
    sections.append("*📝 Content:*")
    sections.append("```")

    # Truncate if too long (Slack has 3000 char limit per message)
    if len(draft) > 2500:
        sections.append(draft[:2500] + "...")
        sections.append("(Content truncated - full version in thread)")
    else:
        sections.append(draft)

    sections.append("```")
    sections.append("")

    # Issues/feedback if score < 80
    if score < 80:
        sections.append("*⚠️ Improvement Suggestions:*")
        feedback = grading.get('feedback', 'No specific feedback')
        sections.append(f"> {feedback}")
        sections.append("")

        code_issues = grading.get('code_issues_remaining', [])
        if code_issues:
            sections.append("*🔍 Issues Detected:*")
            for issue in code_issues[:3]:  # Show max 3 issues
                sections.append(f"• {issue.get('message', 'Unknown issue')}")
            if len(code_issues) > 3:
                sections.append(f"_...and {len(code_issues) - 3} more_")
            sections.append("")

    # Strengths if available
    strengths = grading.get('strengths', [])
    if strengths and score >= 80:
        sections.append("*✅ Strengths:*")
        for strength in strengths[:2]:  # Show max 2 strengths
            sections.append(f"• {strength}")
        sections.append("")

    # Airtable scheduling confirmation
    if airtable_url:
        sections.append("*📋 Scheduled to Calendar:*")
        sections.append(f"✅ Content added to Airtable (scheduled for tomorrow)")
        sections.append(f"<{airtable_url}|View in Airtable>")
        sections.append("")
        sections.append("*🎯 Next Steps:*")
        sections.append("React with:")
        sections.append("• ✏️ to request revisions")
        sections.append("• 🔄 to generate alternative version")
        sections.append("• 🔬 for detailed quality report")
    else:
        # Action prompts (if not auto-scheduled)
        sections.append("*🎯 Next Steps:*")
        sections.append("React with:")
        sections.append("• 📅 to schedule to calendar")
        sections.append("• ✏️ to request revisions")
        sections.append("• 🔄 to generate alternative version")
        sections.append("• ✅ to approve & archive")
        sections.append("• 🔬 for detailed quality report")

    return "\n".join(sections)


def format_batch_result(results: list, platform: str) -> str:
    """
    Format batch workflow results for Slack

    Args:
        results: List of workflow execution results
        platform: Platform name

    Returns:
        Formatted summary message
    """
    sections = []

    sections.append(f"✨ *Batch Creation Complete: {len(results)} {platform.upper()} posts*")
    sections.append("")

    # Summary stats
    total_score = sum(r.get('grading', {}).get('score', 0) for r in results)
    avg_score = total_score / len(results) if results else 0
    high_quality = sum(1 for r in results if r.get('grading', {}).get('score', 0) >= 80)

    sections.append(f"📊 Average Quality: {format_quality_score(int(avg_score))}")
    sections.append(f"✅ Ready to Ship: {high_quality}/{len(results)} posts")
    sections.append("")

    # Individual post summaries
    sections.append("*📝 Posts Created:*")
    for i, result in enumerate(results, 1):
        score = result.get('grading', {}).get('score', 0)
        draft_preview = result.get('draft', '')[:80]
        if len(result.get('draft', '')) > 80:
            draft_preview += "..."

        score_emoji = "🟢" if score >= 80 else "🟡" if score >= 70 else "🔴"
        sections.append(f"{i}. {score_emoji} {score}/100 - _{draft_preview}_")

    sections.append("")
    sections.append("*🎯 Next Steps:*")
    sections.append("Reply with post number to edit (e.g., 'edit post 2')")
    sections.append("React with 📅 to schedule all ready posts to calendar")

    return "\n".join(sections)


def format_detailed_report(result: dict) -> str:
    """
    Format detailed quality report for 🔬 reaction

    Args:
        result: Workflow execution result

    Returns:
        Detailed analysis message
    """
    grading = result.get('grading', {})
    sections = []

    sections.append("*🔬 Detailed Quality Report*")
    sections.append("")

    # Overall score
    score = grading.get('score', 0)
    sections.append(f"📊 Overall Score: {format_quality_score(score)}")
    sections.append("")

    # Strengths
    strengths = grading.get('strengths', [])
    if strengths:
        sections.append("*✅ Strengths:*")
        for strength in strengths:
            sections.append(f"• {strength}")
        sections.append("")

    # Issues
    issues = grading.get('issues', [])
    if issues:
        sections.append("*⚠️ Issues Identified:*")
        for issue in issues:
            sections.append(f"• {issue}")
        sections.append("")

    # Code validation
    code_issues = grading.get('code_issues_remaining', [])
    if code_issues:
        sections.append("*🔍 Pattern Detection:*")
        for issue in code_issues:
            severity = issue.get('severity', 'medium')
            severity_emoji = "🔴" if severity == 'high' else "🟡"
            sections.append(f"{severity_emoji} {issue.get('code', 'unknown')}: {issue.get('message', '')}")
        sections.append("")

    # Feedback
    feedback = grading.get('feedback', '')
    if feedback:
        sections.append("*💡 Improvement Suggestions:*")
        sections.append(f"> {feedback}")
        sections.append("")

    # Revision history
    revision_history = result.get('revision_history', [])
    if revision_history:
        sections.append("*🔄 Revision History:*")
        for rev in revision_history:
            iteration = rev.get('iteration', 0)
            rev_score = rev.get('score', 0)
            sections.append(f"Iteration {iteration}: {rev_score}/100")
        sections.append("")

    return "\n".join(sections)


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message for user-friendly Slack display

    Args:
        error: Exception that occurred
        context: Additional context about what failed

    Returns:
        Formatted error message
    """
    sections = []

    sections.append("❌ *Something went wrong*")
    sections.append("")

    if context:
        sections.append(f"*Context:* {context}")
        sections.append("")

    # User-friendly error mapping
    error_str = str(error)

    if "rate_limit" in error_str.lower():
        sections.append("⏱️ *Rate limit reached*")
        sections.append("Please wait a moment and try again.")
    elif "api_key" in error_str.lower() or "authentication" in error_str.lower():
        sections.append("🔐 *Authentication error*")
        sections.append("There's an issue with API credentials. Contact support.")
    elif "timeout" in error_str.lower():
        sections.append("⏰ *Request timeout*")
        sections.append("The operation took too long. Try a simpler request.")
    else:
        sections.append(f"*Error:* {error_str[:200]}")
        sections.append("")
        sections.append("Try rephrasing your request or contact support if this persists.")

    return "\n".join(sections)


def detect_platform_from_message(text: str) -> str:
    """
    Detect platform from message text

    Args:
        text: Message text from user

    Returns:
        Platform name (linkedin, twitter, email) or None
    """
    text_lower = text.lower()

    # Explicit platform mentions
    if 'linkedin' in text_lower or 'li post' in text_lower:
        return 'linkedin'
    elif 'twitter' in text_lower or 'tweet' in text_lower or 'thread' in text_lower:
        return 'twitter'
    elif 'email' in text_lower or 'newsletter' in text_lower:
        return 'email'

    # Content type hints
    if 'post' in text_lower and 'professional' in text_lower:
        return 'linkedin'
    elif 'thread' in text_lower or 'tweet' in text_lower:
        return 'twitter'

    # Default to LinkedIn for general content requests
    return 'linkedin'


def parse_content_request(text: str) -> dict:
    """
    Parse content request from Slack message

    Args:
        text: Message text

    Returns:
        Dict with platform, content_type, topic, additional_context
    """
    # Remove bot mention
    text = text.replace('<@', '').replace('>', '')

    # Detect platform
    platform = detect_platform_from_message(text)

    # Extract topic (everything after trigger words)
    trigger_words = ['write', 'create', 'draft', 'make', 'generate']
    topic = text

    for trigger in trigger_words:
        if trigger in text.lower():
            parts = text.lower().split(trigger, 1)
            if len(parts) > 1:
                topic = parts[1].strip()
                # Remove platform name from topic if present
                topic = topic.replace('linkedin post', '').replace('twitter thread', '').replace('email', '').strip()
                break

    return {
        'platform': platform,
        'content_type': 'post' if platform == 'linkedin' else 'thread' if platform == 'twitter' else 'email',
        'topic': topic,
        'additional_context': ''
    }

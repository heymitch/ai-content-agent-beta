"""
Content creation and workflow tools
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


def execute_content_workflow(
    platform: str,
    topic: str,
    additional_context: str = "",
    user_id: str = "slack_user",
    target_score: int = 80
) -> str:
    """
    Execute 3-agent content workflow: Writer → Validator → Reviser

    Args:
        platform: Target platform (linkedin, twitter, email)
        topic: Content topic/brief
        additional_context: Extra context (research, brand voice, etc.)
        user_id: User identifier
        target_score: Minimum quality score (default 80)

    Returns:
        JSON string with draft, score, and metadata
    """
    from workflows import WORKFLOW_REGISTRY
    import os
    from supabase import create_client

    # Initialize Supabase
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    # Get workflow class
    if platform.lower() not in WORKFLOW_REGISTRY:
        return json.dumps({
            'error': f'Unknown platform: {platform}',
            'available': list(WORKFLOW_REGISTRY.keys())
        })

    # Execute workflow
    try:
        workflow_class = WORKFLOW_REGISTRY[platform.lower()]
        workflow = workflow_class(supabase)

        # Combine topic and context
        full_brief = f"{topic}\n\nAdditional Context:\n{additional_context}" if additional_context else topic

        # Run async workflow (we'll need to handle this properly)
        import asyncio
        result = asyncio.run(workflow.execute(
            brief=full_brief,
            brand_context="",  # Will fetch from DB later
            user_id=user_id,
            target_score=target_score
        ))

        return json.dumps({
            'success': True,
            'platform': platform,
            'draft': result['draft'],
            'score': result['grading']['score'],
            'issues': result['grading'].get('issues', []),
            'iterations': result.get('iterations', 1),
            'metadata': result
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e),
            'platform': platform
        })


def execute_batch_workflows(
    workflows: List[Dict[str, Any]],
    delay_seconds: int = 2,
    auto_send_to_calendar: bool = True
) -> str:
    """
    Execute multiple workflows in sequence with rate limiting

    Args:
        workflows: List of workflow configs with platform, topic, additional_context, publish_date
        delay_seconds: Delay between workflows (default 2)
        auto_send_to_calendar: Auto-schedule to Airtable (default True)

    Returns:
        JSON string with results for each workflow
    """
    import time

    results = []

    for idx, workflow_config in enumerate(workflows):
        print(f"🎨 Executing workflow {idx + 1}/{len(workflows)}")

        # Extract config
        platform = workflow_config.get('platform', 'linkedin')
        topic = workflow_config.get('topic', '')
        additional_context = workflow_config.get('additional_context', '')
        publish_date = workflow_config.get('publish_date', '')

        # Execute workflow
        result = execute_content_workflow(
            platform=platform,
            topic=topic,
            additional_context=additional_context
        )

        result_data = json.loads(result)

        # Add to results
        results.append({
            'workflow': idx + 1,
            'platform': platform,
            'topic': topic,
            'result': result_data
        })

        # Send to calendar if requested
        if auto_send_to_calendar and result_data.get('success'):
            calendar_result = send_to_calendar(
                content=result_data['draft'],
                platform=platform,
                publish_date=publish_date,
                score=result_data['score']
            )
            results[-1]['calendar'] = calendar_result

        # Rate limit delay
        if idx < len(workflows) - 1:
            time.sleep(delay_seconds)

    return json.dumps({
        'total': len(workflows),
        'completed': len(results),
        'results': results
    }, indent=2)


def send_to_calendar(
    content: str,
    platform: str,
    publish_date: str = "",
    score: int = 0,
    metadata: Dict = None
) -> str:
    """
    Send content to Airtable calendar

    Args:
        content: Content text
        platform: Platform name
        publish_date: Date to publish (YYYY-MM-DD or "tomorrow", "next monday")
        score: Quality score
        metadata: Additional metadata

    Returns:
        JSON string with calendar record ID
    """
    try:
        from integrations.airtable_client import AirtableContentCalendar

        airtable = AirtableContentCalendar()

        # Parse publish date
        if not publish_date:
            # Default to tomorrow
            publish_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Create record
        record_id = airtable.create_content(
            content=content,
            platform=platform,
            scheduled_date=publish_date,
            quality_score=score,
            metadata=metadata or {}
        )

        return json.dumps({
            'success': True,
            'record_id': record_id,
            'scheduled_date': publish_date,
            'platform': platform
        })

    except Exception as e:
        return json.dumps({
            'error': str(e)
        })

"""
Batch Orchestration Tools for CMO Agent
Provides cancel and status checking for bulk content generation
"""

from typing import Dict, Any, Optional
from agents.batch_orchestrator import _batch_plans
from agents.content_queue import ContentQueueManager

# Global registry of active queue managers (plan_id -> ContentQueueManager)
_active_queues: Dict[str, ContentQueueManager] = {}


def cancel_batch(plan_id: str) -> str:
    """
    Cancel an active batch generation job

    Args:
        plan_id: The ID of the batch plan to cancel (e.g., "batch_20250125_143022")

    Returns:
        Status message about the cancellation

    Usage:
        User: "Stop the batch! Cancel it!"
        Agent: cancel_batch("batch_20250125_143022")
    """
    # Check if plan exists
    if plan_id not in _batch_plans:
        return f"❌ No batch found with ID '{plan_id}'. Use get_batch_status() to see active batches."

    # Check if queue manager exists
    if plan_id not in _active_queues:
        return f"⚠️ Batch '{plan_id}' exists but is not currently running. It may have already completed."

    queue_manager = _active_queues[plan_id]

    # Cancel the batch
    result = queue_manager.cancel_batch()

    if result['success']:
        return f"""🛑 **Batch Cancellation Initiated**

✅ In-progress posts will complete gracefully
🚫 Pending posts will be cancelled

Current stats:
- Completed: {result['stats']['total_completed']}
- Failed: {result['stats']['total_failed']}
- Remaining: Will be cancelled

You'll see a final summary when the cancellation completes."""
    else:
        return f"❌ {result['message']}"


async def get_batch_status(plan_id: Optional[str] = None) -> str:
    """
    Get status of a batch generation job

    Args:
        plan_id: The ID of the batch plan to check. If None, shows all active batches.

    Returns:
        Status information about the batch(es)

    Usage:
        User: "How's the batch going?"
        Agent: await get_batch_status("batch_20250125_143022")

        User: "What batches are running?"
        Agent: await get_batch_status()
    """
    # If no plan_id specified, show all active batches
    if plan_id is None:
        if not _active_queues:
            return "📭 No active batches running right now."

        status_lines = ["📊 **Active Batches:**\n"]
        for pid, queue_mgr in _active_queues.items():
            stats = await queue_mgr.get_all_status()
            status_lines.append(
                f"• `{pid}`: {stats['stats']['total_completed']}/{stats['stats']['total_queued']} completed "
                f"({stats['queue_size']} pending)"
            )

        return "\n".join(status_lines) + "\n\nUse `get_batch_status(plan_id)` for detailed status."

    # Check if plan exists
    if plan_id not in _batch_plans:
        return f"❌ No batch found with ID '{plan_id}'."

    # Check if queue manager exists
    if plan_id not in _active_queues:
        plan = _batch_plans[plan_id]
        return f"""⚠️ Batch '{plan_id}' is not currently running.

Plan details:
- Posts: {len(plan.get('posts', []))}
- Created: {plan.get('created_at', 'Unknown')}

This batch may have already completed. Check your Slack history for the completion summary."""

    # Get detailed status
    queue_manager = _active_queues[plan_id]
    stats = await queue_manager.get_all_status()

    # Build status message
    total = stats['stats']['total_queued']
    completed = stats['stats']['total_completed']
    failed = stats['stats']['total_failed']
    cancelled = stats['stats'].get('total_cancelled', 0)
    processing = stats['jobs']['processing']
    queued = stats['jobs']['queued']

    progress_bar = _create_progress_bar(completed, failed, cancelled, total)

    status_msg = f"""📊 **Batch Status: {plan_id}**

{progress_bar}

**Progress:**
- ✅ Completed: {completed}/{total}
- ❌ Failed: {failed}/{total}
{f'- 🚫 Cancelled: {cancelled}/{total}' if cancelled > 0 else ''}
- ⏳ Processing: {processing}
- 📥 Queued: {queued}

**Timing:**
- Average time per post: {stats['stats']['average_time']:.1f}s
- Estimated time remaining: {stats['estimated_time_remaining']:.0f}s

{f'⚠️ This batch has been cancelled.' if queue_manager.cancelled else ''}
"""

    return status_msg


def _create_progress_bar(completed: int, failed: int, cancelled: int, total: int, width: int = 20) -> str:
    """Create a visual progress bar"""
    if total == 0:
        return "[" + " " * width + "] 0%"

    done = completed + failed + cancelled
    progress = done / total

    filled = int(progress * width)
    bar = "=" * filled + " " * (width - filled)

    return f"[{bar}] {int(progress * 100)}%"


def register_queue_manager(plan_id: str, queue_manager: ContentQueueManager):
    """
    Register a queue manager for tracking
    Called by the orchestrator when starting a batch
    """
    _active_queues[plan_id] = queue_manager


def unregister_queue_manager(plan_id: str):
    """
    Unregister a queue manager after completion
    Called by the orchestrator when batch finishes
    """
    if plan_id in _active_queues:
        del _active_queues[plan_id]

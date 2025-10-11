"""
Content Queue Manager - Production-ready batch processing for content generation
Handles rate limiting, retries, and progress tracking
"""

import asyncio
from asyncio import Queue, Semaphore
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentStatus(Enum):
    """Status tracking for content generation"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ContentJob:
    """Single content generation job"""
    id: str
    platform: str  # linkedin, twitter, email
    topic: str
    context: str
    style: str
    status: ContentStatus = ContentStatus.QUEUED
    result: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    created_at: datetime = None
    completed_at: datetime = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()


class ContentQueueManager:
    """
    Manages batch content generation with rate limiting and retries
    Perfect for Replit $20/month Reserved VM
    """

    def __init__(
        self,
        max_concurrent: int = 3,  # Process 3 posts at a time
        max_retries: int = 2,
        retry_delay: int = 5,
        progress_callback: Optional[callable] = None
    ):
        """
        Initialize queue manager

        Args:
            max_concurrent: Maximum posts to process simultaneously (3 recommended)
            max_retries: Number of retry attempts for failed posts
            retry_delay: Seconds to wait before retry
            progress_callback: Function to call with progress updates
        """
        self.queue = Queue()
        self.semaphore = Semaphore(max_concurrent)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_callback = progress_callback

        # Track all jobs
        self.jobs: Dict[str, ContentJob] = {}
        self.processing = False

        # Statistics
        self.stats = {
            'total_queued': 0,
            'total_completed': 0,
            'total_failed': 0,
            'average_time': 0
        }

    async def add_job(self, job: ContentJob) -> str:
        """Add a single content job to the queue"""
        self.jobs[job.id] = job
        await self.queue.put(job)
        self.stats['total_queued'] += 1

        logger.info(f"📥 Queued job {job.id} ({job.platform})")

        # Start processing if not already running
        if not self.processing:
            asyncio.create_task(self._process_queue())

        return job.id

    async def bulk_create(
        self,
        posts: List[Dict[str, Any]],
        platform: str = "linkedin"
    ) -> List[ContentJob]:
        """
        Queue multiple posts for batch processing

        Args:
            posts: List of post dictionaries with topic, context, style
            platform: Target platform (linkedin, twitter, email)

        Returns:
            List of ContentJob objects with IDs for tracking
        """
        jobs = []

        for i, post_data in enumerate(posts):
            job = ContentJob(
                id=f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                platform=platform,
                topic=post_data.get('topic', ''),
                context=post_data.get('context', ''),
                style=post_data.get('style', 'thought_leadership')
            )

            await self.add_job(job)
            jobs.append(job)

        # Notify progress
        if self.progress_callback:
            await self.progress_callback({
                'status': 'queued',
                'total': len(posts),
                'platform': platform
            })

        return jobs

    async def _process_queue(self):
        """Main queue processing loop"""
        self.processing = True

        try:
            while not self.queue.empty():
                # Get next job (blocks if queue is empty)
                job = await self.queue.get()

                # Rate limiting through semaphore
                async with self.semaphore:
                    await self._process_job(job)

                # Mark task as done
                self.queue.task_done()

        finally:
            self.processing = False
            logger.info("✅ Queue processing complete")

    async def _process_job(self, job: ContentJob):
        """Process a single content job with retries"""

        job.status = ContentStatus.PROCESSING
        start_time = datetime.now()

        # Notify progress
        if self.progress_callback:
            await self.progress_callback({
                'status': 'processing',
                'job_id': job.id,
                'platform': job.platform,
                'completed': self.stats['total_completed'],
                'total': self.stats['total_queued']
            })

        try:
            # Import the appropriate workflow
            if job.platform == "linkedin":
                from agents.linkedin_sdk_agent import create_linkedin_post_workflow
                result = await create_linkedin_post_workflow(
                    topic=job.topic,
                    context=job.context,
                    style=job.style
                )
            elif job.platform == "twitter":
                from agents.agentic_twitter_orchestrator import create_twitter_thread_workflow
                result = await create_twitter_thread_workflow(
                    topic=job.topic,
                    context=job.context,
                    style=job.style
                )
            elif job.platform == "email":
                from agents.agentic_email_orchestrator import create_email_workflow
                result = await create_email_workflow(
                    topic=job.topic,
                    context=job.context,
                    style=job.style
                )
            else:
                raise ValueError(f"Unknown platform: {job.platform}")

            # Success!
            job.status = ContentStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now()

            # Update stats
            self.stats['total_completed'] += 1
            elapsed = (job.completed_at - start_time).total_seconds()
            self._update_average_time(elapsed)

            logger.info(f"✅ Completed job {job.id} in {elapsed:.1f}s")

        except Exception as e:
            await self._handle_job_failure(job, e)

    async def _handle_job_failure(self, job: ContentJob, error: Exception):
        """Handle failed job with retry logic"""

        job.attempts += 1
        job.error = str(error)

        if job.attempts < self.max_retries:
            # Retry after delay
            job.status = ContentStatus.RETRYING
            logger.warning(f"⚠️ Job {job.id} failed, retrying ({job.attempts}/{self.max_retries})")

            await asyncio.sleep(self.retry_delay)
            await self.queue.put(job)  # Re-queue for retry

        else:
            # Max retries exceeded
            job.status = ContentStatus.FAILED
            self.stats['total_failed'] += 1
            logger.error(f"❌ Job {job.id} failed after {job.attempts} attempts: {error}")

            # Notify failure
            if self.progress_callback:
                await self.progress_callback({
                    'status': 'failed',
                    'job_id': job.id,
                    'error': str(error)
                })

    def _update_average_time(self, elapsed: float):
        """Update rolling average processing time"""
        completed = self.stats['total_completed']
        current_avg = self.stats['average_time']

        # Calculate new average
        self.stats['average_time'] = (
            (current_avg * (completed - 1) + elapsed) / completed
        )

    async def get_status(self, job_id: str) -> Optional[ContentJob]:
        """Get status of a specific job"""
        return self.jobs.get(job_id)

    async def get_all_status(self) -> Dict[str, Any]:
        """Get overall queue status and statistics"""

        status_counts = {
            'queued': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'retrying': 0
        }

        for job in self.jobs.values():
            status_counts[job.status.value] += 1

        return {
            'jobs': status_counts,
            'stats': self.stats,
            'queue_size': self.queue.qsize(),
            'is_processing': self.processing,
            'estimated_time_remaining': self._estimate_time_remaining()
        }

    def _estimate_time_remaining(self) -> float:
        """Estimate seconds remaining based on average time"""
        if self.stats['average_time'] == 0:
            return 0

        remaining = self.queue.qsize()
        # Account for concurrent processing
        batches = (remaining + 2) // 3  # 3 concurrent
        return batches * self.stats['average_time']

    async def wait_for_completion(self):
        """Wait for all queued jobs to complete"""
        await self.queue.join()
        logger.info(f"📊 Final stats: {self.stats}")


# ================== SLACK INTEGRATION ==================

async def handle_bulk_content_request(
    slack_client,
    channel: str,
    thread_ts: str,
    posts_data: List[Dict],
    platform: str = "linkedin"
):
    """
    Handle bulk content generation request from Slack

    Example usage from Slack command:
    "Create 5 LinkedIn posts about AI ethics, productivity, remote work, cybersecurity, and cloud computing"
    """

    # Create queue manager with Slack progress callback
    async def slack_progress(update):
        """Send progress updates to Slack"""
        if update['status'] == 'processing':
            message = f"⏳ Processing {update['completed']}/{update['total']} {update['platform']} posts..."
        elif update['status'] == 'failed':
            message = f"⚠️ Job {update['job_id']} failed: {update['error']}"
        elif update['status'] == 'queued':
            message = f"📥 Queued {update['total']} {update['platform']} posts for generation"
        else:
            message = f"Status: {update}"

        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=message
        )

    queue_manager = ContentQueueManager(
        max_concurrent=3,
        progress_callback=slack_progress
    )

    # Queue all posts
    jobs = await queue_manager.bulk_create(posts_data, platform)

    # Initial response
    slack_client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=f"🚀 Started generating {len(jobs)} {platform} posts\n"
             f"Processing 3 at a time for optimal quality\n"
             f"Estimated time: {len(jobs) * 45 // 3} seconds"
    )

    # Wait for completion
    await queue_manager.wait_for_completion()

    # Send final summary
    stats = await queue_manager.get_all_status()

    summary = f"""✅ **Bulk Generation Complete**

    📊 Results:
    - Completed: {stats['stats']['total_completed']}
    - Failed: {stats['stats']['total_failed']}
    - Average time: {stats['stats']['average_time']:.1f}s per post

    Check Airtable for all generated content!
    """

    slack_client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=summary
    )

    return jobs


if __name__ == "__main__":
    # Test the queue system
    async def test():

        # Sample posts
        test_posts = [
            {'topic': 'AI Ethics', 'context': 'Focus on bias in ML', 'style': 'thought_leadership'},
            {'topic': 'Remote Work', 'context': 'Post-pandemic insights', 'style': 'practical'},
            {'topic': 'Cybersecurity', 'context': 'SMB best practices', 'style': 'educational'},
        ]

        # Create queue manager
        manager = ContentQueueManager(max_concurrent=2)

        # Queue posts
        jobs = await manager.bulk_create(test_posts, platform='linkedin')

        print(f"Queued {len(jobs)} jobs")

        # Wait for completion
        await manager.wait_for_completion()

        # Check results
        for job in jobs:
            status = await manager.get_status(job.id)
            print(f"Job {job.id}: {status.status.value}")

    asyncio.run(test())
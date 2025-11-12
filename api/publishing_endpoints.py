"""
Publishing State Tracking Endpoints

API endpoints for tracking publishing state transitions.
Called by n8n after successfully publishing to Ayrshare.

Endpoints:
- POST /api/publishing/mark-published - Update post status to published
- POST /api/publishing/mark-scheduled - Update post status to scheduled
- GET /api/publishing/status/{post_id} - Get publishing status
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


async def mark_post_published(
    airtable_record_id: Optional[str] = None,
    post_id: Optional[str] = None,
    ayrshare_post_id: Optional[str] = None,
    published_url: Optional[str] = None,
    published_at: Optional[str] = None,
    platform_ids: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Mark a post as published and store Ayrshare tracking info.

    Called by n8n after successful publishing to Ayrshare.

    Args:
        airtable_record_id: Airtable record ID (primary lookup)
        post_id: UUID of generated_posts record (fallback lookup)
        ayrshare_post_id: Ayrshare post ID for tracking
        published_url: URL to published post
        published_at: ISO timestamp of publishing (defaults to now)
        platform_ids: Dict of platform-specific IDs (e.g., {"linkedin": "123", "twitter": "456"})

    Returns:
        Success confirmation with updated post data
    """
    logger.info(f"Marking post as published: airtable={airtable_record_id}, ayrshare={ayrshare_post_id}")

    try:
        supabase = get_supabase_client()

        # Find post by airtable_record_id or post_id
        if airtable_record_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('airtable_record_id', airtable_record_id)\
                .execute()
        elif post_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('id', post_id)\
                .execute()
        else:
            return {
                'success': False,
                'error': 'Must provide either airtable_record_id or post_id'
            }

        if not result.data:
            return {
                'success': False,
                'error': f'Post not found (airtable_record_id={airtable_record_id}, post_id={post_id})'
            }

        post = result.data[0]
        post_id = post['id']

        # Prepare update data
        update_data = {
            'status': 'published',
            'published_at': published_at or datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        if ayrshare_post_id:
            update_data['ayrshare_post_id'] = ayrshare_post_id

        if published_url:
            update_data['published_url'] = published_url

        if platform_ids:
            update_data['ayrshare_platform_ids'] = platform_ids

        # Update post
        result = supabase.table('generated_posts')\
            .update(update_data)\
            .eq('id', post_id)\
            .execute()

        logger.info(f"Post {post_id} marked as published with Ayrshare ID: {ayrshare_post_id}")

        return {
            'success': True,
            'post_id': post_id,
            'airtable_record_id': post.get('airtable_record_id'),
            'ayrshare_post_id': ayrshare_post_id,
            'published_url': published_url,
            'published_at': update_data['published_at'],
            'message': 'Post successfully marked as published'
        }

    except Exception as e:
        logger.error(f"Error marking post as published: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def mark_post_scheduled(
    airtable_record_id: Optional[str] = None,
    post_id: Optional[str] = None,
    scheduled_for: Optional[str] = None,
    ayrshare_post_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark a post as scheduled.

    Called by n8n after scheduling post in Ayrshare.

    Args:
        airtable_record_id: Airtable record ID (primary lookup)
        post_id: UUID of generated_posts record (fallback lookup)
        scheduled_for: ISO timestamp of scheduled publish time
        ayrshare_post_id: Ayrshare scheduled post ID

    Returns:
        Success confirmation
    """
    logger.info(f"Marking post as scheduled: airtable={airtable_record_id}")

    try:
        supabase = get_supabase_client()

        # Find post
        if airtable_record_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('airtable_record_id', airtable_record_id)\
                .execute()
        elif post_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('id', post_id)\
                .execute()
        else:
            return {
                'success': False,
                'error': 'Must provide either airtable_record_id or post_id'
            }

        if not result.data:
            return {
                'success': False,
                'error': 'Post not found'
            }

        post = result.data[0]
        post_id = post['id']

        # Update data
        update_data = {
            'status': 'scheduled',
            'scheduled_for': scheduled_for,
            'updated_at': datetime.utcnow().isoformat()
        }

        if ayrshare_post_id:
            update_data['ayrshare_post_id'] = ayrshare_post_id

        # Update post
        result = supabase.table('generated_posts')\
            .update(update_data)\
            .eq('id', post_id)\
            .execute()

        logger.info(f"Post {post_id} marked as scheduled for {scheduled_for}")

        return {
            'success': True,
            'post_id': post_id,
            'scheduled_for': scheduled_for,
            'message': 'Post successfully marked as scheduled'
        }

    except Exception as e:
        logger.error(f"Error marking post as scheduled: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def get_publishing_status(
    airtable_record_id: Optional[str] = None,
    post_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get publishing status for a post.

    Args:
        airtable_record_id: Airtable record ID
        post_id: UUID of generated_posts record

    Returns:
        Post status and publishing details
    """
    try:
        supabase = get_supabase_client()

        # Find post
        if airtable_record_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('airtable_record_id', airtable_record_id)\
                .execute()
        elif post_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('id', post_id)\
                .execute()
        else:
            return {
                'success': False,
                'error': 'Must provide either airtable_record_id or post_id'
            }

        if not result.data:
            return {
                'success': False,
                'error': 'Post not found'
            }

        post = result.data[0]

        return {
            'success': True,
            'post_id': post['id'],
            'status': post.get('status'),
            'airtable_record_id': post.get('airtable_record_id'),
            'ayrshare_post_id': post.get('ayrshare_post_id'),
            'published_at': post.get('published_at'),
            'published_url': post.get('published_url'),
            'scheduled_for': post.get('scheduled_for'),
            'impressions': post.get('impressions'),
            'engagement_rate': post.get('engagement_rate'),
            'last_analytics_sync': post.get('last_analytics_sync')
        }

    except Exception as e:
        logger.error(f"Error getting publishing status: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def mark_publish_failed(
    airtable_record_id: Optional[str] = None,
    post_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark a post publish as failed.

    Called by n8n if publishing to Ayrshare fails.

    Args:
        airtable_record_id: Airtable record ID
        post_id: UUID of generated_posts record
        error_message: Error message from Ayrshare

    Returns:
        Success confirmation
    """
    logger.warning(f"Marking post publish as failed: {error_message}")

    try:
        supabase = get_supabase_client()

        # Find post
        if airtable_record_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('airtable_record_id', airtable_record_id)\
                .execute()
        elif post_id:
            result = supabase.table('generated_posts')\
                .select('*')\
                .eq('id', post_id)\
                .execute()
        else:
            return {
                'success': False,
                'error': 'Must provide either airtable_record_id or post_id'
            }

        if not result.data:
            return {
                'success': False,
                'error': 'Post not found'
            }

        post = result.data[0]
        post_id = post['id']

        # Update status
        update_data = {
            'status': 'failed',
            'platform_metadata': {
                'error': error_message,
                'failed_at': datetime.utcnow().isoformat()
            },
            'updated_at': datetime.utcnow().isoformat()
        }

        result = supabase.table('generated_posts')\
            .update(update_data)\
            .eq('id', post_id)\
            .execute()

        logger.info(f"Post {post_id} marked as failed")

        return {
            'success': True,
            'post_id': post_id,
            'message': 'Post marked as failed'
        }

    except Exception as e:
        logger.error(f"Error marking post as failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

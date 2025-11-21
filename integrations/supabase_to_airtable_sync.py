"""
Supabase to Airtable Analytics Sync

Syncs engagement metrics from Supabase generated_posts table back to Airtable
content calendar. This completes the analytics pipeline:

Ayrshare → Supabase → Airtable
           (existing)  (this module)

Use cases:
- Daily scheduled sync (via n8n at 6am)
- On-demand sync after manual analytics fetch
- Backfill historical data

Flow:
1. Query Supabase for published posts with analytics
2. For each post with airtable_record_id:
   - Extract metrics (impressions, engagements, etc.)
   - Update corresponding Airtable record
   - Set Last Synced timestamp
3. Return sync summary (count, errors)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def get_airtable_client():
    """Get Airtable client."""
    from integrations.airtable_client import AirtableClient
    return AirtableClient()


async def sync_analytics_to_airtable(
    post_id: str,
    supabase: Optional[Client] = None,
    airtable_client=None
) -> Dict[str, Any]:
    """
    Sync analytics for a single post from Supabase to Airtable.

    Args:
        post_id: UUID of generated_posts record
        supabase: Supabase client (optional, will create if not provided)
        airtable_client: Airtable client (optional)

    Returns:
        {
            "success": bool,
            "post_id": str,
            "airtable_record_id": str,
            "metrics_synced": {...},
            "error": str (if failed)
        }
    """
    if not supabase:
        supabase = get_supabase_client()

    if not airtable_client:
        airtable_client = get_airtable_client()

    try:
        # Query Supabase for post analytics
        response = supabase.table('generated_posts') \
            .select('*') \
            .eq('id', post_id) \
            .single() \
            .execute()

        if not response.data:
            return {
                "success": False,
                "post_id": post_id,
                "error": "Post not found in Supabase"
            }

        post = response.data
        airtable_record_id = post.get('airtable_record_id')

        if not airtable_record_id:
            return {
                "success": False,
                "post_id": post_id,
                "error": "No airtable_record_id linked to this post"
            }

        # Extract analytics metrics
        metrics = {
            "impressions": post.get('impressions', 0) or 0,
            "engagements": post.get('engagements', 0) or 0,
            "clicks": post.get('clicks', 0) or 0,
            "likes": post.get('likes', 0) or 0,
            "comments": post.get('comments', 0) or 0,
            "shares": post.get('shares', 0) or 0,
            "engagement_rate": post.get('engagement_rate', 0) or 0,
            "last_analytics_sync": post.get('last_analytics_sync')
        }

        # Update Airtable record
        airtable_client.update_analytics(airtable_record_id, metrics)

        logger.info(f"✅ Synced analytics to Airtable for post {post_id}")

        return {
            "success": True,
            "post_id": post_id,
            "airtable_record_id": airtable_record_id,
            "metrics_synced": metrics
        }

    except Exception as e:
        logger.error(f"❌ Error syncing analytics for post {post_id}: {e}")
        return {
            "success": False,
            "post_id": post_id,
            "error": str(e)
        }


async def bulk_sync_analytics_to_airtable(
    days_back: int = 7,
    force_resync: bool = False,
    supabase: Optional[Client] = None,
    airtable_client=None
) -> Dict[str, Any]:
    """
    Bulk sync analytics for multiple posts from Supabase to Airtable.

    Args:
        days_back: Number of days to look back for posts to sync
        force_resync: If True, resync even if recently synced
        supabase: Supabase client (optional)
        airtable_client: Airtable client (optional)

    Returns:
        {
            "success": bool,
            "synced": int,
            "errors": int,
            "total_posts": int,
            "total_impressions": int,
            "total_engagements": int,
            "sync_details": [...]
        }
    """
    if not supabase:
        supabase = get_supabase_client()

    if not airtable_client:
        airtable_client = get_airtable_client()

    try:
        # Query Supabase for published posts with analytics
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = supabase.table('generated_posts') \
            .select('id, airtable_record_id, impressions, engagements, clicks, likes, comments, shares, engagement_rate, last_analytics_sync, published_at') \
            .eq('status', 'published') \
            .not_.is_('airtable_record_id', 'null') \
            .gte('published_at', cutoff_date.isoformat())

        if not force_resync:
            # Only sync if not synced in last hour
            recent_sync_cutoff = datetime.utcnow() - timedelta(hours=1)
            query = query.or_(
                f'last_analytics_sync.is.null,last_analytics_sync.lt.{recent_sync_cutoff.isoformat()}'
            )

        response = query.execute()

        posts = response.data or []

        if not posts:
            logger.info("No posts found to sync")
            return {
                "success": True,
                "synced": 0,
                "errors": 0,
                "total_posts": 0,
                "message": "No posts found to sync"
            }

        logger.info(f"📊 Starting bulk sync for {len(posts)} posts")

        synced = 0
        errors = 0
        total_impressions = 0
        total_engagements = 0
        sync_details = []

        for post in posts:
            result = await sync_analytics_to_airtable(
                post_id=post['id'],
                supabase=supabase,
                airtable_client=airtable_client
            )

            if result['success']:
                synced += 1
                metrics = result.get('metrics_synced', {})
                total_impressions += metrics.get('impressions', 0)
                total_engagements += metrics.get('engagements', 0)
            else:
                errors += 1

            sync_details.append(result)

        logger.info(f"✅ Bulk sync complete: {synced} synced, {errors} errors")

        return {
            "success": True,
            "synced": synced,
            "errors": errors,
            "total_posts": len(posts),
            "total_impressions": total_impressions,
            "total_engagements": total_engagements,
            "sync_details": sync_details
        }

    except Exception as e:
        logger.error(f"❌ Error in bulk sync: {e}")
        return {
            "success": False,
            "synced": 0,
            "errors": 0,
            "total_posts": 0,
            "error": str(e)
        }


def get_sync_status(supabase: Optional[Client] = None) -> Dict[str, Any]:
    """
    Get status of analytics sync (last run time, health check).

    Returns:
        {
            "last_sync": timestamp,
            "posts_with_analytics": int,
            "posts_pending_sync": int,
            "status": "healthy" | "warning" | "error"
        }
    """
    if not supabase:
        supabase = get_supabase_client()

    try:
        # Get last sync timestamp
        response = supabase.table('generated_posts') \
            .select('last_analytics_sync') \
            .eq('status', 'published') \
            .not_.is_('last_analytics_sync', 'null') \
            .order('last_analytics_sync', desc=True) \
            .limit(1) \
            .execute()

        last_sync = None
        if response.data and len(response.data) > 0:
            last_sync = response.data[0].get('last_analytics_sync')

        # Count posts with analytics
        with_analytics = supabase.table('generated_posts') \
            .select('id', count='exact') \
            .eq('status', 'published') \
            .not_.is_('airtable_record_id', 'null') \
            .not_.is_('last_analytics_sync', 'null') \
            .execute()

        # Count posts pending sync (published but no analytics)
        pending = supabase.table('generated_posts') \
            .select('id', count='exact') \
            .eq('status', 'published') \
            .not_.is_('airtable_record_id', 'null') \
            .is_('last_analytics_sync', 'null') \
            .execute()

        posts_with_analytics = with_analytics.count or 0
        posts_pending_sync = pending.count or 0

        # Determine health status
        status = "healthy"
        if not last_sync:
            status = "warning"  # Never synced
        elif posts_pending_sync > 10:
            status = "warning"  # Many posts pending

        return {
            "last_sync": last_sync,
            "posts_with_analytics": posts_with_analytics,
            "posts_pending_sync": posts_pending_sync,
            "status": status
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {
            "last_sync": None,
            "posts_with_analytics": 0,
            "posts_pending_sync": 0,
            "status": "error",
            "error": str(e)
        }

"""
Ayrshare to Supabase Metrics Sync

Syncs engagement metrics from Ayrshare back to generated_posts in Supabase.
Critical for analytics - provides real performance data.

Use cases:
- Scheduled sync (daily at 6am via n8n)
- Before analytics analysis (get latest metrics)
- On-demand via API endpoint

Flow:
1. Query generated_posts for published posts with ayrshare_post_id
2. Fetch metrics from Ayrshare API for each post
3. UPDATE generated_posts with: impressions, likes, shares, engagement_rate, etc.
4. Set last_analytics_sync timestamp
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


async def sync_single_post_metrics(
    post_id: str,
    ayrshare_post_id: str,
    supabase: Client,
    ayrshare_client
) -> Dict[str, Any]:
    """
    Sync metrics for a single post from Ayrshare.

    Args:
        post_id: UUID of generated_posts record
        ayrshare_post_id: Ayrshare post ID
        supabase: Supabase client
        ayrshare_client: Ayrshare client instance

    Returns:
        Result dictionary with status and metrics
    """
    try:
        # Fetch metrics from Ayrshare
        metrics = ayrshare_client.get_post_analytics(ayrshare_post_id)

        if not metrics or metrics.get('error'):
            return {
                'success': False,
                'error': metrics.get('error', 'Unknown error'),
                'post_id': post_id
            }

        # Calculate engagement rate if not provided
        impressions = metrics.get('impressions', 0)
        engagements = metrics.get('engagements', 0)

        if impressions > 0:
            engagement_rate = (engagements / impressions) * 100
        else:
            engagement_rate = 0.0

        # Prepare update data
        update_data = {
            'impressions': metrics.get('impressions', 0),
            'engagements': metrics.get('engagements', 0),
            'clicks': metrics.get('clicks', 0),
            'likes': metrics.get('likes', 0),
            'comments': metrics.get('comments', 0),
            'shares': metrics.get('shares', 0),
            'saves': metrics.get('saves', 0),
            'engagement_rate': round(engagement_rate, 2),
            'last_analytics_sync': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Optional fields if available
        if 'click_through_rate' in metrics:
            update_data['click_through_rate'] = metrics['click_through_rate']
        if 'conversions' in metrics:
            update_data['conversions'] = metrics['conversions']
        if 'revenue_attributed' in metrics:
            update_data['revenue_attributed'] = metrics['revenue_attributed']

        # Update Supabase
        result = supabase.table('generated_posts')\
            .update(update_data)\
            .eq('id', post_id)\
            .execute()

        logger.info(
            f"Synced metrics for post {post_id}: "
            f"{impressions} impressions, {engagements} engagements, {engagement_rate:.1f}% rate"
        )

        return {
            'success': True,
            'post_id': post_id,
            'ayrshare_post_id': ayrshare_post_id,
            'metrics': update_data
        }

    except Exception as e:
        logger.error(f"Error syncing metrics for post {post_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'post_id': post_id
        }


async def sync_ayrshare_metrics(
    days_back: int = 7,
    limit: Optional[int] = None,
    force_resync: bool = False
) -> Dict[str, Any]:
    """
    Sync engagement metrics from Ayrshare to generated_posts.

    Args:
        days_back: Only sync posts published in last N days
        limit: Max number of posts to sync (None = all)
        force_resync: Resync even if recently synced

    Returns:
        Summary of sync operation
    """
    from integrations.ayrshare_client import get_ayrshare_client

    logger.info(f"Starting Ayrshare → Supabase metrics sync (last {days_back} days)")

    try:
        supabase = get_supabase_client()
        ayrshare_client = get_ayrshare_client()

        # Query published posts with ayrshare_post_id
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        query = supabase.table('generated_posts')\
            .select('id, ayrshare_post_id, platform, published_at, last_analytics_sync')\
            .eq('status', 'published')\
            .not_.is_('ayrshare_post_id', 'null')\
            .gte('published_at', cutoff_date)\
            .order('published_at', desc=True)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        posts = result.data

        if not posts:
            return {
                'success': True,
                'total': 0,
                'synced': 0,
                'skipped': 0,
                'errors': 0,
                'message': f'No published posts with Ayrshare IDs in last {days_back} days'
            }

        logger.info(f"Found {len(posts)} published posts to sync")

        # Filter out recently synced posts (unless force_resync)
        if not force_resync:
            posts_to_sync = []
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

            for post in posts:
                last_sync = post.get('last_analytics_sync')
                if not last_sync or last_sync < one_hour_ago:
                    posts_to_sync.append(post)

            if len(posts_to_sync) < len(posts):
                logger.info(
                    f"Skipping {len(posts) - len(posts_to_sync)} recently synced posts "
                    f"(synced within last hour)"
                )
            posts = posts_to_sync

        if not posts:
            return {
                'success': True,
                'total': 0,
                'synced': 0,
                'skipped': 0,
                'errors': 0,
                'message': 'All posts recently synced'
            }

        # Sync each post
        results = []
        for post in posts:
            result = await sync_single_post_metrics(
                post['id'],
                post['ayrshare_post_id'],
                supabase,
                ayrshare_client
            )
            results.append(result)

        # Summarize results
        synced = sum(1 for r in results if r.get('success'))
        errors = sum(1 for r in results if not r.get('success'))

        # Calculate total metrics across all synced posts
        total_impressions = sum(
            r.get('metrics', {}).get('impressions', 0)
            for r in results if r.get('success')
        )
        total_engagements = sum(
            r.get('metrics', {}).get('engagements', 0)
            for r in results if r.get('success')
        )

        summary = {
            'success': True,
            'total': len(posts),
            'synced': synced,
            'skipped': 0,
            'errors': errors,
            'total_impressions': total_impressions,
            'total_engagements': total_engagements,
            'results': results
        }

        logger.info(
            f"Metrics sync complete: {synced} synced, {errors} errors, "
            f"{total_impressions:,} total impressions"
        )

        return summary

    except Exception as e:
        logger.error(f"Metrics sync failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': 0
        }


async def sync_bulk_metrics(post_ids: List[str]) -> Dict[str, Any]:
    """
    Sync metrics for specific posts using Ayrshare's bulk API.

    More efficient than syncing one by one.

    Args:
        post_ids: List of ayrshare_post_ids

    Returns:
        Summary of bulk sync operation
    """
    from integrations.ayrshare_client import get_ayrshare_client

    logger.info(f"Bulk syncing metrics for {len(post_ids)} posts")

    try:
        supabase = get_supabase_client()
        ayrshare_client = get_ayrshare_client()

        # Fetch bulk metrics from Ayrshare
        bulk_metrics = ayrshare_client.get_bulk_analytics(post_ids)

        if not bulk_metrics:
            return {
                'success': False,
                'error': 'Bulk metrics fetch failed',
                'total': len(post_ids),
                'synced': 0,
                'errors': len(post_ids)
            }

        # Update each post in Supabase
        results = []
        for ayrshare_post_id, metrics in bulk_metrics.items():
            try:
                # Find Supabase post by ayrshare_post_id
                post_result = supabase.table('generated_posts')\
                    .select('id')\
                    .eq('ayrshare_post_id', ayrshare_post_id)\
                    .execute()

                if not post_result.data:
                    results.append({
                        'success': False,
                        'error': 'Post not found in Supabase',
                        'ayrshare_post_id': ayrshare_post_id
                    })
                    continue

                post_id = post_result.data[0]['id']

                # Sync metrics
                result = await sync_single_post_metrics(
                    post_id,
                    ayrshare_post_id,
                    supabase,
                    ayrshare_client
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Error syncing {ayrshare_post_id}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'ayrshare_post_id': ayrshare_post_id
                })

        synced = sum(1 for r in results if r.get('success'))
        errors = sum(1 for r in results if not r.get('success'))

        return {
            'success': True,
            'total': len(post_ids),
            'synced': synced,
            'skipped': 0,
            'errors': errors,
            'results': results
        }

    except Exception as e:
        logger.error(f"Bulk metrics sync failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': len(post_ids),
            'synced': 0,
            'errors': len(post_ids)
        }


async def get_sync_status() -> Dict[str, Any]:
    """
    Get status of metrics sync - when last run, how many posts synced, etc.

    Returns:
        Status summary
    """
    try:
        supabase = get_supabase_client()

        # Get sync statistics
        result = supabase.table('generated_posts')\
            .select('last_analytics_sync, published_at, engagement_rate')\
            .eq('status', 'published')\
            .not_.is_('ayrshare_post_id', 'null')\
            .execute()

        posts = result.data

        if not posts:
            return {
                'success': True,
                'total_posts': 0,
                'synced_posts': 0,
                'unsynced_posts': 0,
                'last_sync': None
            }

        synced = [p for p in posts if p.get('last_analytics_sync')]
        unsynced = [p for p in posts if not p.get('last_analytics_sync')]

        # Find most recent sync
        last_sync = None
        if synced:
            last_sync = max(p['last_analytics_sync'] for p in synced)

        # Find posts needing sync (published >1 day ago but never synced)
        one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        needs_sync = [
            p for p in unsynced
            if p.get('published_at') and p['published_at'] < one_day_ago
        ]

        return {
            'success': True,
            'total_posts': len(posts),
            'synced_posts': len(synced),
            'unsynced_posts': len(unsynced),
            'needs_sync': len(needs_sync),
            'last_sync': last_sync,
            'avg_engagement_rate': round(
                sum(p.get('engagement_rate', 0) for p in synced) / len(synced), 2
            ) if synced else 0
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {
            'success': False,
            'error': str(e)
        }

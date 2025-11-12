"""
Airtable to Supabase Sync

Syncs edited content from Airtable back to generated_posts in Supabase.
Critical for analytics accuracy - ensures embeddings reflect published content.

Use cases:
- Run before analytics analysis (get latest edits)
- Scheduled sync (daily/hourly via n8n)
- On-demand via API endpoint

Flow:
1. Fetch all generated_posts with airtable_record_id
2. Get current content from Airtable
3. If content changed: re-generate embedding, update Supabase
4. Sync status changes (Draft → Scheduled → Published)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def get_openai_client() -> OpenAI:
    """Get OpenAI client for embeddings."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")
    return OpenAI(api_key=api_key)


def generate_embedding(text: str) -> List[float]:
    """
    Generate OpenAI embedding for text.

    Args:
        text: Content to embed

    Returns:
        1536-dimensional embedding vector
    """
    client = get_openai_client()

    # Use same model as original generation
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


async def sync_single_post(
    post_id: str,
    supabase: Client,
    airtable_client
) -> Dict[str, Any]:
    """
    Sync a single post from Airtable to Supabase.

    Args:
        post_id: UUID of generated_posts record
        supabase: Supabase client
        airtable_client: Airtable client instance

    Returns:
        Result dictionary with status and details
    """
    try:
        # Get current post from Supabase
        result = supabase.table('generated_posts').select('*').eq('id', post_id).execute()

        if not result.data:
            return {'success': False, 'error': 'Post not found in Supabase'}

        post = result.data[0]
        airtable_record_id = post.get('airtable_record_id')

        if not airtable_record_id:
            return {'success': False, 'error': 'No airtable_record_id', 'skipped': True}

        # Fetch from Airtable
        airtable_result = airtable_client.get_content_record(airtable_record_id)

        if not airtable_result.get('success'):
            return {
                'success': False,
                'error': f"Failed to fetch from Airtable: {airtable_result.get('error')}"
            }

        airtable_fields = airtable_result['record']['fields']
        airtable_content = airtable_fields.get('Body Content', '')
        airtable_status = airtable_fields.get('Status', 'Draft')

        # Check if content changed
        content_changed = airtable_content != post.get('body_content')
        status_changed = airtable_status != post.get('airtable_status')

        if not content_changed and not status_changed:
            return {'success': True, 'changed': False, 'skipped': True}

        update_data = {}

        # Update content and regenerate embedding if changed
        if content_changed:
            logger.info(f"Content changed for post {post_id}, regenerating embedding")
            new_embedding = generate_embedding(airtable_content)
            update_data['body_content'] = airtable_content
            update_data['embedding'] = new_embedding

        # Update status
        if status_changed:
            # Map Airtable status to Supabase status
            status_map = {
                'Draft': 'draft',
                'Scheduled': 'scheduled',
                'Published': 'published',
                'Archived': 'archived'
            }
            update_data['airtable_status'] = airtable_status
            # Only update status if not manually set to something else
            if post.get('status') in ['draft', 'scheduled']:
                update_data['status'] = status_map.get(airtable_status, 'draft')

        # Update hook if content changed (first 200 chars)
        if content_changed:
            update_data['post_hook'] = airtable_content[:200]

        update_data['updated_at'] = datetime.utcnow().isoformat()

        # Perform update
        supabase.table('generated_posts').update(update_data).eq('id', post_id).execute()

        return {
            'success': True,
            'changed': True,
            'content_changed': content_changed,
            'status_changed': status_changed,
            'post_id': post_id,
            'airtable_record_id': airtable_record_id
        }

    except Exception as e:
        logger.error(f"Error syncing post {post_id}: {e}")
        return {'success': False, 'error': str(e), 'post_id': post_id}


async def sync_airtable_to_generated_posts(
    limit: Optional[int] = None,
    only_recent: bool = True
) -> Dict[str, Any]:
    """
    Sync edited Airtable content back to generated_posts.

    Args:
        limit: Max number of posts to sync (None = all)
        only_recent: Only sync posts from last 30 days

    Returns:
        Summary of sync operation
    """
    from integrations.airtable_client import get_airtable_client

    logger.info("Starting Airtable → Supabase sync")

    try:
        supabase = get_supabase_client()
        airtable_client = get_airtable_client()

        # Query posts with airtable_record_id
        query = supabase.table('generated_posts')\
            .select('id, airtable_record_id, body_content, airtable_status, created_at')\
            .not_.is_('airtable_record_id', 'null')

        # Filter to recent posts if requested
        if only_recent:
            from datetime import timedelta
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            query = query.gte('created_at', thirty_days_ago)

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
                'message': 'No posts to sync'
            }

        logger.info(f"Found {len(posts)} posts to check")

        # Sync each post
        results = []
        for post in posts:
            result = await sync_single_post(post['id'], supabase, airtable_client)
            results.append(result)

        # Summarize results
        synced = sum(1 for r in results if r.get('success') and r.get('changed'))
        skipped = sum(1 for r in results if r.get('skipped'))
        errors = sum(1 for r in results if not r.get('success'))

        summary = {
            'success': True,
            'total': len(posts),
            'synced': synced,
            'skipped': skipped,
            'errors': errors,
            'results': results
        }

        logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {errors} errors")

        return summary

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': 0
        }


async def sync_specific_posts(post_ids: List[str]) -> Dict[str, Any]:
    """
    Sync specific posts by ID.

    Args:
        post_ids: List of generated_posts UUIDs

    Returns:
        Summary of sync operation
    """
    from integrations.airtable_client import get_airtable_client

    logger.info(f"Syncing {len(post_ids)} specific posts")

    try:
        supabase = get_supabase_client()
        airtable_client = get_airtable_client()

        results = []
        for post_id in post_ids:
            result = await sync_single_post(post_id, supabase, airtable_client)
            results.append(result)

        synced = sum(1 for r in results if r.get('success') and r.get('changed'))
        skipped = sum(1 for r in results if r.get('skipped'))
        errors = sum(1 for r in results if not r.get('success'))

        return {
            'success': True,
            'total': len(post_ids),
            'synced': synced,
            'skipped': skipped,
            'errors': errors,
            'results': results
        }

    except Exception as e:
        logger.error(f"Specific post sync failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

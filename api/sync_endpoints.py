"""
Sync API Endpoints

REST endpoints for triggering analytics sync between:
- Ayrshare → Supabase (existing in ayrshare_sync.py)
- Supabase → Airtable (new in supabase_to_airtable_sync.py)

Endpoints:
- POST /api/sync/analytics-to-airtable - Trigger Supabase → Airtable sync
- GET /api/sync/status - Check sync health and last run time
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from integrations.supabase_to_airtable_sync import (
    bulk_sync_analytics_to_airtable,
    get_sync_status
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/sync", tags=["sync"])


# Request/Response Models
class SyncAnalyticsRequest(BaseModel):
    """Request body for analytics sync"""
    days_back: int = Field(default=7, ge=1, le=365, description="Number of days to look back for posts to sync")
    force_resync: bool = Field(default=False, description="If true, resync even if recently synced")


class SyncAnalyticsResponse(BaseModel):
    """Response for analytics sync"""
    success: bool
    synced: int
    errors: int
    total_posts: int
    total_impressions: Optional[int] = None
    total_engagements: Optional[int] = None
    message: Optional[str] = None


class SyncStatusResponse(BaseModel):
    """Response for sync status check"""
    last_sync: Optional[str] = None
    posts_with_analytics: int
    posts_pending_sync: int
    status: str  # "healthy", "warning", "error"
    error: Optional[str] = None


# Endpoints

@router.post("/analytics-to-airtable", response_model=SyncAnalyticsResponse)
async def sync_analytics_to_airtable_endpoint(request: SyncAnalyticsRequest):
    """
    Trigger Supabase → Airtable analytics sync.

    This endpoint syncs engagement metrics from Supabase generated_posts table
    back to Airtable content calendar records.

    **Workflow:**
    1. Query Supabase for published posts with analytics
    2. For each post with airtable_record_id:
       - Extract metrics (impressions, engagements, etc.)
       - Update corresponding Airtable record
       - Set Last Synced timestamp
    3. Return sync summary

    **Use Cases:**
    - Daily scheduled sync (via n8n at 6am)
    - On-demand sync after manual analytics fetch
    - Backfill historical data

    **Example Request:**
    ```json
    {
        "days_back": 7,
        "force_resync": false
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "synced": 45,
        "errors": 2,
        "total_posts": 47,
        "total_impressions": 150000,
        "total_engagements": 12500
    }
    ```
    """
    try:
        logger.info(f"📊 Starting analytics sync: days_back={request.days_back}, force_resync={request.force_resync}")

        result = await bulk_sync_analytics_to_airtable(
            days_back=request.days_back,
            force_resync=request.force_resync
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Sync failed: {result.get('error', 'Unknown error')}"
            )

        logger.info(f"✅ Sync complete: {result.get('synced')} posts synced")

        return SyncAnalyticsResponse(
            success=result["success"],
            synced=result.get("synced", 0),
            errors=result.get("errors", 0),
            total_posts=result.get("total_posts", 0),
            total_impressions=result.get("total_impressions"),
            total_engagements=result.get("total_engagements"),
            message=result.get("message")
        )

    except Exception as e:
        logger.error(f"❌ Error in analytics sync endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing analytics: {str(e)}"
        )


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status_endpoint():
    """
    Check analytics sync health and status.

    Returns information about:
    - Last successful sync timestamp
    - Number of posts with analytics
    - Number of posts pending sync
    - Overall health status

    **Health Status Values:**
    - `healthy`: Sync working normally
    - `warning`: Never synced OR many posts pending (>10)
    - `error`: System error occurred

    **Example Response:**
    ```json
    {
        "last_sync": "2025-11-13T06:00:15Z",
        "posts_with_analytics": 145,
        "posts_pending_sync": 3,
        "status": "healthy"
    }
    ```
    """
    try:
        status = get_sync_status()

        return SyncStatusResponse(
            last_sync=status.get("last_sync"),
            posts_with_analytics=status.get("posts_with_analytics", 0),
            posts_pending_sync=status.get("posts_pending_sync", 0),
            status=status.get("status", "unknown"),
            error=status.get("error")
        )

    except Exception as e:
        logger.error(f"❌ Error getting sync status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sync status: {str(e)}"
        )

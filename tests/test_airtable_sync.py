"""
Tests for Airtable Analytics Sync

Tests the Supabase → Airtable analytics sync functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_sync_single_post_analytics():
    """Test syncing analytics for a single post."""
    from integrations.supabase_to_airtable_sync import sync_analytics_to_airtable

    # Mock Supabase response
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={
            "id": "test-post-id",
            "airtable_record_id": "recABC123",
            "impressions": 1500,
            "engagements": 120,
            "clicks": 45,
            "likes": 60,
            "comments": 10,
            "shares": 5,
            "engagement_rate": 8.0,
            "last_analytics_sync": "2025-11-13T06:00:00Z"
        }
    )

    # Mock Airtable client
    mock_airtable = Mock()
    mock_airtable.update_analytics.return_value = {
        "success": True,
        "record_id": "recABC123"
    }

    # Run sync
    result = await sync_analytics_to_airtable(
        post_id="test-post-id",
        supabase=mock_supabase,
        airtable_client=mock_airtable
    )

    # Assertions
    assert result["success"] is True
    assert result["post_id"] == "test-post-id"
    assert result["airtable_record_id"] == "recABC123"
    assert result["metrics_synced"]["impressions"] == 1500
    assert result["metrics_synced"]["engagements"] == 120

    # Verify Airtable update was called
    mock_airtable.update_analytics.assert_called_once()


@pytest.mark.asyncio
async def test_sync_post_not_found():
    """Test handling when post doesn't exist in Supabase."""
    from integrations.supabase_to_airtable_sync import sync_analytics_to_airtable

    # Mock Supabase response (no data)
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data=None
    )

    result = await sync_analytics_to_airtable(
        post_id="nonexistent-id",
        supabase=mock_supabase
    )

    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_sync_no_airtable_record_id():
    """Test handling when post has no airtable_record_id."""
    from integrations.supabase_to_airtable_sync import sync_analytics_to_airtable

    # Mock Supabase response (no airtable_record_id)
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={
            "id": "test-post-id",
            "airtable_record_id": None,
            "impressions": 1500
        }
    )

    result = await sync_analytics_to_airtable(
        post_id="test-post-id",
        supabase=mock_supabase
    )

    assert result["success"] is False
    assert "airtable_record_id" in result["error"].lower()


@pytest.mark.asyncio
async def test_bulk_sync_analytics():
    """Test bulk syncing analytics for multiple posts."""
    from integrations.supabase_to_airtable_sync import bulk_sync_analytics_to_airtable

    # Mock Supabase query
    mock_supabase = Mock()

    # Mock response with 3 posts
    mock_posts = [
        {
            "id": "post-1",
            "airtable_record_id": "rec1",
            "impressions": 1000,
            "engagements": 100,
            "clicks": 30,
            "likes": 50,
            "comments": 10,
            "shares": 10,
            "engagement_rate": 10.0,
            "last_analytics_sync": None,
            "published_at": "2025-11-10T10:00:00Z"
        },
        {
            "id": "post-2",
            "airtable_record_id": "rec2",
            "impressions": 2000,
            "engagements": 200,
            "clicks": 60,
            "likes": 100,
            "comments": 20,
            "shares": 20,
            "engagement_rate": 10.0,
            "last_analytics_sync": None,
            "published_at": "2025-11-11T10:00:00Z"
        },
        {
            "id": "post-3",
            "airtable_record_id": "rec3",
            "impressions": 1500,
            "engagements": 150,
            "clicks": 45,
            "likes": 75,
            "comments": 15,
            "shares": 15,
            "engagement_rate": 10.0,
            "last_analytics_sync": None,
            "published_at": "2025-11-12T10:00:00Z"
        }
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.gte.return_value.execute.return_value = Mock(
        data=mock_posts
    )

    # Mock Airtable client
    mock_airtable = Mock()
    mock_airtable.update_analytics.return_value = {
        "success": True
    }

    # Mock sync_analytics_to_airtable to return success
    with patch('integrations.supabase_to_airtable_sync.sync_analytics_to_airtable') as mock_sync:
        mock_sync.side_effect = [
            {"success": True, "post_id": "post-1", "airtable_record_id": "rec1", "metrics_synced": {"impressions": 1000, "engagements": 100}},
            {"success": True, "post_id": "post-2", "airtable_record_id": "rec2", "metrics_synced": {"impressions": 2000, "engagements": 200}},
            {"success": True, "post_id": "post-3", "airtable_record_id": "rec3", "metrics_synced": {"impressions": 1500, "engagements": 150}}
        ]

        result = await bulk_sync_analytics_to_airtable(
            days_back=7,
            supabase=mock_supabase,
            airtable_client=mock_airtable
        )

        # Assertions
        assert result["success"] is True
        assert result["synced"] == 3
        assert result["errors"] == 0
        assert result["total_posts"] == 3
        assert result["total_impressions"] == 4500
        assert result["total_engagements"] == 450


@pytest.mark.asyncio
async def test_bulk_sync_with_errors():
    """Test bulk sync handling when some posts fail."""
    from integrations.supabase_to_airtable_sync import bulk_sync_analytics_to_airtable

    mock_supabase = Mock()
    mock_posts = [
        {"id": "post-1", "airtable_record_id": "rec1", "impressions": 1000, "engagements": 100, "clicks": 30, "likes": 50, "comments": 10, "shares": 10, "engagement_rate": 10.0, "last_analytics_sync": None, "published_at": "2025-11-10T10:00:00Z"},
        {"id": "post-2", "airtable_record_id": "rec2", "impressions": 2000, "engagements": 200, "clicks": 60, "likes": 100, "comments": 20, "shares": 20, "engagement_rate": 10.0, "last_analytics_sync": None, "published_at": "2025-11-11T10:00:00Z"}
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.gte.return_value.execute.return_value = Mock(
        data=mock_posts
    )

    mock_airtable = Mock()

    # Mock: First post succeeds, second fails
    with patch('integrations.supabase_to_airtable_sync.sync_analytics_to_airtable') as mock_sync:
        mock_sync.side_effect = [
            {"success": True, "post_id": "post-1", "metrics_synced": {"impressions": 1000, "engagements": 100}},
            {"success": False, "post_id": "post-2", "error": "Airtable update failed"}
        ]

        result = await bulk_sync_analytics_to_airtable(
            days_back=7,
            supabase=mock_supabase,
            airtable_client=mock_airtable
        )

        assert result["success"] is True
        assert result["synced"] == 1
        assert result["errors"] == 1
        assert result["total_posts"] == 2


def test_get_sync_status():
    """Test getting sync status."""
    from integrations.supabase_to_airtable_sync import get_sync_status

    mock_supabase = Mock()

    # Mock last sync query
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
        data=[{"last_analytics_sync": "2025-11-13T06:00:00Z"}]
    )

    # Mock posts with analytics count
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.not_.is_.return_value.execute.return_value = Mock(
        count=145
    )

    # Mock posts pending sync count
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.is_.return_value.execute.return_value = Mock(
        count=3
    )

    status = get_sync_status(supabase=mock_supabase)

    assert status["status"] == "healthy"
    assert status["posts_with_analytics"] == 145
    assert status["posts_pending_sync"] == 3
    assert status["last_sync"] == "2025-11-13T06:00:00Z"


def test_airtable_update_analytics():
    """Test Airtable update_analytics method."""
    from integrations.airtable_client import AirtableContentCalendar

    # Mock pyairtable table
    with patch('integrations.airtable_client.Api') as mock_api:
        mock_table = Mock()
        mock_table.update.return_value = {
            "id": "recABC123",
            "fields": {
                "Impressions": 1500,
                "Engagements": 120,
                "Engagement Rate": 0.08
            }
        }
        mock_api.return_value.table.return_value = mock_table

        client = AirtableContentCalendar()
        result = client.update_analytics(
            record_id="recABC123",
            metrics={
                "impressions": 1500,
                "engagements": 120,
                "clicks": 45,
                "likes": 60,
                "comments": 10,
                "shares": 5,
                "engagement_rate": 8.0,
                "last_analytics_sync": "2025-11-13T06:00:00Z"
            }
        )

        assert result["success"] is True
        assert result["record_id"] == "recABC123"
        mock_table.update.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

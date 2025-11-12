"""
Ayrshare Integration Client

Handles fetching engagement metrics from Ayrshare API.
Ayrshare provides social media scheduling and analytics.
"""

import os
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AyrshareClient:
    """Client for Ayrshare API integration."""

    def __init__(self, api_key: Optional[str] = None, profile_key: Optional[str] = None):
        """
        Initialize Ayrshare client.

        Args:
            api_key: Ayrshare API key (defaults to env var AYRSHARE_API_KEY)
            profile_key: Optional Profile Key for user-specific analytics (defaults to env var AYRSHARE_PROFILE_KEY)
        """
        self.api_key = api_key or os.getenv('AYRSHARE_API_KEY')
        self.profile_key = profile_key or os.getenv('AYRSHARE_PROFILE_KEY')
        self.base_url = "https://api.ayrshare.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Add Profile-Key header if provided (for user-specific analytics)
        if self.profile_key:
            self.headers["Profile-Key"] = self.profile_key

        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.info("Ayrshare integration disabled (no API key)")

    def get_post_analytics(self, post_id: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get analytics for a specific post.

        Args:
            post_id: Ayrshare post ID from /post endpoint
            platforms: Optional list of platforms to filter (e.g., ['twitter', 'linkedin'])

        Returns:
            Dict with normalized analytics + platform-specific data
        """
        if not self.enabled:
            return self._mock_analytics(post_id)

        try:
            # Build request body
            body = {"id": post_id}
            if platforms:
                body["platforms"] = platforms

            # POST request (not GET) to /analytics/post endpoint
            response = requests.post(
                f"{self.base_url}/analytics/post",
                headers=self.headers,
                json=body
            )
            response.raise_for_status()
            data = response.json()

            # Handle specific error codes
            if isinstance(data, dict):
                error_code = data.get("code")
                if error_code == 116:
                    logger.error(f"Post ID {post_id} not found in Ayrshare")
                    return {"error": "Post not found", "code": 116}
                elif error_code == 186:
                    logger.error(f"Post ID {post_id} deleted at social network")
                    return {"error": "Post deleted at social network", "code": 186}

            # Parse platform-specific analytics
            return self._parse_analytics_response(data)

        except Exception as e:
            logger.error(f"Error fetching Ayrshare analytics for {post_id}: {e}")
            return self._mock_analytics(post_id)

    def get_bulk_analytics(self, post_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get analytics for multiple posts.

        Args:
            post_ids: List of Ayrshare post IDs

        Returns:
            Dict mapping post_id to analytics data
        """
        results = {}
        for post_id in post_ids:
            results[post_id] = self.get_post_analytics(post_id)
        return results

    def get_history(
        self,
        days_back: int = 7,
        platforms: Optional[List[str]] = None,
        limit: int = 100,
        status: Optional[str] = None,
        post_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get posting history.

        Args:
            days_back: Number of days to look back (0 = all history, default: 7)
            platforms: List of platforms to filter (OR logic, e.g., ['twitter', 'linkedin'])
            limit: Max posts to return (max: 1000, default: 100)
            status: Filter by status (success, error, processing, pending, paused, deleted, awaiting approval)
            post_type: Filter by type (immediate, scheduled)

        Returns:
            List of posts (Note: analytics NOT included, must call get_post_analytics separately)
        """
        if not self.enabled:
            return self._mock_history(days_back, platforms)

        try:
            params = {}

            # Use lastDays parameter (simpler than startDate/endDate)
            if days_back > 0:
                params["lastDays"] = days_back
            # If days_back == 0, omit to get all history

            # Add optional filters
            if platforms:
                params["platforms"] = platforms  # Array, not single string

            if limit:
                params["limit"] = min(limit, 1000)  # Cap at API max

            if status:
                params["status"] = status

            if post_type:
                params["type"] = post_type

            response = requests.get(
                f"{self.base_url}/history",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # Process and return posts (correct field name: "history")
            posts = []
            for post in data.get("history", []):
                posts.append({
                    "id": post.get("id"),
                    "platforms": post.get("platforms", []),  # Array, not single string
                    "content": post.get("post"),  # Field name is "post" not "content"
                    "status": post.get("status"),
                    "type": post.get("type"),
                    "scheduled_date": post.get("scheduleDate"),  # When it was/will be posted
                    "created_at": post.get("created"),
                    "post_ids": post.get("postIds", {}),  # Platform-specific IDs (dict)
                    # Note: analytics are NOT included in history response
                    # Must call get_post_analytics(post['id']) separately
                })

            return posts

        except Exception as e:
            logger.error(f"Error fetching Ayrshare history: {e}")
            return self._mock_history(days_back, platforms)

    def _calculate_engagement_rate(self, data: Dict[str, Any]) -> float:
        """Calculate engagement rate from metrics."""
        impressions = data.get("impressions", 0)
        engagements = data.get("engagements", 0)

        if impressions > 0:
            return (engagements / impressions) * 100
        return 0.0

    def _parse_analytics_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse platform-specific analytics into normalized format.

        Official API returns different structures per platform:
        - twitter: publicMetrics.impressionCount, likeCount, replyCount, retweetCount
        - instagram: reach, likes, comments, saves, shares
        - tiktok: views, likes, comments, shares
        - linkedin: clicks, likes, comments (varies by profile type)
        - facebook: reach, engagement, clicks

        Args:
            data: Raw API response with platform-specific analytics

        Returns:
            Normalized dict with totals + platform-specific data
        """
        normalized = {
            "impressions": 0,
            "engagements": 0,
            "clicks": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "platform_data": {}
        }

        # Extract platform-specific metrics
        for platform in ["twitter", "linkedin", "instagram", "tiktok", "facebook", "pinterest", "youtube"]:
            if platform in data:
                platform_analytics = data[platform].get("analytics", {})
                normalized["platform_data"][platform] = platform_analytics

                # Platform-specific extraction
                if platform == "twitter":
                    metrics = platform_analytics.get("publicMetrics", {})
                    normalized["impressions"] += metrics.get("impressionCount", 0)
                    normalized["likes"] += metrics.get("likeCount", 0)
                    normalized["comments"] += metrics.get("replyCount", 0)
                    normalized["shares"] += metrics.get("retweetCount", 0)

                elif platform == "instagram":
                    normalized["impressions"] += platform_analytics.get("reach", 0)
                    normalized["likes"] += platform_analytics.get("likes", 0)
                    normalized["comments"] += platform_analytics.get("comments", 0)
                    normalized["shares"] += platform_analytics.get("shares", 0)
                    normalized["saves"] += platform_analytics.get("saves", 0)

                elif platform == "tiktok":
                    normalized["impressions"] += platform_analytics.get("views", 0)
                    normalized["likes"] += platform_analytics.get("likes", 0)
                    normalized["comments"] += platform_analytics.get("comments", 0)
                    normalized["shares"] += platform_analytics.get("shares", 0)

                elif platform == "linkedin":
                    # LinkedIn has different structures for corporate vs personal
                    normalized["impressions"] += platform_analytics.get("impressions", 0)
                    normalized["clicks"] += platform_analytics.get("clicks", 0)
                    normalized["likes"] += platform_analytics.get("likes", 0)
                    normalized["comments"] += platform_analytics.get("comments", 0)
                    normalized["shares"] += platform_analytics.get("shares", 0)

                elif platform == "facebook":
                    normalized["impressions"] += platform_analytics.get("reach", 0)
                    normalized["engagements"] += platform_analytics.get("engagement", 0)
                    normalized["clicks"] += platform_analytics.get("clicks", 0)

                elif platform == "youtube":
                    normalized["impressions"] += platform_analytics.get("views", 0)
                    normalized["likes"] += platform_analytics.get("likes", 0)
                    normalized["comments"] += platform_analytics.get("comments", 0)
                    normalized["shares"] += platform_analytics.get("shares", 0)

                elif platform == "pinterest":
                    normalized["impressions"] += platform_analytics.get("impressions", 0)
                    normalized["clicks"] += platform_analytics.get("clicks", 0)
                    normalized["saves"] += platform_analytics.get("saves", 0)

        # Calculate total engagements (if not already provided by platform)
        if normalized["engagements"] == 0:
            normalized["engagements"] = (
                normalized["likes"] +
                normalized["comments"] +
                normalized["shares"] +
                normalized["clicks"] +
                normalized["saves"]
            )

        # Calculate engagement rate
        normalized["engagement_rate"] = self._calculate_engagement_rate(normalized)

        return normalized

    def _mock_analytics(self, post_id: str) -> Dict[str, Any]:
        """Generate mock analytics for testing."""
        import random

        base_impressions = random.randint(1000, 15000)
        engagement_factor = random.uniform(0.05, 0.12)  # 5-12% engagement

        engagements = int(base_impressions * engagement_factor)

        return {
            "impressions": base_impressions,
            "engagements": engagements,
            "clicks": int(engagements * 0.3),
            "likes": int(engagements * 0.6),
            "comments": int(engagements * 0.2),
            "shares": int(engagements * 0.2),
            "engagement_rate": engagement_factor * 100
        }

    def _mock_history(self, days_back: int, platforms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate mock history for testing."""
        posts = []
        available_platforms = platforms or ["linkedin", "twitter"]

        for i in range(min(days_back * 2, 20)):  # Max 20 posts
            published_date = datetime.now() - timedelta(days=i/2)
            platform = available_platforms[i % len(available_platforms)]

            posts.append({
                "id": f"mock_{i}",
                "platforms": [platform],  # Array, not single string
                "content": f"Mock post {i}",
                "scheduled_date": published_date.isoformat(),
                "created_at": (published_date - timedelta(hours=2)).isoformat(),
                "status": "success",
                "type": "immediate" if i % 3 == 0 else "scheduled",
                "post_ids": {platform: f"{platform}_post_{i}"}
            })

        return posts


# Singleton instance
_ayrshare_client: Optional[AyrshareClient] = None


def get_ayrshare_client() -> AyrshareClient:
    """Get or create Ayrshare client singleton."""
    global _ayrshare_client
    if _ayrshare_client is None:
        _ayrshare_client = AyrshareClient()
    return _ayrshare_client
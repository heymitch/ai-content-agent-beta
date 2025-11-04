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

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Ayrshare client.

        Args:
            api_key: Ayrshare API key (defaults to env var AYRSHARE_API_KEY)
        """
        self.api_key = api_key or os.getenv('AYRSHARE_API_KEY')
        self.base_url = "https://api.ayrshare.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.info("Ayrshare integration disabled (no API key)")

    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific post.

        Args:
            post_id: Ayrshare post ID

        Returns:
            Dict with impressions, engagements, clicks, etc.
        """
        if not self.enabled:
            return self._mock_analytics(post_id)

        try:
            response = requests.get(
                f"{self.base_url}/analytics/{post_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Extract relevant metrics
            return {
                "impressions": data.get("impressions", 0),
                "engagements": data.get("engagements", 0),
                "clicks": data.get("clicks", 0),
                "likes": data.get("likes", 0),
                "comments": data.get("comments", 0),
                "shares": data.get("shares", 0),
                "engagement_rate": self._calculate_engagement_rate(data)
            }

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

    def get_history(self, days_back: int = 7, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get posting history with analytics.

        Args:
            days_back: Number of days to look back
            platform: Filter by platform (linkedin, twitter, etc.)

        Returns:
            List of posts with their analytics
        """
        if not self.enabled:
            return self._mock_history(days_back, platform)

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            params = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            }
            if platform:
                params["platform"] = platform

            response = requests.get(
                f"{self.base_url}/history",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # Process and return posts
            posts = []
            for post in data.get("posts", []):
                posts.append({
                    "id": post.get("id"),
                    "platform": post.get("platform"),
                    "content": post.get("content"),
                    "published_at": post.get("publishedAt"),
                    "url": post.get("url"),
                    "analytics": {
                        "impressions": post.get("impressions", 0),
                        "engagements": post.get("engagements", 0),
                        "engagement_rate": self._calculate_engagement_rate(post)
                    }
                })

            return posts

        except Exception as e:
            logger.error(f"Error fetching Ayrshare history: {e}")
            return self._mock_history(days_back, platform)

    def _calculate_engagement_rate(self, data: Dict[str, Any]) -> float:
        """Calculate engagement rate from metrics."""
        impressions = data.get("impressions", 0)
        engagements = data.get("engagements", 0)

        if impressions > 0:
            return (engagements / impressions) * 100
        return 0.0

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

    def _mock_history(self, days_back: int, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate mock history for testing."""
        posts = []
        for i in range(min(days_back * 2, 20)):  # Max 20 posts
            published_date = datetime.now() - timedelta(days=i/2)
            posts.append({
                "id": f"mock_{i}",
                "platform": platform or ("linkedin" if i % 2 == 0 else "twitter"),
                "content": f"Mock post {i}",
                "published_at": published_date.isoformat(),
                "url": f"https://example.com/post/{i}",
                "analytics": self._mock_analytics(f"mock_{i}")
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
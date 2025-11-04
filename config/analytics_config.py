"""
Analytics Configuration

Controls whether analytics features are enabled and how they behave.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime


class AnalyticsConfig:
    """Configuration for analytics features."""

    def __init__(self):
        """Initialize analytics configuration from environment variables."""
        # Core analytics settings
        self.enabled = os.getenv('ANALYTICS_ENABLED', 'false').lower() == 'true'
        self.auto_briefing = os.getenv('ANALYTICS_AUTO_BRIEFING', 'false').lower() == 'true'
        self.briefing_day = os.getenv('ANALYTICS_BRIEFING_DAY', 'monday').lower()
        self.briefing_time = os.getenv('ANALYTICS_BRIEFING_TIME', '09:00')
        self.briefing_channel = os.getenv('ANALYTICS_BRIEFING_CHANNEL', 'content-strategy')

        # Data sources
        self.use_airtable = os.getenv('ANALYTICS_USE_AIRTABLE', 'true').lower() == 'true'
        self.use_ayrshare = os.getenv('ANALYTICS_USE_AYRSHARE', 'false').lower() == 'true'
        self.use_mock_data = os.getenv('ANALYTICS_USE_MOCK_DATA', 'true').lower() == 'true'

        # Analysis settings
        self.min_posts_for_analysis = int(os.getenv('ANALYTICS_MIN_POSTS', '5'))
        self.days_lookback = int(os.getenv('ANALYTICS_DAYS_LOOKBACK', '7'))
        self.include_trending = os.getenv('ANALYTICS_INCLUDE_TRENDING', 'true').lower() == 'true'

        # Performance thresholds
        self.high_engagement_threshold = float(os.getenv('ANALYTICS_HIGH_ENGAGEMENT', '8.0'))
        self.low_engagement_threshold = float(os.getenv('ANALYTICS_LOW_ENGAGEMENT', '3.0'))

    def is_enabled(self) -> bool:
        """Check if analytics is enabled."""
        return self.enabled

    def should_run_briefing(self) -> bool:
        """
        Check if auto-briefing should run now.

        Returns:
            True if it's the right day/time for briefing
        """
        if not self.auto_briefing or not self.enabled:
            return False

        now = datetime.now()
        current_day = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')

        # Check if it's the right day and approximately the right time
        if current_day == self.briefing_day:
            # Check if within 30 minutes of scheduled time
            scheduled_hour, scheduled_min = map(int, self.briefing_time.split(':'))
            current_hour, current_min = map(int, current_time.split(':'))

            time_diff = abs((current_hour * 60 + current_min) - (scheduled_hour * 60 + scheduled_min))
            return time_diff <= 30

        return False

    def get_data_sources(self) -> Dict[str, bool]:
        """Get enabled data sources."""
        return {
            'airtable': self.use_airtable,
            'ayrshare': self.use_ayrshare,
            'mock_data': self.use_mock_data
        }

    def get_analysis_params(self) -> Dict[str, Any]:
        """Get parameters for analysis."""
        return {
            'min_posts': self.min_posts_for_analysis,
            'days_lookback': self.days_lookback,
            'include_trending': self.include_trending,
            'high_engagement_threshold': self.high_engagement_threshold,
            'low_engagement_threshold': self.low_engagement_threshold
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            'enabled': self.enabled,
            'auto_briefing': self.auto_briefing,
            'briefing_schedule': {
                'day': self.briefing_day,
                'time': self.briefing_time,
                'channel': self.briefing_channel
            },
            'data_sources': self.get_data_sources(),
            'analysis_params': self.get_analysis_params()
        }


# Singleton instance
_analytics_config: Optional[AnalyticsConfig] = None


def get_analytics_config() -> AnalyticsConfig:
    """Get or create analytics configuration singleton."""
    global _analytics_config
    if _analytics_config is None:
        _analytics_config = AnalyticsConfig()
    return _analytics_config


def is_analytics_enabled() -> bool:
    """Quick check if analytics is enabled."""
    config = get_analytics_config()
    return config.is_enabled()
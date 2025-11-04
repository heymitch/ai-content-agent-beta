"""
Shared Anthropic Client Manager
Prevents connection exhaustion by reusing a single client across all tools and utilities.
This fixes the Post 6+ hang issue caused by creating 9+ new clients per post.
"""
import os
from anthropic import Anthropic
from typing import Optional

# Global shared client instance
_anthropic_client: Optional[Anthropic] = None


def get_anthropic_client() -> Anthropic:
    """Get or create a shared Anthropic client.

    This prevents connection exhaustion by reusing a single client
    instead of creating new ones for each tool call.

    Returns:
        Anthropic: The shared Anthropic client instance
    """
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        _anthropic_client = Anthropic(api_key=api_key)
    return _anthropic_client


def cleanup_anthropic_client():
    """Clean up the shared Anthropic client.

    Should be called when shutting down or after batch operations.
    """
    global _anthropic_client
    if _anthropic_client is not None:
        try:
            # Anthropic client doesn't have an async close, but we can del it
            # to help garbage collection
            del _anthropic_client
        except:
            pass
        finally:
            _anthropic_client = None
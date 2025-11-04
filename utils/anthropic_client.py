"""
Shared Anthropic Client Manager
Prevents connection exhaustion by reusing a single client across all tools and utilities.
This fixes the Post 6+ hang issue caused by creating 9+ new clients per post.
"""
import os
import logging
from anthropic import Anthropic
from typing import Optional

# Setup logging
logger = logging.getLogger(__name__)

# Global shared client instance
_anthropic_client: Optional[Anthropic] = None
_client_request_count = 0


def get_anthropic_client() -> Anthropic:
    """Get or create a shared Anthropic client.

    This prevents connection exhaustion by reusing a single client
    instead of creating new ones for each tool call.

    Returns:
        Anthropic: The shared Anthropic client instance
    """
    global _anthropic_client, _client_request_count

    if _anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        _anthropic_client = Anthropic(api_key=api_key)
        print(f"🔌 [SHARED CLIENT] Created NEW Anthropic client (should see this ONCE)", flush=True)
        logger.info("Created new shared Anthropic client")
    else:
        _client_request_count += 1
        if _client_request_count % 5 == 0:  # Log every 5 requests to avoid spam
            print(f"♻️  [SHARED CLIENT] Reusing existing client (request #{_client_request_count})", flush=True)
            logger.debug(f"Reusing shared Anthropic client (request #{_client_request_count})")

    return _anthropic_client


def cleanup_anthropic_client():
    """Clean up the shared Anthropic client.

    Should be called when shutting down or after batch operations.
    """
    global _anthropic_client, _client_request_count

    if _anthropic_client is not None:
        print(f"🧹 [SHARED CLIENT] Cleaning up Anthropic client (served {_client_request_count} requests)", flush=True)
        logger.info(f"Cleaning up shared Anthropic client after {_client_request_count} requests")
        try:
            # Anthropic client doesn't have an async close, but we can del it
            # to help garbage collection
            del _anthropic_client
        except:
            pass
        finally:
            _anthropic_client = None
            _client_request_count = 0
            print(f"✅ [SHARED CLIENT] Cleanup complete", flush=True)
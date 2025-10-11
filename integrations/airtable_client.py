"""
Airtable client for content calendar management
Replaces n8n webhook integration with direct Airtable API calls
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

class AirtableContentCalendar:
    """
    Manages content calendar records in Airtable

    Table Fields:
    - Post Hook: Opening line/headline
    - Body Content: Full content text
    - Media/Thumbnail: Image/video URL (optional)
    - Status: Draft, Scheduled, Published, etc.
    - Client: Client name (e.g., "Agency Content Autopilot")
    - Platform: linkedin, twitter, email, etc.
    - Publish Date: When to publish
    - Suggested Edits: AI feedback or manual notes
    - % Score: Quality score from validation (0-100)
    - Edited Time: Last edit timestamp
    - Created: Record creation timestamp
    """

    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_ACCESS_TOKEN')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME')

        if not all([self.api_key, self.base_id, self.table_name]):
            raise ValueError("Missing Airtable credentials. Set AIRTABLE_ACCESS_TOKEN, AIRTABLE_BASE_ID, and AIRTABLE_TABLE_NAME in .env")

        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)

    def create_content_record(
        self,
        content: str,
        platform: str,
        publish_date: Optional[str] = None,
        post_hook: Optional[str] = None,
        client: str = "Agency Content Autopilot",
        status: str = "Draft",
        quality_score: Optional[int] = None,
        suggested_edits: Optional[str] = None,
        media_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new content calendar record in Airtable

        Args:
            content: Full content body text
            platform: linkedin, twitter, email, etc.
            publish_date: ISO date string (YYYY-MM-DD) or None for unscheduled
            post_hook: Opening line/headline (auto-extracted if not provided)
            client: Client name
            status: Draft, Scheduled, Published, etc.
            quality_score: Validation score (0-100)
            suggested_edits: AI feedback or manual notes
            media_url: URL to image/video
            metadata: Additional metadata (conversation_id, user_id, etc.)

        Returns:
            Created Airtable record
        """

        # Auto-extract hook from content if not provided
        if not post_hook and content:
            post_hook = self._extract_hook(content, platform)

        # Build Airtable fields
        # Platform is a multi-select field in Airtable, so it needs to be an array
        # Note: 'Created' and 'Edited Time' are auto-computed fields in Airtable
        # Note: 'Client' might be a select field - only include if you have permission to set it
        fields = {
            'Body Content': content,
            'Platform': [platform.capitalize()],  # Array for multi-select field
            'Status': status,
        }

        # Only add Client if provided and not using default (to avoid select field issues)
        if client and client != "Agency Content Autopilot":
            fields['Client'] = client

        # Add optional fields only if provided
        if post_hook:
            fields['Post Hook'] = post_hook

        if publish_date:
            # Ensure date is in YYYY-MM-DD format for Airtable
            fields['Publish Date'] = publish_date

        if quality_score is not None:
            fields['% Score'] = quality_score

        if suggested_edits:
            fields['Suggested Edits'] = suggested_edits

        if media_url:
            fields['Media/Thumbnail'] = media_url

        # Store metadata as JSON string in Suggested Edits if no edits provided
        if metadata and not suggested_edits:
            import json
            fields['Suggested Edits'] = json.dumps(metadata)

        try:
            record = self.table.create(fields)
            return {
                'success': True,
                'record_id': record['id'],
                'fields': record['fields'],
                'url': f"https://airtable.com/{self.base_id}/{self.table_name}/{record['id']}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def update_content_record(
        self,
        record_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing Airtable record

        Args:
            record_id: Airtable record ID
            fields: Dictionary of fields to update

        Returns:
            Updated record data
        """
        try:
            # Note: 'Edited Time' is auto-computed in Airtable, don't set it manually
            record = self.table.update(record_id, fields)
            return {
                'success': True,
                'record_id': record['id'],
                'fields': record['fields']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_content_record(self, record_id: str) -> Dict[str, Any]:
        """Fetch a specific record by ID"""
        try:
            record = self.table.get(record_id)
            return {
                'success': True,
                'record': record
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_content_records(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        max_records: int = 100
    ) -> Dict[str, Any]:
        """
        List content records with optional filters

        Args:
            platform: Filter by platform
            status: Filter by status
            max_records: Max number of records to return

        Returns:
            List of records
        """
        try:
            formula_parts = []

            if platform:
                formula_parts.append(f"{{Platform}} = '{platform.capitalize()}'")

            if status:
                formula_parts.append(f"{{Status}} = '{status}'")

            formula = None
            if formula_parts:
                formula = f"AND({', '.join(formula_parts)})"

            records = self.table.all(
                formula=formula,
                max_records=max_records,
                sort=['-Created']  # Most recent first
            )

            return {
                'success': True,
                'records': records,
                'count': len(records)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_hook(self, content: str, platform: str) -> str:
        """
        Extract the hook/opening line from content

        Args:
            content: Full content text
            platform: Platform type to determine extraction logic

        Returns:
            First line or sentence as hook
        """
        if not content:
            return ""

        # Clean HTML if present
        import re
        text = re.sub(r'<[^>]+>', '', content)
        text = text.strip()

        if platform.lower() == 'email':
            # For email, extract subject line if present
            lines = text.split('\n')
            for line in lines[:3]:
                if line.startswith('Subject:'):
                    return line.replace('Subject:', '').strip()
            # Otherwise first line
            return lines[0] if lines else ""

        elif platform.lower() == 'twitter':
            # For Twitter, get first tweet
            tweets = text.split('\n\n')
            first_tweet = tweets[0] if tweets else text
            # Remove thread numbering like "1/7"
            first_tweet = re.sub(r'^\d+/\d+\s*', '', first_tweet)
            return first_tweet[:100] + ('...' if len(first_tweet) > 100 else '')

        else:
            # For LinkedIn/other, get first line
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            return lines[0] if lines else text[:100]


# Singleton instance
_airtable_client = None

def get_airtable_client() -> AirtableContentCalendar:
    """Get or create Airtable client singleton"""
    global _airtable_client
    if _airtable_client is None:
        _airtable_client = AirtableContentCalendar()
    return _airtable_client

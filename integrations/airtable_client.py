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

        # Clean content before saving (remove SDK metadata/headers)
        clean_content = self._clean_content(content)

        # Prevent saving blank content
        if not clean_content or len(clean_content.strip()) < 10:
            return {
                'success': False,
                'error': 'Content is empty or too short after cleaning'
            }

        # Auto-extract hook from content if not provided
        if not post_hook and clean_content:
            post_hook = self._extract_hook(clean_content, platform)

        # Build Airtable fields
        # Platform is a multi-select field in Airtable, so it needs to be an array
        # Note: 'Created' and 'Edited Time' are auto-computed fields in Airtable
        # Note: 'Client' is a select field - don't set it to avoid permission errors

        # Map internal platform names to Airtable options (case-sensitive)
        platform_mapping = {
            'linkedin': 'Linkedin',
            'twitter': 'X/twitter',  # Matches Airtable field option
            'email': 'Email',  # Add this option to Airtable Platform field
            'youtube': 'Youtube'
        }
        airtable_platform = platform_mapping.get(platform.lower(), platform.capitalize())

        fields = {
            'Body Content': clean_content,  # Save only clean post content
            'Platform': [airtable_platform],  # Array for multi-select field
            'Status': status,
        }

        # Don't set Client field - it's a restricted select dropdown in Airtable
        # Users can manually set it in Airtable UI

        # Add optional fields only if provided
        if post_hook:
            fields['Post Hook'] = post_hook

        if publish_date:
            # Ensure date is in YYYY-MM-DD format for Airtable
            fields['Publish Date'] = publish_date

        # Don't set quality_score - field doesn't exist in Airtable
        # if quality_score is not None:
        #     fields['% Score'] = quality_score

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

    def _clean_content(self, content: str) -> str:
        """
        Strip SDK output metadata and headers to get clean post content.

        Removes:
        - "---" dividers
        - "POST 1:", "POST 2:", etc.
        - "Final LinkedIn Post", "Final Twitter Thread", etc.
        - Score/metadata lines
        - "(Estimated Score: X/Y)" lines
        - "Changes Applied:" sections

        Args:
            content: Raw SDK output

        Returns:
            Clean post content only
        """
        if not content:
            return ""

        import re

        # Clean HTML if present
        text = re.sub(r'<[^>]+>', '', content)
        text = text.strip()

        # Split into lines
        lines = text.split('\n')
        clean_lines = []
        skip_rest = False

        for line in lines:
            stripped = line.strip()

            # Skip horizontal dividers
            if stripped == '---' or stripped.startswith('==='):
                continue

            # Skip headers like "POST 1:", "POST 2:", etc.
            if re.match(r'^(POST|THREAD|EMAIL|SCRIPT)\s*\d*:', stripped, re.IGNORECASE):
                continue

            # Skip "Final [Platform] Post" headers (with optional markdown ## and emojis)
            # Handles: "## ✅ Final Twitter Thread (Score: 24+/25)"
            if re.match(r'^#+\s*[✅✓]?\s*Final (LinkedIn|Twitter|Email|YouTube)', stripped, re.IGNORECASE):
                continue
            if re.match(r'^[✅✓]?\s*Final (LinkedIn|Twitter|Email|YouTube)', stripped, re.IGNORECASE):
                continue

            # Skip score lines
            if re.search(r'(Estimated Score|Quality Score):', stripped, re.IGNORECASE):
                continue

            # Skip "Changes Applied:" and everything after
            if re.match(r'^Changes Applied:', stripped, re.IGNORECASE):
                skip_rest = True
                continue

            if skip_rest:
                continue

            # Skip empty lines at the start
            if not clean_lines and not stripped:
                continue

            clean_lines.append(line)

        # Join and clean up extra whitespace
        cleaned = '\n'.join(clean_lines).strip()
        return cleaned

    def _extract_hook(self, content: str, platform: str) -> str:
        """
        Extract the hook/opening line from content

        Args:
            content: Full content text (should be pre-cleaned)
            platform: Platform type to determine extraction logic

        Returns:
            First 200 chars of actual post content as hook
        """
        if not content:
            return ""

        import re

        # Clean content first
        text = self._clean_content(content)

        if platform.lower() == 'email':
            # For email, extract subject line if present
            lines = text.split('\n')
            for line in lines[:3]:
                if line.startswith('Subject:'):
                    return line.replace('Subject:', '').strip()
            # Otherwise first non-empty line
            non_empty = [l.strip() for l in lines if l.strip()]
            return non_empty[0][:200] if non_empty else ""

        elif platform.lower() == 'twitter':
            # For Twitter, get first tweet
            tweets = text.split('\n\n')
            first_tweet = tweets[0] if tweets else text
            # Remove thread numbering like "1/7"
            first_tweet = re.sub(r'^\d+/\d+\s*', '', first_tweet)
            # Return first 200 chars
            return first_tweet[:200].strip()

        else:
            # For LinkedIn/YouTube/other, get first 200 chars
            non_empty_lines = [l.strip() for l in text.split('\n') if l.strip()]
            first_content = '\n'.join(non_empty_lines) if non_empty_lines else text
            return first_content[:200].strip()


def get_airtable_client() -> AirtableContentCalendar:
    """
    Create a fresh Airtable client instance.

    Note: No singleton caching to support multi-tenant deployments
    where different instances may use different table IDs.
    """
    return AirtableContentCalendar()

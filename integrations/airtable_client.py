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
            'twitter': 'X/Twitter',  # Exact match for Airtable field option
            'email': 'Email',  # Add this option to Airtable Platform field
            'youtube': 'Youtube',
            'instagram': 'Instagram'  # Add Instagram support
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
            fields['Suggested Edits'] = json.dumps(metadata, ensure_ascii=False)

        try:
            record = self.table.create(fields)
            return {
                'success': True,
                'record_id': record['id'],
                'fields': record['fields'],
                'url': f"https://airtable.com/{self.base_id}/{self.table.id}/{record['id']}"
            }
        except Exception as e:
            error_str = str(e).lower()

            # Detect quota/rate limit errors
            is_quota_error = any(keyword in error_str for keyword in [
                'quota', 'rate limit', 'too many requests', '429', 'limit exceeded'
            ])

            return {
                'success': False,
                'error': str(e),
                'is_quota_error': is_quota_error,
                'fallback_message': 'Airtable quota exceeded. Saved to Supabase only.' if is_quota_error else None
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

    def search_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        days_back: int = 30,
        keyword: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search content calendar for posts matching criteria.

        Args:
            platform: linkedin, twitter, email, youtube, instagram
            status: Draft, Scheduled, Published, Archived
            days_back: How far back to search (default 30 days)
            keyword: Text to search in Post Hook and Body Content
            max_results: Maximum number of results to return

        Returns:
            Dict with results array containing record_id, hook, body_preview, platform, status, dates
        """
        from datetime import datetime, timedelta

        try:
            formula_parts = []

            # Platform filter (handle mapping)
            if platform:
                platform_mapping = {
                    'linkedin': 'Linkedin',
                    'twitter': 'X/Twitter',
                    'email': 'Email',
                    'youtube': 'Youtube',
                    'instagram': 'Instagram'
                }
                airtable_platform = platform_mapping.get(platform.lower(), platform.capitalize())
                formula_parts.append(f"FIND('{airtable_platform}', ARRAYJOIN({{Platform}}, ','))")

            # Status filter
            if status:
                formula_parts.append(f"{{Status}} = '{status}'")

            # Date range filter
            if days_back:
                cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                formula_parts.append(f"IS_AFTER({{Created}}, '{cutoff}')")

            # Keyword search in Post Hook and Body Content
            if keyword:
                # Case-insensitive search using FIND with LOWER
                keyword_escaped = keyword.replace("'", "\\'")
                formula_parts.append(
                    f"OR(FIND(LOWER('{keyword_escaped}'), LOWER({{Post Hook}})), "
                    f"FIND(LOWER('{keyword_escaped}'), LOWER({{Body Content}})))"
                )

            # Combine filters
            formula = None
            if formula_parts:
                formula = f"AND({', '.join(formula_parts)})"

            # Fetch records
            records = self.table.all(
                formula=formula,
                max_records=max_results,
                sort=['-Created']  # Most recent first
            )

            # Format results for agent consumption
            results = []
            for record in records:
                fields = record.get('fields', {})
                body = fields.get('Body Content', '')

                results.append({
                    'record_id': record.get('id'),
                    'hook': fields.get('Post Hook', '')[:200],
                    'body_preview': body[:300] + '...' if len(body) > 300 else body,
                    'platform': fields.get('Platform', []),
                    'status': fields.get('Status', ''),
                    'publish_date': fields.get('Publish Date', ''),
                    'created': fields.get('Created', ''),
                    'score': fields.get('% Score', 0),
                    'url': f"https://airtable.com/{self.base_id}/{self.table_name}/{record.get('id')}"
                })

            return {
                'success': True,
                'total_found': len(results),
                'results': results
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }

    def get_posts_in_range(self, start_date, end_date):
        """
        Fetch posts from Airtable within a date range.

        Args:
            start_date: datetime object for start of range
            end_date: datetime object for end of range

        Returns:
            List of post records with their fields
        """
        try:
            # Format dates for Airtable filter
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Build filter formula
            # Airtable formula: AND(IS_AFTER({Publish Date}, 'start'), IS_BEFORE({Publish Date}, 'end'))
            formula = f"AND(IS_AFTER({{Publish Date}}, '{start_str}'), IS_BEFORE({{Publish Date}}, DATEADD('{end_str}', 1, 'days')))"

            # Fetch records with filter
            records = self.table.all(formula=formula)

            # Extract fields from records
            posts = []
            for record in records:
                fields = record.get('fields', {})
                fields['record_id'] = record.get('id')  # Include record ID
                posts.append(fields)

            return posts

        except Exception as e:
            print(f"Error fetching posts from Airtable: {e}")
            return []

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
        - Agent commentary ("✅ ALL CONTENT COMPLETE", "Key themes across all three formats", etc.)
        - "---" dividers
        - "POST 1:", "POST 2:", "1. LINKEDIN POST", "2. THREE TWITTER POSTS", etc.
        - "Final LinkedIn Post", "Final Twitter Thread", etc.
        - Score/metadata lines
        - "(Estimated Score: X/Y)" lines
        - "Changes Applied:" sections
        - Multi-platform summaries

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
        found_content_start = False

        for line in lines:
            stripped = line.strip()

            # Skip agent commentary patterns
            if re.match(r'^[✅✓🚀🎯]\s*(ALL CONTENT COMPLETE|Key themes|Ready to ship|Posted above)', stripped, re.IGNORECASE):
                continue

            # Skip horizontal dividers
            if stripped == '---' or stripped.startswith('===') or re.match(r'^-{3,}$', stripped):
                continue

            # Skip numbered section headers like "1. LINKEDIN POST", "2. THREE TWITTER POSTS", "3. YOUTUBE SCRIPT"
            if re.match(r'^\d+\.\s+(LINKEDIN|TWITTER|EMAIL|YOUTUBE|THREE\s+TWITTER)', stripped, re.IGNORECASE):
                continue

            # Skip headers like "POST 1:", "POST 2:", "Tweet 1:", "Tweet 2:", etc.
            if re.match(r'^(POST|THREAD|EMAIL|SCRIPT|TWEET)\s*\d*:', stripped, re.IGNORECASE):
                continue

            # Skip "Final [Platform] Post" headers (with optional markdown ## and emojis)
            # Handles: "## ✅ Final Twitter Thread (Score: 24+/25)" or "✅ FINAL EMAIL (Score: 22/25)"
            if re.match(r'^#+\s*[✅✓]?\s*Final (LinkedIn|Twitter|Email|YouTube)', stripped, re.IGNORECASE):
                continue
            if re.match(r'^[✅✓]?\s*Final (LinkedIn|Twitter|Email|YouTube)', stripped, re.IGNORECASE):
                continue

            # Skip score lines and "Final Score:" or "(Score: X/25)"
            if re.search(r'(Estimated Score|Quality Score|Final Score|\(Score:\s*\d+/\d+\))', stripped, re.IGNORECASE):
                continue

            # Skip "Subject:" and "Preview:" lines (for email body - hook extracts these separately)
            if re.match(r'^(Subject|Preview):', stripped, re.IGNORECASE):
                continue

            # Skip "Title:" and "Structure:" lines (YouTube metadata)
            if re.match(r'^(Title|Structure):', stripped, re.IGNORECASE):
                continue

            # Skip section markers like "Hook (0:00-0:30):", "Section 1 (0:30-2:30):"
            if re.search(r'^\w+\s*\(\d+:\d+-\d+:\d+\):', stripped):
                continue

            # Stop at "Final Score:" - this marks end of actual content
            if re.match(r'^Final Score:', stripped, re.IGNORECASE):
                skip_rest = True
                continue

            # Stop at agent conversation patterns
            if re.match(r'^(Changes Applied:|Ready to send|Key themes|Full script saved|What changed:)', stripped, re.IGNORECASE):
                skip_rest = True
                continue

            # Stop at summary patterns
            if re.match(r'^(All content emphasizes|Ready to ship|Post now scores)', stripped, re.IGNORECASE):
                skip_rest = True
                continue

            if skip_rest:
                continue

            # Skip "Posted above -" commentary lines
            if re.match(r'^Posted above', stripped, re.IGNORECASE):
                continue

            # Skip empty lines at the start
            if not clean_lines and not stripped:
                continue

            # If we've found actual content, keep track
            if stripped and not found_content_start:
                found_content_start = True

            clean_lines.append(line)

        # Join and clean up extra whitespace
        cleaned = '\n'.join(clean_lines).strip()

        # Remove trailing whitespace and multiple blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

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
            # For email, extract subject line from RAW content (before cleaning strips it)
            # Don't use cleaned text - we need the "Subject:" line
            raw_lines = content.split('\n')
            for line in raw_lines[:10]:  # Check first 10 lines
                if line.strip().startswith('Subject:'):
                    return line.replace('Subject:', '').strip()
            # Fallback: first non-empty line from cleaned text
            non_empty = [l.strip() for l in text.split('\n') if l.strip()]
            return non_empty[0][:200] if non_empty else ""

        elif platform.lower() == 'twitter':
            # For Twitter, get first tweet (handle multiple tweet formats)
            # Remove "Tweet 1:", "Tweet 2:" patterns first
            text = re.sub(r'^Tweet\s+\d+\s*(\([^)]+\))?:', '', text, flags=re.MULTILINE|re.IGNORECASE)

            # Split on double newlines to get individual tweets
            tweets = text.split('\n\n')
            first_tweet = tweets[0] if tweets else text

            # Remove thread numbering like "1/7" or "(Contrarian Hook)"
            first_tweet = re.sub(r'^\d+/\d+\s*', '', first_tweet)
            first_tweet = re.sub(r'^\([^)]+\):\s*', '', first_tweet)

            # Return first 200 chars
            return first_tweet[:200].strip()

        else:
            # For LinkedIn/YouTube/other, get first 200 chars
            non_empty_lines = [l.strip() for l in text.split('\n') if l.strip()]
            first_content = '\n'.join(non_empty_lines) if non_empty_lines else text
            return first_content[:200].strip()

    def update_analytics(
        self,
        record_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update analytics fields for an Airtable record.

        Args:
            record_id: Airtable record ID
            metrics: Dictionary with analytics data:
                - impressions (int)
                - engagements (int)
                - clicks (int)
                - likes (int)
                - comments (int)
                - shares (int)
                - engagement_rate (float)
                - last_analytics_sync (datetime or ISO string)

        Returns:
            {
                "success": bool,
                "record_id": str,
                "fields": {...}  (if success)
                "error": str  (if failure)
            }
        """
        try:
            # Build Airtable fields for analytics
            fields = {}

            # Add numeric metrics if present
            if 'impressions' in metrics:
                fields['Impressions'] = int(metrics['impressions'] or 0)

            if 'engagements' in metrics:
                fields['Engagements'] = int(metrics['engagements'] or 0)

            if 'clicks' in metrics:
                fields['Clicks'] = int(metrics['clicks'] or 0)

            if 'likes' in metrics:
                fields['Likes'] = int(metrics['likes'] or 0)

            if 'comments' in metrics:
                fields['Comments'] = int(metrics['comments'] or 0)

            if 'shares' in metrics:
                fields['Shares'] = int(metrics['shares'] or 0)

            # Engagement rate as percentage (Airtable percent field expects 0-1, we store as 0-100)
            if 'engagement_rate' in metrics:
                rate = float(metrics['engagement_rate'] or 0)
                # If rate > 1, assume it's already in percentage (0-100), convert to 0-1
                fields['Engagement Rate'] = rate / 100 if rate > 1 else rate

            # Last synced timestamp
            if 'last_analytics_sync' in metrics:
                sync_time = metrics['last_analytics_sync']
                # Convert to ISO string if datetime object
                if hasattr(sync_time, 'isoformat'):
                    fields['Last Synced'] = sync_time.isoformat()
                else:
                    fields['Last Synced'] = sync_time

            # Update the record
            record = self.table.update(record_id, fields)

            return {
                'success': True,
                'record_id': record['id'],
                'fields': record['fields']
            }

        except Exception as e:
            return {
                'success': False,
                'record_id': record_id,
                'error': str(e)
            }


def get_airtable_client() -> AirtableContentCalendar:
    """
    Create a fresh Airtable client instance.

    Note: No singleton caching to support multi-tenant deployments
    where different instances may use different table IDs.
    """
    return AirtableContentCalendar()

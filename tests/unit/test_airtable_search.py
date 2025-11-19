"""
Unit tests for Airtable search functionality (Phase 3)
Tests search_posts, get_airtable_post_content, and agent tool wrappers
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSearchPostsFormula:
    """Tests for Airtable formula building in search_posts"""

    @pytest.fixture
    def mock_airtable_client(self):
        """Create mock Airtable client"""
        from integrations.airtable_client import AirtableClient

        with patch.object(AirtableClient, '__init__', lambda x: None):
            client = AirtableClient()
            client.table = Mock()
            client.base_id = 'app123'
            client.table_name = 'Content Calendar'
            return client

    def test_platform_mapping_linkedin(self, mock_airtable_client):
        """'linkedin' maps to 'Linkedin' in Airtable"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(platform='linkedin')

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert "FIND('Linkedin'" in formula

    def test_platform_mapping_twitter(self, mock_airtable_client):
        """'twitter' maps to 'X/Twitter' in Airtable"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(platform='twitter')

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert "FIND('X/Twitter'" in formula

    def test_status_filter_exact_match(self, mock_airtable_client):
        """Status filter uses exact match"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(status='Draft')

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert "{Status} = 'Draft'" in formula

    def test_keyword_search_case_insensitive(self, mock_airtable_client):
        """Keyword search is case-insensitive"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(keyword='AI')

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        # Should use LOWER() for case-insensitive
        assert "LOWER('ai')" in formula or "LOWER('{keyword}')" in formula.replace('AI', '{keyword}')

    def test_keyword_searches_hook_and_body(self, mock_airtable_client):
        """Keyword search checks both Post Hook and Body Content"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(keyword='test')

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert "Post Hook" in formula
        assert "Body Content" in formula

    def test_keyword_escapes_single_quotes(self, mock_airtable_client):
        """Keywords with single quotes are escaped"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(keyword="it's a test")

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        # Should escape the quote
        assert "\\'" in formula or "it\\'s" in formula

    def test_combined_filters_use_and(self, mock_airtable_client):
        """Multiple filters are combined with AND"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(
            platform='linkedin',
            status='Published',
            keyword='AI'
        )

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert formula.startswith("AND(")

    def test_date_range_filter(self, mock_airtable_client):
        """Date range uses IS_AFTER with cutoff date"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(days_back=30)

        call_args = mock_airtable_client.table.all.call_args
        formula = call_args[1]['formula']
        assert "IS_AFTER({Created}" in formula

    def test_max_results_limit(self, mock_airtable_client):
        """Respects max_results parameter"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts(max_results=5)

        call_args = mock_airtable_client.table.all.call_args
        assert call_args[1]['max_records'] == 5

    def test_results_sorted_by_created_desc(self, mock_airtable_client):
        """Results are sorted by Created date descending"""
        mock_airtable_client.table.all = Mock(return_value=[])

        mock_airtable_client.search_posts()

        call_args = mock_airtable_client.table.all.call_args
        assert call_args[1]['sort'] == ['-Created']


class TestSearchPostsResults:
    """Tests for search_posts result formatting"""

    @pytest.fixture
    def mock_airtable_client(self):
        """Create mock Airtable client"""
        from integrations.airtable_client import AirtableClient

        with patch.object(AirtableClient, '__init__', lambda x: None):
            client = AirtableClient()
            client.table = Mock()
            client.base_id = 'app123'
            client.table_name = 'tbl456'
            return client

    def test_formats_results_correctly(self, mock_airtable_client):
        """Results include all expected fields"""
        mock_airtable_client.table.all = Mock(return_value=[
            {
                'id': 'rec123',
                'fields': {
                    'Post Hook': 'Test hook',
                    'Body Content': 'Test body content here',
                    'Platform': ['Linkedin'],
                    'Status': 'Published',
                    'Publish Date': '2024-01-15',
                    'Created': '2024-01-10',
                    '% Score': 85
                }
            }
        ])

        result = mock_airtable_client.search_posts()

        assert result['success'] is True
        assert result['total_found'] == 1
        post = result['results'][0]
        assert post['record_id'] == 'rec123'
        assert post['hook'] == 'Test hook'
        assert post['platform'] == ['Linkedin']
        assert post['status'] == 'Published'
        assert post['score'] == 85
        assert 'airtable.com' in post['url']

    def test_truncates_long_body(self, mock_airtable_client):
        """Body content is truncated to 300 chars with ellipsis"""
        long_body = 'A' * 500
        mock_airtable_client.table.all = Mock(return_value=[
            {
                'id': 'rec123',
                'fields': {
                    'Body Content': long_body,
                    'Post Hook': 'Hook'
                }
            }
        ])

        result = mock_airtable_client.search_posts()

        post = result['results'][0]
        assert len(post['body_preview']) <= 303  # 300 + '...'
        assert post['body_preview'].endswith('...')

    def test_empty_results(self, mock_airtable_client):
        """Returns empty array for no matches"""
        mock_airtable_client.table.all = Mock(return_value=[])

        result = mock_airtable_client.search_posts()

        assert result['success'] is True
        assert result['total_found'] == 0
        assert result['results'] == []

    def test_api_error_handling(self, mock_airtable_client):
        """Returns error dict on API failure"""
        mock_airtable_client.table.all = Mock(
            side_effect=Exception('API Error')
        )

        result = mock_airtable_client.search_posts()

        assert result['success'] is False
        assert 'error' in result
        assert 'API Error' in result['error']


class TestSearchAirtablePostsTool:
    """Tests for the agent tool wrapper search_airtable_posts"""

    def test_returns_formatted_results(self):
        """Tool returns formatted markdown string"""
        from slack_bot.agent_tools import search_airtable_posts

        with patch('slack_bot.agent_tools.get_airtable_client') as mock_get:
            mock_client = Mock()
            mock_client.search_posts.return_value = {
                'success': True,
                'results': [
                    {
                        'record_id': 'rec123',
                        'hook': 'Test hook',
                        'platform': ['Linkedin'],
                        'status': 'Published',
                        'publish_date': '2024-01-15',
                        'score': 85,
                        'url': 'https://airtable.com/...'
                    }
                ]
            }
            mock_get.return_value = mock_client

            result = search_airtable_posts(platform='linkedin')

            assert 'Found 1 post' in result
            assert 'Test hook' in result
            assert 'rec123' in result

    def test_no_results_message(self):
        """Returns helpful message when no posts found"""
        from slack_bot.agent_tools import search_airtable_posts

        with patch('slack_bot.agent_tools.get_airtable_client') as mock_get:
            mock_client = Mock()
            mock_client.search_posts.return_value = {
                'success': True,
                'results': []
            }
            mock_get.return_value = mock_client

            result = search_airtable_posts(
                platform='linkedin',
                keyword='nonexistent'
            )

            assert 'No posts found' in result

    def test_airtable_not_configured(self):
        """Returns error when Airtable not configured"""
        from slack_bot.agent_tools import search_airtable_posts

        with patch('slack_bot.agent_tools.get_airtable_client', return_value=None):
            result = search_airtable_posts()

            assert 'not configured' in result


class TestGetAirtablePostContent:
    """Tests for the get_airtable_post_content tool"""

    def test_returns_full_content(self):
        """Tool returns complete post content with metadata"""
        from slack_bot.agent_tools import get_airtable_post_content

        with patch('slack_bot.agent_tools.get_airtable_client') as mock_get:
            mock_client = Mock()
            mock_client.base_id = 'app123'
            mock_client.table_name = 'tbl456'
            mock_client.get_content_record.return_value = {
                'success': True,
                'record': {
                    'id': 'rec123',
                    'fields': {
                        'Platform': ['Linkedin'],
                        'Status': 'Published',
                        'Publish Date': '2024-01-15',
                        '% Score': 85,
                        'Post Hook': 'This is the hook',
                        'Body Content': 'This is the full body content'
                    }
                }
            }
            mock_get.return_value = mock_client

            result = get_airtable_post_content('rec123')

            assert 'Post Content' in result
            assert 'Linkedin' in result
            assert 'This is the hook' in result
            assert 'This is the full body content' in result

    def test_record_not_found(self):
        """Returns error when record doesn't exist"""
        from slack_bot.agent_tools import get_airtable_post_content

        with patch('slack_bot.agent_tools.get_airtable_client') as mock_get:
            mock_client = Mock()
            mock_client.get_content_record.return_value = {
                'success': False,
                'error': 'Record not found'
            }
            mock_get.return_value = mock_client

            result = get_airtable_post_content('invalid_id')

            assert 'Failed to retrieve' in result


class TestToolRegistration:
    """Tests that tools are properly registered for agent use"""

    def test_search_tool_in_content_tools(self):
        """search_airtable_posts is in CONTENT_TOOLS"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool_names = [t['name'] for t in CONTENT_TOOLS]
        assert 'search_airtable_posts' in tool_names

    def test_get_content_tool_in_content_tools(self):
        """get_airtable_post_content is in CONTENT_TOOLS"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool_names = [t['name'] for t in CONTENT_TOOLS]
        assert 'get_airtable_post_content' in tool_names

    def test_search_tool_registered_in_functions(self):
        """search_airtable_posts is in TOOL_FUNCTIONS"""
        from slack_bot.agent_tools import TOOL_FUNCTIONS

        assert 'search_airtable_posts' in TOOL_FUNCTIONS

    def test_get_content_tool_registered_in_functions(self):
        """get_airtable_post_content is in TOOL_FUNCTIONS"""
        from slack_bot.agent_tools import TOOL_FUNCTIONS

        assert 'get_airtable_post_content' in TOOL_FUNCTIONS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

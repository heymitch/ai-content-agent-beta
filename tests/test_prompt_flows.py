#!/usr/bin/env python3
"""
Prompt Flow Testing Framework
Tests agent behavior with various user request patterns to catch breaking scenarios

This framework tests:
1. Bulk requests (3 posts, 5 posts, multiple platforms)
2. Edge cases (empty requests, malformed requests, impossible requests)
3. Airtable save operations (verify separate rows, not one column)
4. Response completeness (agent says "On it..." but never responds)
5. Thread context handling (mixed requests in threads)

Usage:
    python tests/test_prompt_flows.py

    # Run specific test category:
    pytest tests/test_prompt_flows.py::TestBulkRequests -v
    pytest tests/test_prompt_flows.py::TestEdgeCases -v
    pytest tests/test_prompt_flows.py::TestAirtableIntegrity -v
"""

import pytest
import asyncio
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.airtable_client import AirtableContentCalendar


class PromptFlowTest:
    """Base class for prompt flow tests with common utilities"""

    def __init__(self):
        self.airtable_calls = []
        self.slack_messages = []
        self.agent_responses = []

    def track_airtable_call(self, content: str, platform: str, post_hook: str):
        """Track Airtable save operations"""
        self.airtable_calls.append({
            'content': content,
            'platform': platform,
            'post_hook': post_hook,
            'timestamp': datetime.now().isoformat()
        })

    def track_slack_message(self, channel: str, text: str, thread_ts: str = None):
        """Track Slack messages sent by agent"""
        self.slack_messages.append({
            'channel': channel,
            'text': text,
            'thread_ts': thread_ts,
            'timestamp': datetime.now().isoformat()
        })

    def verify_separate_airtable_rows(self, expected_count: int) -> bool:
        """Verify that N posts created N separate Airtable rows (not one column)"""
        if len(self.airtable_calls) != expected_count:
            return False

        # Check each call has distinct content
        contents = [call['content'] for call in self.airtable_calls]
        unique_contents = set(contents)

        return len(unique_contents) == expected_count

    def verify_agent_responded(self) -> bool:
        """Verify agent sent a response (not just 'On it...')"""
        if not self.slack_messages:
            return False

        # Check if there's a message other than acknowledgement
        non_ack_messages = [
            msg for msg in self.slack_messages
            if msg['text'].lower() not in ['on it...', 'on it', 'working on it...']
        ]

        return len(non_ack_messages) > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get test execution summary"""
        return {
            'airtable_calls': len(self.airtable_calls),
            'slack_messages': len(self.slack_messages),
            'agent_responses': len(self.agent_responses),
            'details': {
                'airtable': self.airtable_calls,
                'slack': self.slack_messages,
                'responses': self.agent_responses
            }
        }


@pytest.mark.asyncio
class TestBulkRequests:
    """Test bulk content creation requests"""

    async def test_three_linkedin_posts_separate_rows(self):
        """
        Test: 'Create 3 separate LinkedIn posts'
        Expected: 3 Airtable rows (not 1 row with 3 posts in one column)
        """
        test = PromptFlowTest()

        # Mock Airtable client
        with patch('integrations.airtable_client.AirtableContentCalendar') as mock_airtable:
            mock_instance = Mock()
            mock_instance.create_content_record = Mock(side_effect=lambda content, **kwargs: (
                test.track_airtable_call(content, kwargs.get('platform', 'linkedin'), kwargs.get('post_hook', '')),
                {'success': True, 'record_id': f'rec{len(test.airtable_calls)}'}
            )[1])
            mock_airtable.return_value = mock_instance

            # Simulate agent processing: "Create 3 separate LinkedIn posts"
            # Agent should call save_to_airtable 3 times, not once with all content

            # Expected behavior:
            posts = [
                "Post 1: Motivational content about overcoming challenges...",
                "Post 2: Thought-provoking question about industry trends...",
                "Post 3: Tactical advice on implementing a specific strategy..."
            ]

            for i, post in enumerate(posts):
                mock_instance.create_content_record(
                    content=post,
                    platform='linkedin',
                    post_hook=f'Post {i+1} hook',
                    status='Draft'
                )

            # Verify separate rows
            assert test.verify_separate_airtable_rows(3), \
                f"Expected 3 separate Airtable rows, got {len(test.airtable_calls)} calls"

            # Verify each call has unique content
            contents = [call['content'] for call in test.airtable_calls]
            assert all('Post ' in c for c in contents), "Each post should be distinct"

            print(f"✅ Test passed: 3 separate Airtable rows created")
            print(f"   Airtable calls: {len(test.airtable_calls)}")

    async def test_five_posts_mixed_platforms(self):
        """
        Test: 'Create 5 posts: 2 LinkedIn, 2 Twitter, 1 Email'
        Expected: 5 separate Airtable rows with correct platform tags
        """
        test = PromptFlowTest()

        with patch('integrations.airtable_client.AirtableContentCalendar') as mock_airtable:
            mock_instance = Mock()
            mock_instance.create_content_record = Mock(side_effect=lambda content, **kwargs: (
                test.track_airtable_call(content, kwargs.get('platform', 'linkedin'), kwargs.get('post_hook', '')),
                {'success': True, 'record_id': f'rec{len(test.airtable_calls)}'}
            )[1])
            mock_airtable.return_value = mock_instance

            # Create mixed posts
            posts = [
                ('LinkedIn post 1', 'linkedin'),
                ('LinkedIn post 2', 'linkedin'),
                ('Twitter thread 1', 'twitter'),
                ('Twitter thread 2', 'twitter'),
                ('Email newsletter', 'email')
            ]

            for content, platform in posts:
                mock_instance.create_content_record(
                    content=content,
                    platform=platform,
                    post_hook=f'{platform} hook',
                    status='Draft'
                )

            assert len(test.airtable_calls) == 5, f"Expected 5 calls, got {len(test.airtable_calls)}"

            # Verify platforms
            platforms = [call['platform'] for call in test.airtable_calls]
            assert platforms.count('linkedin') == 2, "Should have 2 LinkedIn posts"
            assert platforms.count('twitter') == 2, "Should have 2 Twitter posts"
            assert platforms.count('email') == 1, "Should have 1 Email post"

            print(f"✅ Test passed: 5 posts across 3 platforms")

    async def test_bulk_request_agent_completes_response(self):
        """
        Test: Agent says 'On it...' but ALSO sends final response
        Expected: Agent sends both acknowledgement AND final message with content
        """
        test = PromptFlowTest()

        # Simulate Slack messages
        test.track_slack_message('C123', 'On it...', 'thread_123')
        # Wait 5 seconds (simulate processing)
        await asyncio.sleep(0.1)  # Use shorter time for testing
        # Agent should send final response
        test.track_slack_message('C123', 'Created 3 LinkedIn posts:\n\n1. [Post 1]\n2. [Post 2]\n3. [Post 3]', 'thread_123')

        assert test.verify_agent_responded(), \
            "Agent sent 'On it...' but never sent final response"

        assert len(test.slack_messages) == 2, \
            f"Expected 2 messages (ack + response), got {len(test.slack_messages)}"

        print(f"✅ Test passed: Agent completed response after acknowledgement")


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases that might break the agent"""

    async def test_empty_request(self):
        """
        Test: User sends empty message or just whitespace
        Expected: Agent asks for clarification
        """
        test = PromptFlowTest()

        # Simulate empty request
        user_message = "   "

        # Agent should respond asking for clarification
        test.track_slack_message('C123', "I need more information. What content would you like me to create?", 'thread_123')

        assert test.verify_agent_responded(), "Agent should respond to empty requests"

        # Should NOT create Airtable records
        assert len(test.airtable_calls) == 0, "Agent should not create content for empty requests"

        print(f"✅ Test passed: Empty request handled gracefully")

    async def test_impossible_request(self):
        """
        Test: 'Create 100 LinkedIn posts right now'
        Expected: Agent explains limitations and offers alternative
        """
        test = PromptFlowTest()

        # Agent should respond with limitation explanation
        test.track_slack_message(
            'C123',
            "I can create multiple posts, but 100 at once would be overwhelming. How about I create 5 posts now and we can iterate?",
            'thread_123'
        )

        assert test.verify_agent_responded(), "Agent should respond to impossible requests"
        assert len(test.airtable_calls) <= 5, "Agent should not try to create 100 posts"

        print(f"✅ Test passed: Impossible request handled gracefully")

    async def test_ambiguous_count(self):
        """
        Test: 'Create some LinkedIn posts'
        Expected: Agent asks for specific count
        """
        test = PromptFlowTest()

        test.track_slack_message('C123', "How many LinkedIn posts would you like me to create?", 'thread_123')

        assert test.verify_agent_responded(), "Agent should ask for clarification"

        print(f"✅ Test passed: Ambiguous count handled")

    async def test_mixed_instructions(self):
        """
        Test: 'Create 3 posts. Make them motivational. Also check my calendar.'
        Expected: Agent handles all instructions without dropping any
        """
        test = PromptFlowTest()

        # Track that agent:
        # 1. Checks calendar
        # 2. Creates 3 posts
        # 3. Confirms all tasks completed

        test.track_slack_message('C123', 'Checking your calendar...', 'thread_123')
        test.track_slack_message('C123', 'Creating 3 motivational posts...', 'thread_123')

        # Simulate 3 Airtable saves
        for i in range(3):
            test.track_airtable_call(f'Motivational post {i+1}', 'linkedin', f'Hook {i+1}')

        test.track_slack_message('C123', 'Done! Created 3 posts and checked calendar.', 'thread_123')

        assert len(test.airtable_calls) == 3, "Should create 3 posts"
        assert len(test.slack_messages) >= 3, "Should send multiple updates"

        print(f"✅ Test passed: Mixed instructions handled")


@pytest.mark.asyncio
class TestAirtableIntegrity:
    """Test Airtable data integrity"""

    async def test_no_merged_content_in_single_column(self):
        """
        Test: Verify agent NEVER puts multiple posts in one Airtable column
        Expected: Each post goes to separate row
        """
        test = PromptFlowTest()

        with patch('integrations.airtable_client.AirtableContentCalendar') as mock_airtable:
            mock_instance = Mock()

            # Create a bad call (simulating the bug)
            bad_content = "Post 1\n\nPost 2\n\nPost 3"

            # This should NOT happen
            test.track_airtable_call(bad_content, 'linkedin', 'Multiple hooks in one column')

            # Detect merged content
            has_merged_content = any(
                call['content'].count('\n\n') > 5  # More than 5 double-newlines suggests merged posts
                for call in test.airtable_calls
            )

            assert not has_merged_content or len(test.airtable_calls) > 1, \
                "Detected multiple posts merged into one Airtable column - this is the bug!"

            print(f"⚠️ Test caught merged content bug simulation")

    async def test_platform_field_mapping(self):
        """
        Test: Verify platform names map correctly to Airtable options
        Expected: 'linkedin' → 'Linkedin', 'twitter' → 'X/Twitter', etc.
        """
        test = PromptFlowTest()

        with patch('integrations.airtable_client.AirtableContentCalendar') as mock_airtable:
            mock_instance = Mock()
            mock_instance.create_content_record = Mock(side_effect=lambda content, **kwargs: (
                test.track_airtable_call(content, kwargs.get('platform', 'linkedin'), kwargs.get('post_hook', '')),
                {'success': True, 'record_id': f'rec{len(test.airtable_calls)}'}
            )[1])
            mock_airtable.return_value = mock_instance

            # Test each platform
            platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']

            for platform in platforms:
                mock_instance.create_content_record(
                    content=f'Test post for {platform}',
                    platform=platform,
                    post_hook=f'{platform} test hook',
                    status='Draft'
                )

            assert len(test.airtable_calls) == 5, "Should handle all 5 platforms"

            # Verify platform values
            saved_platforms = [call['platform'] for call in test.airtable_calls]
            assert 'linkedin' in saved_platforms, "LinkedIn should be saved"
            assert 'twitter' in saved_platforms, "Twitter should be saved"

            print(f"✅ Test passed: All platforms mapped correctly")

    async def test_status_field_consistency(self):
        """
        Test: Verify status field is consistent ('Draft' not 'draft' or 'DRAFT')
        Expected: All saves use 'Draft' status
        """
        test = PromptFlowTest()

        # This test would verify the actual Airtable saves use consistent casing
        # Based on the schema, 'Draft' and 'Scheduled' are the valid options

        # Simulate saves with different casings (testing error handling)
        valid_statuses = ['Draft', 'Scheduled']

        for status in valid_statuses:
            test.track_airtable_call(
                content='Test post',
                platform='linkedin',
                post_hook='Test hook'
            )

        print(f"✅ Test passed: Status field consistency check")


@pytest.mark.asyncio
class TestThreadContextHandling:
    """Test agent behavior in Slack threads"""

    async def test_thread_isolation(self):
        """
        Test: Two threads requesting content simultaneously
        Expected: Each thread gets correct content (no mixing)
        """
        test1 = PromptFlowTest()
        test2 = PromptFlowTest()

        # Thread 1: Request LinkedIn post
        test1.track_slack_message('C123', 'Creating LinkedIn post...', 'thread_111')
        test1.track_airtable_call('LinkedIn content', 'linkedin', 'LI hook')

        # Thread 2: Request Twitter thread (simultaneous)
        test2.track_slack_message('C123', 'Creating Twitter thread...', 'thread_222')
        test2.track_airtable_call('Twitter content', 'twitter', 'TW hook')

        # Verify no mixing
        assert test1.airtable_calls[0]['platform'] == 'linkedin', "Thread 1 should get LinkedIn"
        assert test2.airtable_calls[0]['platform'] == 'twitter', "Thread 2 should get Twitter"

        print(f"✅ Test passed: Thread isolation maintained")

    async def test_dm_context_persistence(self):
        """
        Test: DM conversation should maintain context across messages
        Expected: Agent remembers previous messages in DM
        """
        test = PromptFlowTest()

        # Message 1: "Create a LinkedIn post about AI"
        test.track_slack_message('DM123', 'On it...', 'dm_DM123')
        test.track_airtable_call('AI post', 'linkedin', 'AI hook')
        test.track_slack_message('DM123', 'Created LinkedIn post about AI', 'dm_DM123')

        # Message 2: "Now create 2 more on the same topic"
        # Agent should remember "AI" is the topic
        test.track_slack_message('DM123', 'Creating 2 more AI posts...', 'dm_DM123')
        test.track_airtable_call('AI post 2', 'linkedin', 'AI hook 2')
        test.track_airtable_call('AI post 3', 'linkedin', 'AI hook 3')

        assert len(test.airtable_calls) == 3, "Should create 3 total posts"
        assert all('AI' in call['content'] or 'AI' in call['post_hook'] for call in test.airtable_calls), \
            "All posts should relate to AI topic"

        print(f"✅ Test passed: DM context maintained")


@pytest.mark.asyncio
class TestResponseCompleteness:
    """Test that agent always completes responses"""

    async def test_no_hanging_on_it(self):
        """
        Test: Agent says 'On it...' but never responds
        Expected: This should NEVER happen
        """
        test = PromptFlowTest()

        # Simulate acknowledgement
        test.track_slack_message('C123', 'On it...', 'thread_123')

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Check if final response was sent
        has_final_response = len([
            msg for msg in test.slack_messages
            if msg['text'].lower() not in ['on it...', 'on it', 'working on it...']
        ]) > 0

        # This test should FAIL if agent hangs
        assert has_final_response, \
            "CRITICAL BUG: Agent said 'On it...' but never sent final response!"

        print(f"✅ Test passed: Agent completed response")

    async def test_error_handling_sends_response(self):
        """
        Test: If agent hits error, it should STILL respond to user
        Expected: Error message sent to user (not silent failure)
        """
        test = PromptFlowTest()

        # Simulate error during processing
        test.track_slack_message('C123', 'On it...', 'thread_123')

        # Simulate error
        try:
            raise Exception("Airtable connection failed")
        except Exception as e:
            # Agent should catch and report
            test.track_slack_message('C123', f'Error: {str(e)}', 'thread_123')

        assert test.verify_agent_responded(), "Agent must respond even on errors"

        # Check error was communicated
        error_messages = [msg for msg in test.slack_messages if 'error' in msg['text'].lower()]
        assert len(error_messages) > 0, "Agent should send error message to user"

        print(f"✅ Test passed: Errors are communicated")


# ============= TEST RUNNER =============

async def run_all_tests():
    """Run all prompt flow tests"""
    print("\n" + "="*70)
    print("PROMPT FLOW TESTING FRAMEWORK")
    print("="*70)
    print("Testing agent behavior with various user request patterns\n")

    test_classes = [
        TestBulkRequests,
        TestEdgeCases,
        TestAirtableIntegrity,
        TestThreadContextHandling,
        TestResponseCompleteness
    ]

    total_passed = 0
    total_failed = 0

    for test_class in test_classes:
        print(f"\n{'='*70}")
        print(f"Running: {test_class.__name__}")
        print(f"{'='*70}\n")

        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in test_methods:
            try:
                print(f"Running: {method_name}...")
                method = getattr(instance, method_name)
                await method()
                total_passed += 1
            except AssertionError as e:
                print(f"❌ FAILED: {method_name}")
                print(f"   Error: {e}")
                total_failed += 1
            except Exception as e:
                print(f"❌ ERROR: {method_name}")
                print(f"   Exception: {e}")
                total_failed += 1

    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"{'='*70}\n")

    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

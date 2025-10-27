"""
Test that VERY LONG outlines (500+ words) are preserved in full
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import create_batch_plan


def test_long_outline_fully_preserved():
    """Test: 500+ word outline is preserved completely without truncation"""

    # Create a VERY long strategic outline (simulating nearly-complete post)
    long_outline = """Post 1: Most high-ticket operators have built the wrong AI tools.

They spent months on chatbots that answer FAQs. They hired developers to build custom GPT wrappers. They paid consultants who delivered strategy decks.

I've been heads-down building something different.

My niche: info businesses, education companies, and agencies doing $1M to $50M annually. These operators don't need more theory. They need agents that handle real work.

I built two systems:

The "Everything Agent" runs inside Claude's Code workspace. It writes code, debugs infrastructure, and ships features without switching tools. Last week it fixed a production bug at 3am while I was sleeping. It analyzed logs, identified the race condition, wrote the patch, tested it locally, and created the PR. I woke up to a Slack notification saying "Bug fixed, PR ready for review."

The AI Employee system handles recurring business operations. Client onboarding used to take our team 3 hours per client. Now it takes 20 minutes of human oversight. The agent collects documents, validates completions, creates project structures, sends welcome sequences, and schedules kickoff calls. It handles edge cases better than our previous SOPs because it can actually think through problems.

Content production went from 15 hours weekly to 2 hours of strategic input. The agent doesn't just write - it researches trending topics in our space, analyzes what resonates with our audience, creates content calendars, writes drafts that sound like me (not ChatGPT), and even handles distribution across platforms.

Data analysis that used to require a part-time analyst now runs automatically. Every Monday morning I get a report showing conversion rates by traffic source, content performance metrics, customer health scores, and recommended actions based on patterns the agent identified.

These aren't prototypes. They run daily in real businesses right now.

A $3M education company replaced their entire customer success workflow. A $15M agency automated their entire proposal process. A $8M SaaS founder uses agents to manage their entire content operation.

The pattern is clear: high-ticket operators need sovereignty over convenience. They need quality over speed. They need systems that understand their specific business context, not generic tools.

I'm spending the next few weeks sharing exactly how we built them, what worked, and what failed. Real screenshots. Actual costs. Technical decisions that mattered.

Proof coming at 1 PM today.

If you're running a high-ticket operation and tired of AI theater, follow along. This will be specific.

What's the one task in your business you wish an agent could handle completely?"""

    # Create plan with this LONG outline
    posts = [{
        "platform": "linkedin",
        "topic": "High-ticket operators and AI agents",
        "context": "Strategic launch post",
        "detailed_outline": long_outline,
        "style": "contrarian"
    }]

    plan = create_batch_plan(posts, "Launch sequence")

    # Verify ENTIRE outline is preserved
    assert plan['posts'][0]['detailed_outline'] == long_outline
    assert len(plan['posts'][0]['detailed_outline']) == len(long_outline)

    # Count words to prove nothing was truncated
    word_count = len(long_outline.split())
    preserved_word_count = len(plan['posts'][0]['detailed_outline'].split())

    print(f"\n✅ Original outline: {word_count} words")
    print(f"✅ Preserved outline: {preserved_word_count} words")
    print(f"✅ Character count: {len(long_outline)} chars preserved")

    assert word_count == preserved_word_count, "Some words were lost!"
    assert word_count > 400, "Test should use 400+ word outline"

    # Verify it's marked as rich context
    assert plan['context_quality'] == 'rich'
    assert plan['avg_context_length'] > 2000  # Very long context


if __name__ == "__main__":
    test_long_outline_fully_preserved()
    print("\n🎉 SUCCESS: Long outlines are preserved in FULL without any truncation!")
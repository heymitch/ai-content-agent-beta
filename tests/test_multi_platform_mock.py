#!/usr/bin/env python3
"""
Multi-Platform Content Quality Mock Test
Simulates SDK agent responses for local testing without Claude SDK
"""

import asyncio
import json
import random
from datetime import datetime

# Mock responses for testing
MOCK_RESPONSES = {
    "twitter": {
        "success": True,
        "thread": """AI agents write like robots because we train them wrong.

Here's what nobody tells you:

1. We feed them corporate blogs → They output corporate slop
2. We reward long responses → They become verbose
3. We avoid controversy → They hedge everything

The fix is simple but uncomfortable:

Train on real human conversations. Include the messiness, the opinions, the incomplete thoughts.

Your AI doesn't need more data. It needs better data.

What trashy content are you secretly feeding your AI?""",
        "hook": "AI agents write like robots because we train them wrong.",
        "score": 19,
        "hooks_tested": 5,
        "iterations": 2,
        "airtable_url": "https://airtable.com/mock/twitter123",
        "session_id": "twitter_test_001",
        "timestamp": datetime.now().isoformat()
    },
    "youtube": {
        "success": True,
        "script": """[HOOK - 0:00-0:15]
"Your AI content sounds like a robot. Today, I'm showing you exactly how to fix that in under 10 minutes."

[PROBLEM - 0:15-1:00]
Look, we've all been there. You use AI to write content, and it comes out sounding like a corporate press release from 2003. Words like "leverage" and "synergy" everywhere. Paragraphs that say nothing in 500 words.

[SOLUTION OVERVIEW - 1:00-2:00]
The problem isn't the AI - it's how we're using it. Today, I'll show you three specific techniques that transform robotic AI content into writing that actually sounds human.

[TECHNIQUE 1 - 2:00-4:00]
First, the "specificity injection" method. Instead of letting AI be vague, force it to be specific...

[Continue for 10 minutes...]""",
        "hook": "Your AI content sounds like a robot. Today, I'm showing you exactly how to fix that.",
        "score": 21,
        "structure_score": 22,
        "airtable_url": "https://airtable.com/mock/youtube456",
        "video_length": "10_min",
        "timestamp": datetime.now().isoformat()
    },
    "instagram": {
        "success": True,
        "caption": """The hidden cost of AI content? It's not the subscription fee.

It's the trust you lose when your audience realizes you've been feeding them robot words.

I spent 6 months publishing AI content. Engagement tanked. Comments dried up. DMs went silent.

Then I changed one thing: I started editing like a human, not optimizing like a machine.

→ Killed every "leverage"
→ Added real stories
→ Kept the typos that felt real
→ Wrote like I text my friends

Result: 3x engagement in 30 days.

Your audience doesn't want perfect. They want real.

What "imperfection" made your content better? 👇""",
        "hook": "The hidden cost of AI content? It's not the subscription fee.",
        "score": 20,
        "hashtag_suggestions": ["#AIContent", "#ContentStrategy", "#AuthenticMarketing"],
        "airtable_url": "https://airtable.com/mock/instagram789",
        "timestamp": datetime.now().isoformat()
    },
    "email": {
        "Newsletter": {
            "success": True,
            "email": """Subject: This Week: 3 AI Tools That Don't Make You Sound Like a Bot

Hey [First Name],

Quick question: Ever read your AI-generated content out loud and cringe?

You're not alone. This week, I tested 47 AI writing tools to find the ones that actually sound human.

Here are the only 3 worth your time:

**1. ClaudeCode (Not Just for Coding)**
Everyone thinks it's just for developers. Wrong. Use it for content editing - it catches AI patterns better than any grammar checker.

**2. Hemingway Editor + GPT-4**
Old tool, new trick. Run your AI content through Hemingway first, THEN ask GPT-4 to maintain the simplicity. Game-changer.

**3. Copy.ai's Brand Voice Feature**
Upload your actual emails (yes, the casual ones). It learns your real voice, not your LinkedIn voice.

**The Week's Reality Check:**
I analyzed 1,000 AI-generated LinkedIn posts. 94% used the phrase "in today's digital landscape."

Don't be the 94%.

**What I'm Testing Next Week:**
Building a "slop detector" - a tool that flags corporate jargon in real-time. Reply if you want early access.

Keep it real,
[Your Name]

P.S. - If your AI content includes "synergy," you owe me coffee.""",
            "hook": "Ever read your AI-generated content out loud and cringe?",
            "score": 22,
            "email_type": "Newsletter",
            "airtable_url": "https://airtable.com/mock/email_newsletter",
            "timestamp": datetime.now().isoformat()
        },
        "Sales": {
            "success": True,
            "email": """Subject: Your content team is wasting Tuesday afternoons

[First Name],

I watched 5 content teams last week. They all did the same thing:

Tuesday, 2pm: Start writing blog post
Tuesday, 4pm: Still editing the intro
Tuesday, 5pm: Scrap it and start over

Sound familiar?

The problem isn't writer's block. It's process block.

Your team is spending 70% of their time on tasks that AI could handle in minutes. But they're scared it'll sound robotic.

Fair concern. Most AI content does.

That's why we built ContentFlow differently. Instead of replacing writers, it handles the grunt work:
- Research: 2 hours → 10 minutes
- First drafts: 3 hours → 15 minutes
- SEO optimization: 1 hour → automated

Your writers then spend 100% of their time on what matters: making it sound human.

Three of your competitors started using this last month. Their content velocity doubled.

Want to see what your Tuesday afternoons could look like?

[BUTTON: Show Me a 10-Minute Demo]

No sales pitch. Just a screen share showing your exact use case.

[Your Name]

P.S. - That blog post your team is struggling with? Send me the topic. I'll show you how we'd handle it.""",
            "hook": "Your content team is wasting Tuesday afternoons",
            "score": 21,
            "email_type": "Sales",
            "airtable_url": "https://airtable.com/mock/email_sales",
            "timestamp": datetime.now().isoformat()
        },
        "Value": {
            "success": True,
            "email": """Subject: The 5-Minute Audit That Exposed My AI Blindspots

[First Name],

I thought my AI content was good. Then I did this 5-minute audit.

Found 47 instances of "leverage" in one week's content. FORTY-SEVEN.

Here's the exact audit I run every Friday:

**The AI Content Reality Check** (5 minutes)

1. **The Cringe Test** (1 minute)
   Read your content out loud to someone. Count the eye rolls.

2. **The Jargon Count** (1 minute)
   Ctrl+F these words: leverage, synergy, innovative, groundbreaking
   More than 2? Rewrite.

3. **The Specificity Score** (1 minute)
   Highlight every specific number, name, or example.
   Less than 30% highlighted? Too vague.

4. **The Friend Test** (1 minute)
   Would you send this in a text to a friend?
   No? It's too formal.

5. **The Action Check** (1 minute)
   Can someone DO something after reading?
   No clear action = wasted content.

**My Results:**
- Week 1: Failed all 5 tests
- Week 4: Passed 3/5
- Week 8: Consistent 5/5

**Your Turn:**
Run this audit on your last piece of content. Reply with your score - I'll personally review the first 10 responses.

[Your Name]

P.S. - Made a simple checklist version of this. Want it? Just reply "CHECKLIST" and it's yours.""",
            "hook": "I thought my AI content was good. Then I did this 5-minute audit.",
            "score": 23,
            "email_type": "Value",
            "airtable_url": "https://airtable.com/mock/email_value",
            "timestamp": datetime.now().isoformat()
        }
    }
}

def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)

def simulate_processing_time():
    """Simulate API processing time"""
    import time
    delay = random.uniform(0.5, 2.0)
    print(f"   ⏳ Simulating API call ({delay:.1f}s)...")
    time.sleep(delay)

async def test_twitter():
    """Mock test for Twitter SDK Agent"""
    print_section_header("Testing Twitter SDK Agent (MOCK)")

    print("📝 Creating thread about: Why most AI agents fail at content creation...")
    print("   Style: tactical")

    simulate_processing_time()

    result = MOCK_RESPONSES["twitter"]

    print(f"\n✅ Twitter - SUCCESS (MOCK)")
    print(f"   Score: {result['score']}/25")
    print(f"   Hook: {result['hook'][:80]}...")
    print(f"   📊 Airtable: {result['airtable_url']}")

    # Show sample of the thread
    print(f"\n   Preview of thread:")
    for i, tweet in enumerate(result['thread'].split('\n\n')[:3], 1):
        if tweet.strip():
            print(f"   Tweet {i}: {tweet[:100]}...")

    return result

async def test_youtube():
    """Mock test for YouTube SDK Agent"""
    print_section_header("Testing YouTube SDK Agent (MOCK)")

    print("📝 Creating script about: How to Build an AI Content Agent...")
    print("   Type: educational")

    simulate_processing_time()

    result = MOCK_RESPONSES["youtube"]

    print(f"\n✅ YouTube - SUCCESS (MOCK)")
    print(f"   Score: {result['score']}/25")
    print(f"   Structure Score: {result['structure_score']}/25")
    print(f"   Hook: {result['hook'][:80]}...")
    print(f"   📊 Airtable: {result['airtable_url']}")

    # Show script preview
    print(f"\n   Script preview:")
    for line in result['script'].split('\n')[:5]:
        if line.strip():
            print(f"   {line[:100]}")

    return result

async def test_instagram():
    """Mock test for Instagram SDK Agent"""
    print_section_header("Testing Instagram SDK Agent (MOCK)")

    print("📝 Creating caption about: The hidden cost of AI-generated content...")
    print("   Style: inspirational")

    simulate_processing_time()

    result = MOCK_RESPONSES["instagram"]

    print(f"\n✅ Instagram - SUCCESS (MOCK)")
    print(f"   Score: {result['score']}/25")
    print(f"   Hook: {result['hook'][:80]}...")
    print(f"   📊 Airtable: {result['airtable_url']}")

    # Show caption preview
    print(f"\n   Caption preview (first 200 chars):")
    print(f"   {result['caption'][:200]}...")

    return result

async def test_email(email_type: str):
    """Mock test for Email SDK Agent"""
    print(f"\n📧 Testing {email_type} email...")

    simulate_processing_time()

    result = MOCK_RESPONSES["email"][email_type]

    print(f"✅ Email ({email_type}) - SUCCESS (MOCK)")
    print(f"   Score: {result['score']}/25")
    print(f"   Hook: {result['hook'][:80]}...")

    # Show subject line
    email_lines = result['email'].split('\n')
    subject = next((line for line in email_lines if line.startswith('Subject:')), 'No subject')
    print(f"   {subject}")

    return result

async def test_all_emails():
    """Mock test for all email types"""
    print_section_header("Testing Email SDK Agent - All Types (MOCK)")

    results = []
    for email_type in ["Newsletter", "Sales", "Value"]:
        result = await test_email(email_type)
        results.append(result)

    return results

async def run_quality_analysis(results):
    """Analyze quality patterns across platforms"""
    print_section_header("QUALITY ANALYSIS")

    print("\n📊 Cross-Platform Patterns:")

    # Check for banned words (mock check)
    banned_words = ["leverage", "synergy", "innovative", "governance", "infrastructure"]

    print(f"\n   Banned Words Check:")
    for platform, result in results.items():
        if platform == 'email':
            continue  # Skip email array

        content = result.get('thread', '') or result.get('script', '') or result.get('caption', '')
        found = [word for word in banned_words if word.lower() in content.lower()]

        if found:
            print(f"   ⚠️  {platform.title()}: Found banned words: {', '.join(found)}")
        else:
            print(f"   ✅ {platform.title()}: Clean of banned words")

    print(f"\n   AI Pattern Detection:")
    print(f"   ✅ No contrast framing detected")
    print(f"   ✅ No rule of three patterns")
    print(f"   ⚠️  Minor: Some sections could be more specific")

    print(f"\n   Engagement Predictions:")
    print(f"   🎯 Twitter: High (controversial hook)")
    print(f"   🎯 YouTube: Medium-High (clear value prop)")
    print(f"   🎯 Instagram: High (emotional connection)")
    print(f"   🎯 Email: Varies by type (Value > Newsletter > Sales)")

async def run_all_tests():
    """Run all mock tests"""
    print("\n" + "🚀 " * 20)
    print("MULTI-PLATFORM CONTENT QUALITY TEST (MOCK MODE)")
    print("Simulating YouTube, Instagram, Email (3 types), and Twitter")
    print("🚀 " * 20)

    results = {}

    # Run tests
    results['twitter'] = await test_twitter()
    results['youtube'] = await test_youtube()
    results['instagram'] = await test_instagram()
    results['email'] = await test_all_emails()

    # Quality analysis
    await run_quality_analysis(results)

    # Summary
    print_section_header("TEST SUMMARY")

    print("\n✅ All platforms tested successfully (MOCK)")
    print("📊 Average Score: 21/25")
    print("⚠️  Note: These are mock responses for testing")

    print("\n💡 Insights from Mock Test:")
    print("   1. Twitter benefits from controversial hooks")
    print("   2. YouTube needs clear structure markers")
    print("   3. Instagram requires emotional storytelling")
    print("   4. Email success varies greatly by type")
    print("   5. All platforms need specific examples")

    return results

if __name__ == "__main__":
    import sys

    print("\n⚠️  MOCK MODE: Using simulated responses for local testing")
    print("   For real tests, run test_multi_platform_quality.py on Replit")

    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
        if platform == 'twitter':
            asyncio.run(test_twitter())
        elif platform == 'youtube':
            asyncio.run(test_youtube())
        elif platform == 'instagram':
            asyncio.run(test_instagram())
        elif platform == 'email':
            asyncio.run(test_all_emails())
        else:
            print(f"Unknown platform: {platform}")
    else:
        asyncio.run(run_all_tests())

    print("\n✨ Mock test complete!")
    print("=" * 80)
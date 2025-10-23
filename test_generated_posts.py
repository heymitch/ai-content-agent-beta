"""
Test generated_posts integration
Tests that posts save to both Airtable and Supabase with embeddings
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_linkedin_save():
    """Test LinkedIn agent saves to both Airtable + Supabase"""
    print("\n" + "="*60)
    print("TEST: LinkedIn Post → Airtable + Supabase Save")
    print("="*60)

    # Sample post (your Daniel post from the selection)
    sample_post = """LinkedIn's reach is sh*t right now.

So, here's what I'm doing about it:

Now, before I get into any of the tactical stuff, there's 1 important question to address:

"Why care about impressions?"

Assuming the quality of the impressions is the same, then you probably want to have more impressions (not less).

Because at the end of the day...

More impressions = more email subscribers = potential customers/clients = more revenue.

Now, I've seen some people say they're getting less impressions but the "quality" of those impressions is higher.

And while that *could* be true, I don't have any data to back it up.

So instead of just hoping things get better, here are 4 things I'm doing to continue to grow my traffic:

1/ Collaborations with other creators/writers

There are numerous possibilities on this front, but I'm particularly interested in conducting "joint viral giveaways" with other creators.

For example:

This past Wednesday, I conducted a viral giveaway collaboration with my friend Matthew Brown.

The results were quite positive. We successfully generated 450+ email subscribers between the two of us.

Therefore, I'm definitely planning to conduct more experiments like this.

2/ Doubling down on Substack

I have been writing on Substack for the past 1-2 months, and it has been an excellent experience.

I'm very optimistic about the platform's distribution engine and believe it has the potential to become what Twitter was during 2020-2023.

Consequently, I'm definitely going to increase the amount of effort and thought I dedicate to the platform each week (rather than treating it merely as a place to repurpose my LinkedIn content).

3/ Doubling down on social selling

During the past year, I've conducted numerous "social selling" experiments to accelerate my traffic and distribution.

The results have been pleasantly surprising.

However, there remains significant untapped potential!

Therefore, now that reach has decreased, I'm planning to double down on this approach and experiment with more advanced tactics such as sending outbound connection requests and proactively reaching out to individuals who are engaging with my content.

4/ Doubling down on email

My perspective on email is:

It serves as an insurance policy against the volatility of social platforms and algorithms.

As I implement these changes and conduct these experiments, the primary question will continue to be:

"How can I maximize the number of email subscribers I'm obtaining from my content, social selling, etc.?"

Additionally, I want to experiment with novel methods to utilize email to accelerate social traffic, ensuring the entire flywheel continues to gain momentum.

And that concludes my thoughts!

I hope you can extract some useful ideas for your own implementation from this post.

If you're also contemplating new approaches to try/experiment in response to declining reach, please share your thoughts below.

I would greatly appreciate hearing your perspective."""

    # Import LinkedIn agent
    from agents.linkedin_sdk_agent import LinkedInSDKAgent

    print("\n📝 Creating LinkedIn agent...")
    agent = LinkedInSDKAgent(user_id="test_user_123")

    print("\n🔄 Parsing post output (simulating agent creation)...")
    result = await agent._parse_output(sample_post)

    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"✅ Success: {result.get('success')}")
    print(f"📊 Hook: {result.get('hook')[:80]}...")
    print(f"📈 Quality Score: {result.get('score')}")
    print(f"🔗 Airtable URL: {result.get('airtable_url')}")
    print(f"🗄️  Supabase ID: {result.get('supabase_id')}")

    # Verify in Supabase
    if result.get('supabase_id'):
        print("\n🔍 Verifying record in Supabase...")
        from integrations.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        verify = supabase.table('generated_posts').select('*').eq('id', result['supabase_id']).execute()

        if verify.data:
            record = verify.data[0]
            print(f"   ✅ Record found!")
            print(f"   - Platform: {record['platform']}")
            print(f"   - Content Type: {record['content_type']}")
            print(f"   - Status: {record['status']}")
            print(f"   - Has Embedding: {record['embedding'] is not None}")
            print(f"   - Airtable Record ID: {record['airtable_record_id']}")
            print(f"   - Created By: {record['created_by_agent']}")
            print(f"   - Body Length: {len(record['body_content'])} chars")

            # Test semantic search
            print("\n🔍 Testing semantic search...")
            from tools.research_tools import generate_embedding

            query_embedding = generate_embedding("how to grow impressions on LinkedIn")
            search_results = supabase.rpc('search_generated_posts', {
                'query_embedding': query_embedding,
                'filter_platform': 'linkedin',
                'match_count': 3
            }).execute()

            if search_results.data:
                print(f"   ✅ Found {len(search_results.data)} similar posts")
                for i, post in enumerate(search_results.data, 1):
                    print(f"   {i}. {post['post_hook'][:60]}... (similarity: {post['similarity']:.2f})")
            else:
                print("   ⚠️ No search results (this is the first post)")
        else:
            print("   ❌ Record not found in Supabase")

    return result


async def test_content_type_detection():
    """Test content type detection"""
    print("\n" + "="*60)
    print("TEST: Content Type Detection")
    print("="*60)

    from agents.linkedin_sdk_agent import LinkedInSDKAgent

    agent = LinkedInSDKAgent(user_id="test_user")

    test_cases = [
        ("1. First point\n2. Second point\n3. Third point", "listicle"),
        ("I spent $15K and lost everything. Here's what happened:", "story"),
        ("Everyone thinks AI is a bubble. They're wrong.", "hot_take"),
        ("LinkedIn vs Twitter: Which is better for B2B?", "comparison"),
        ("Here's my framework for content strategy", "thought_leadership"),
    ]

    for content, expected in test_cases:
        detected = agent._detect_content_type(content)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{content[:50]}...' → {detected} (expected: {expected})")


async def main():
    """Run all tests"""
    try:
        # Test 1: Content type detection
        await test_content_type_detection()

        # Test 2: Full save workflow
        result = await test_linkedin_save()

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)

        if result.get('supabase_id'):
            print("\n🎉 SUCCESS: Post saved to both Airtable + Supabase")
            print(f"   Supabase ID: {result['supabase_id']}")
            print(f"   Airtable URL: {result.get('airtable_url')}")
        else:
            print("\n⚠️  Post saved to Airtable but Supabase save may have failed")
            print("   Check error messages above")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

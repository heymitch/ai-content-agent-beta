# Batch Processing Guide

Generate 10 posts in 15 minutes, or 100 posts in 2.5 hours. This guide shows you how to use batch processing for multi-platform content campaigns.

---

## Quick Start

**Generate 10 posts in 15 minutes:**

```
User: "Create 10 LinkedIn posts about sovereign AI using my strategic outline"
```

The agent will:
1. Read your strategic outline from this conversation
2. Check `cloud.md` for your active platforms
3. Create 10 posts **sequentially** (safe, no rate limit issues)
4. Each post takes ~90 seconds
5. All posts saved to Airtable with quality scores

---

## How It Works

### Sequential Execution (Safe & Stable)

- **One post at a time** - No concurrent execution to avoid rate limiting
- **Circuit breaker protection** - Prevents cascade failures in long batches
- **Independent posts** - Each uses YOUR strategic outline (no "learning" pollution)
- **Clear progress** - Slack updates after every post: "Post 3/10 complete (Score: 21/25)"

### Strategic Context (From Your Outline)

- Each post receives **YOUR strategic outline** from the conversation
- No AI-generated "learnings" accumulated between posts
- Consistent with **YOUR thinking**, not iterative improvements
- Templates from `/templates` folder automatically matched and applied

### Optional Strategy Memory

- Ask agent to **"remember past discussions about [topic]"**
- Agent scans last 5 conversations, compacts to 1000 tokens max
- Only added if you **explicitly request it** (prevents context bloat)
- Same compacted context shared across all posts in batch for consistency

---

## Example Workflows

### Workflow 1: Generate Week of Content from Strategy Session

```
User: "We just finished the sovereign AI research. Create 7 posts across my active platforms."
```

**What happens:**
1. Agent reads `cloud.md` → Sees you post on LinkedIn (Mon/Wed/Fri), Twitter (Daily)
2. Creates strategic outlines for each post based on your conversation
3. Generates:
   - **Monday**: LinkedIn post #1
   - **Tuesday**: Twitter thread
   - **Wednesday**: LinkedIn post #2
   - **Thursday**: Twitter thread
   - **Friday**: LinkedIn post #3
   - **Saturday**: Twitter thread
   - **Sunday**: Twitter thread
4. **Total time**: ~10.5 minutes (7 posts × 90 sec)

---

### Workflow 2: Repurpose Content for Active Platforms

```
User: "Take this LinkedIn post and repurpose for my other active platforms"
```

**What happens:**
1. Agent reads `cloud.md` → Sees Twitter, Email active
2. Creates adapted outlines:
   - **Twitter**: Convert to thread format (280 chars × 5 tweets)
   - **Email**: Convert to newsletter format (subject + body)
3. Generates sequentially
4. **Total time**: ~3 minutes (2 posts)

---

### Workflow 3: 100-Post Campaign (Extreme Example)

```
User: "Product launch next week. Create 100 posts across all platforms."
```

**What happens:**
1. Agent verifies strategic outline covers all topics
2. Reads `cloud.md` for platform distribution
3. Generates 100 posts **sequentially**:
   - Progress updates every 10 posts
   - Circuit breaker prevents cascade failures
   - Retry logic (max 2×) handles API issues
4. **Total time**: ~150 minutes (2.5 hours)
5. **Expected success**: 95-98/100 posts (2-5 may fail despite retries)

**Slack Updates During 100-Post Batch:**
- **Every post**: "Post 47/100 complete (Score: 22/25) - [View in Airtable]"
- **Every 10 posts**: "Checkpoint: 50/100 complete (Avg score: 21.8/25)"
- **Final**: "🎉 Batch complete! 98/100 posts created in 2.5 hours - [View all]"

---

## Platform Configuration (cloud.md)

Your active platforms and posting schedule should be in `cloud.md`:

```yaml
platforms:
  linkedin:
    active: true
    schedule: ["Monday", "Wednesday", "Friday"]
    style: "thought_leadership"

  twitter:
    active: true
    schedule: ["Daily"]
    style: "tactical"

  email:
    active: true
    schedule: ["Tuesday"]
    type: "Email_Value"

  youtube:
    active: false

  instagram:
    active: false
```

**Agent reads this to:**
- Know which platforms you post on
- Suggest appropriate posting schedule
- Apply platform-specific styles
- When you say "repurpose for all platforms", use **only your active platforms**

---

## Quality & Safety

### Circuit Breaker Protection

- **Tracks failures** per batch
- After **3 consecutive failures** → pauses 60 seconds
- Prevents cascade failures in 100-post batches
- Automatically resets after successful post

### Retry Logic

- Failed posts **auto-retry** (max 2×)
- Exponential backoff (5s, then 10s)
- Most API issues resolved automatically
- Manual retry available for persistent failures

### Airtable Status Automation

- **Score <18** → Status: "Needs Review"
- **Score ≥18** → Status: "Draft"
- **GPTZero flagged** → Included in "Suggested Edits" field with specific sentences

### Rate Limiting (Conservative)

- **Sequential execution** = ~40 requests/minute max
- **Tier 2 limit**: 4,000 requests/minute
- **Safety margin**: 100× under limit
- **No parallel execution** until rate limiting proven stable

---

## Performance Expectations

| Batch Size | Time (Sequential) | Success Rate | Slack Updates |
|------------|-------------------|--------------|---------------|
| **5 posts** | ~7.5 min | 100% | Every post |
| **10 posts** | ~15 min | 99%+ | Every post + checkpoint at 10 |
| **25 posts** | ~37.5 min | 98%+ | Every post + checkpoints at 10, 20 |
| **50 posts** | ~75 min | 97%+ | Every post + checkpoints every 10 |
| **100 posts** | ~150 min (2.5 hrs) | 95%+ | Every post + checkpoints every 10 |

**Why sequential?**
- Extremely safe (1% of rate limit used)
- Predictable timing (90 sec/post)
- High reliability (95%+ success even at 100 posts)
- No rate limit fears during testing

---

## Troubleshooting

### "Batch taking longer than expected"

**Normal behavior:**
- 90 seconds/post is average
- Some posts take 120-150 sec if complex outline
- Check Slack for per-post progress
- YouTube/long-form content may take 180 sec

**Solution**: Wait for completion, monitor Slack updates.

---

### "Post failed after 2 retries"

**Possible causes:**
- Circuit breaker may be in OPEN state
- API rate limit hit (rare with sequential)
- Invalid strategic outline or context

**Solutions:**
1. Check circuit breaker status in error message
2. Review error message in Slack
3. Retry failed posts individually after batch completes
4. Verify strategic outline has all required details

---

### "Quality scores lower than expected"

**Possible causes:**
- Strategic outlines not detailed enough
- Missing proof points/specific examples
- Template structure not followed

**Solutions:**
1. Review strategic outlines - add more details
2. Check Editor-in-Chief validation in Airtable "Suggested Edits"
3. GPTZero may flag specific sentences for rewriting
4. Search company documents for proof points before batch

---

### "Circuit breaker opened - posts paused"

**What this means:**
- 3 consecutive failures detected
- System paused for 60 seconds to prevent cascade
- Will auto-resume after cooldown

**Solutions:**
- Wait 60 seconds for automatic recovery
- Check error messages to identify root cause
- If persistent, retry batch after fixing issue

---

## Advanced: Remembering Past Strategy

```
User: "Create 5 posts about sovereign AI, and remember our past discussions about self-hosting"
```

**What happens:**
1. Agent calls `get_strategy_context` tool
2. Scans last 5 separate conversations for "sovereign AI" + "self-hosting"
3. Compacts to **1000 tokens max** using Haiku
4. Includes in batch plan
5. Each of 5 posts receives same compacted memory (consistent context)

**When to use:**
- Continuity with past discussions matters
- You've had extensive research sessions before
- Want to maintain consistent themes across batches

**When NOT to use:**
- First time discussing topic
- Strategic outline already comprehensive
- Trying to avoid context bloat

**This is OPTIONAL** - only use when continuity with past discussions matters.

---

## Best Practices

### 1. Write Detailed Strategic Outlines

**Good outline:**
```
Post 1: LinkedIn - "I've self-hosted AI 3 times. Here's what nobody tells you."

Detailed outline:
- Hook: Personal experience (3 deployments: Ollama, DeepSeek, Chinese multi-layer)
- Problem: Everyone says "own your AI stack" but nobody talks about reality
- Core insights:
  * Consumer hardware bottleneck (no GPU = slow inference)
  * Latency vs sovereignty tradeoff
  * Production needs favor API, experimentation favors local
- Proof: Specific performance data from 3 deployments
- Conclusion: Sovereign AI isn't binary - it's a spectrum
```

**Bad outline:**
```
Post 1: Write about AI self-hosting
```

**Why it matters**: Detailed outlines give SDK agent clear direction, resulting in higher quality (22+/25) vs vague outlines (16-18/25).

---

### 2. Check cloud.md Before "Repurpose for All"

**Before**: `User: "Repurpose this for all platforms"`

**Verify**: Your `cloud.md` has correct active platforms

**Why**: Agent will create posts for ALL active platforms. If YouTube is accidentally marked active, you'll get video scripts you don't need.

---

### 3. Use Templates for Consistent Quality

Templates automatically matched from `/templates` folder:
- **Ship 30 tactics**: `long_form_expansion.json`, `outline_as_content.json`, `x_vs_y_comparison.json`
- **LinkedIn**: `framework_post.json`, `lead_magnet_post.json`
- **Twitter**: `hot_take.json`
- **Email**: `value_email.json`
- **Frameworks**: `dickie_listicle_formula.json`, `cole_hook_patterns.json`

Agent auto-matches templates based on:
- Platform + Style + Topic keywords
- Applies template structure, quality criteria, forbidden patterns

**Result**: More consistent formatting, proven structures applied automatically.

---

### 4. Monitor First 10 Posts Before Scaling to 100

**Start small:**
1. Create 10-post batch first
2. Review quality scores, Airtable records
3. Verify strategic outlines producing expected output
4. Adjust outlines based on results

**Then scale:**
- Once 10 posts averaging 20+/25, safe to scale to 100
- Quality patterns established, less manual review needed

---

### 5. Use Strategy Memory Sparingly

**Good use case:**
```
User: "Create 10 posts about sovereign AI, remember our 3-hour research session yesterday"
```

**Bad use case:**
```
User: "Create 10 posts about random topics, remember everything we've ever discussed"
```

**Why**:
- Good: Maintains consistency in specific topic area
- Bad: Irrelevant context bloats prompt, reduces quality

**Rule of thumb**: Only use strategy memory when past discussions directly inform current batch.

---

## Technical Details

### Sequential Execution Architecture

```
Batch Plan Created:
{
  'id': 'batch_20250130_143022',
  'posts': [
    {platform: 'linkedin', topic: '...', detailed_outline: '...' },
    {platform: 'twitter', topic: '...', detailed_outline: '...' },
    ... (10 total)
  ],
  'strategy_memory': compacted_context (if requested),
  'user_platforms': ['linkedin', 'twitter', 'email']  # from cloud.md
}

Execution Flow:
Post 1 → SDK Agent → Airtable/Supabase → Slack update (90 sec)
Post 2 → SDK Agent → Airtable/Supabase → Slack update (90 sec)
...
Post 10 → SDK Agent → Airtable/Supabase → Final summary

Total: 15 minutes for 10 posts
```

### Production Hardening (v4.2.0)

All SDK agents include:
- **Circuit breaker**: Failure threshold (3), recovery timeout (60s)
- **Structured logging**: Operation timing, error context, quality scores
- **Retry logic**: Max 2 retries with exponential backoff
- **Graceful degradation**: Works without GPTZero API key (Editor-in-Chief only)
- **Type safety**: Handles dict and string issue formats
- **Pattern detection**: Catches "The X:" headers, short questions, AI tells

### Validation Pipeline

Each post automatically runs:
1. **Editor-in-Chief rules** (5-axis quality rubric)
2. **GPTZero AI detection** (optional, if API key present)
3. **Issue normalization** (converts to structured dict format)
4. **Airtable status automation** (<18 = "Needs Review", ≥18 = "Draft")

Results saved to:
- **Airtable**: "Suggested Edits" field with GPTZero flagged sentences
- **Supabase**: `generated_posts` table with embeddings for search

---

## Batch Processing vs Single Posts

| Feature | Single Post | Batch (10 posts) |
|---------|------------|------------------|
| **Time** | 90 sec | 15 min |
| **Context setup** | Once | Once (shared across all) |
| **Strategic outline** | Required | Required for each |
| **Quality validation** | Per post | Per post |
| **Airtable saves** | 1 | 10 |
| **Slack updates** | Final only | Every post + final |
| **Progress visibility** | Low | High |
| **Failure isolation** | N/A | Yes (post 5 fails, post 6-10 continue) |

**When to use batch:**
- 5+ posts with similar strategic context
- Multi-platform campaigns
- Week/month content planning

**When to use single:**
- One-off post creation
- Testing strategic outline quality
- Urgent content needs

---

## FAQ

### Q: Can I cancel a batch mid-execution?

**A:** Yes, but gracefully:
1. In-progress post will complete (don't interrupt SDK agent)
2. Pending posts will be cancelled
3. Completed posts remain in Airtable

Use `cancel_batch(plan_id)` tool (not yet documented - coming soon).

---

### Q: What happens if my strategic outline is incomplete?

**A:** SDK agent will:
1. Generate with available context
2. Quality score likely lower (15-17/25)
3. Airtable status: "Needs Review"
4. Editor-in-Chief flags missing proof points

**Solution**: Review Airtable "Suggested Edits", add missing details, regenerate.

---

### Q: Can I run multiple batches simultaneously?

**A:** Not recommended:
- Sequential execution already conservative on rate limits
- Multiple batches = multiple sequential streams
- Risk of context confusion between batches
- Better: Combine into single larger batch

---

### Q: How does template matching work?

**A:** Automatic semantic search:
1. Agent builds search query: `"{platform} {style} {topic}"`
2. Searches `/templates` folder using cosine similarity
3. Returns top 1 match if similarity >0.7
4. Injects template structure into post context

Example: `"linkedin thought_leadership sovereign AI"` → matches `framework_post.json`

---

### Q: What if GPTZero API is down?

**A:** Graceful degradation:
- Validation continues with Editor-in-Chief only
- GPTZero fields (`ai_pct`, `flagged_sentences`) set to `null`
- Posts still created, just less AI detection data
- Airtable "Suggested Edits" shows Editor-in-Chief results only

**No batch failure** - system designed to work without GPTZero.

---

## Getting Help

### Documentation
- **This guide**: Batch processing workflows
- **[CLONING_PLAN.md](CLONING_PLAN.md)**: Platform SDK agent architecture
- **[ANALYTICS_PLAN.md](../ANALYTICS_PLAN.md)**: Future analytics integration

### Support
- Check Slack for real-time progress updates
- Review Airtable "Suggested Edits" for quality issues
- Examine Supabase `generated_posts` table for debugging

### Reporting Issues
- Include batch `plan_id` from error message
- Share strategic outline that caused issue
- Note which post number failed (e.g., "Post 47/100")
- Provide Slack error message screenshot

---

## Roadmap

### Current (v4.2.0 - Batch Sequential)
✅ Sequential execution (safe, stable)
✅ Circuit breaker + retry logic
✅ Strategy memory tool (optional)
✅ Template auto-matching
✅ cloud.md platform configuration

### Coming Soon
🔜 Parallel execution (3 concurrent) - after rate limiting proven
🔜 Analytics integration (performance trends inform batch plans)
🔜 Campaign templates (launch week, product announcement, etc.)
🔜 Batch cancellation UI

### Future
🔮 Dynamic platform distribution (AI suggests optimal platform mix)
🔮 Quality prediction (estimate scores before generation)
🔮 Cross-batch learning (Month 2 learns from Month 1 performance)

---

**Ready to get started?** Try a 5-post batch first, then scale to 10, 25, 50, or 100 as confidence grows.

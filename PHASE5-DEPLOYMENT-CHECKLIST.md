# Phase 5 Deployment Checklist

## Summary
Phase 5 adds batch orchestration tools to the CMO agent for sequential execution of 5-50 posts with learning accumulation.

**Status:** ✅ Code Complete - Ready for Deployment Testing

---

## What Changed

### New Files
1. **agents/context_manager.py** (~200 lines)
   - Manages context accumulation across N-post batch
   - Compacts every 10 posts (20k tokens → 2k tokens)
   - Tracks quality progression over batch

2. **agents/batch_orchestrator.py** (~520 lines)
   - Sequential execution logic
   - Helper functions for CMO tools
   - Global registries for plans and context managers

### Modified Files
1. **slack_bot/claude_agent_handler.py**
   - Added 4 new tools: `plan_content_batch`, `execute_post_from_plan`, `compact_learnings`, `checkpoint_with_user`
   - Updated system prompt with batch orchestration workflow instructions
   - Increased tool count from 23 → 27

2. **main_slack.py** (Phase 0.5)
   - Added FastAPI BackgroundTasks for proper async handling
   - Prevents Slack 3-second timeout issues

---

## Pre-Deployment Validation

### ✅ Syntax Checks
```bash
python3 -m py_compile slack_bot/claude_agent_handler.py
python3 -m py_compile agents/batch_orchestrator.py
python3 -m py_compile agents/context_manager.py
```
**Result:** All files compile successfully ✅

### ✅ Git Status
```bash
git log --oneline -3
```
**Commits:**
- `8f76c8a` Phase 5: Add batch orchestration tools to CMO agent
- `f66a99c` Phase 5: Create core batch execution infrastructure
- `cbeecde` Phase 0.5: Add FastAPI BackgroundTasks for proper lifecycle management

**Branch:** `feature/bulk-content-generation`
**Pushed to remote:** ✅ Yes

---

## Deployment Steps

### 1. Verify Environment Variables
Ensure these are set in production:
- `ANTHROPIC_API_KEY` (for context compaction)
- `SUPABASE_URL`, `SUPABASE_KEY` (for post storage)
- `AIRTABLE_ACCESS_TOKEN`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`
- `SLACK_BOT_TOKEN` (for progress updates)

**Command:**
```bash
python tests/pre_deploy_test.py
```

### 2. Deploy to Replit
1. Pull latest from `feature/bulk-content-generation` branch
2. Restart Replit server
3. Check logs for initialization message:
   ```
   🚀 Claude Agent SDK initialized with 27 tools (8 general + 4 batch + 15 co-writing tools for 5 platforms)
   ```

### 3. Test Small Batch (5 Posts)
Send this message in Slack:
```
Create 5 LinkedIn posts about AI agents, productivity, remote work, cybersecurity, and cloud computing
```

**Expected Behavior:**
1. CMO should call `plan_content_batch` and show plan ID
2. CMO should call `execute_post_from_plan` 5 times (once per post)
3. Each post shows quality score and Airtable link
4. No checkpoint (only triggered at 10+ posts)

**Success Criteria:**
- ✅ 5 separate Airtable records created (not 1 merged record)
- ✅ Quality scores visible for each post
- ✅ Each post URL accessible in Airtable
- ✅ No timeout or hanging "On it..." messages

### 4. Test Medium Batch (15 Posts)
Send this message:
```
Create 15 LinkedIn posts: 5 about AI, 5 about productivity, 5 about remote work
```

**Expected Behavior:**
1. Plan created for 15 posts
2. Posts 1-10: Execute sequentially
3. Post 10: Checkpoint message with stats
4. Post 10: Automatic compaction (learnings compressed)
5. Posts 11-15: Execute with compacted learnings

**Success Criteria:**
- ✅ Checkpoint message appears at post 10
- ✅ Average quality score visible in checkpoint
- ✅ Quality trend shows "improving" or "stable"
- ✅ All 15 posts created successfully

### 5. Monitor Performance
Check these metrics:
- **Time per post:** ~90 seconds (target)
- **Memory usage:** Should stay < 4GB (8GB available)
- **Context size:** ~25k tokens for 50 posts (vs 200k without compaction)
- **API errors:** Should be 0

---

## Rollback Plan

If batch orchestration causes issues, rollback is simple (no breaking changes):

### Quick Rollback
1. Remove 4 batch tools from `claude_agent_handler.py`:
   - Comment out lines 785-1063 (4 tool definitions)
   - Comment out lines 1426-1429 (tool registrations)
   - Comment out lines 1322-1367 (batch workflow instructions in system prompt)

2. Restart server

**Result:** Agent reverts to 23 tools (pre-Phase 5 state)

### Full Rollback
```bash
git checkout main
# Or revert specific commits
git revert 8f76c8a f66a99c
```

---

## Known Limitations

### Current Implementation
- **Sequential only:** Posts execute one at a time (~90s each)
- **In-memory plans:** Plans stored in global dict (cleared on restart)
- **No persistence:** If server restarts mid-batch, must start over

### Planned Enhancements (Future)
- Persist plans to Supabase for crash recovery
- Add timeout handling (per-post 3-minute limit)
- Add "resume batch" capability after server restart

---

## Dependencies Required

These dependencies must be installed (from `requirements.txt`):

```
anthropic>=0.43.0         # For context compaction
fastapi>=0.115.12        # For BackgroundTasks
slack-sdk>=3.34.0        # For progress updates
```

**Verify:**
```bash
pip list | grep -E "anthropic|fastapi|slack-sdk"
```

---

## Testing Checklist

### Unit Tests (Local)
- ✅ Python syntax validation
- ⏸️  Context manager logic tests (blocked by import issues)
- ⏸️  Batch orchestrator tests (blocked by import issues)

**Note:** Unit tests blocked by missing `claude_agent_sdk` dependency in test environment. This is expected - dependencies only installed in production.

### Integration Tests (Production)
- [ ] 5-post batch (LinkedIn only)
- [ ] 15-post batch (mixed platforms)
- [ ] 30-post batch (full month)
- [ ] Error handling (invalid platform, failed post)
- [ ] Checkpoint messages (every 10 posts)
- [ ] Context compaction (post 10, 20, 30, etc.)

---

## Success Metrics

### Quality Improvement
- **Target:** Average score increases by 2-3 points over 50-post batch
- **Example:** Post 1 score 20 → Post 50 score 23

### Context Efficiency
- **Target:** 25k tokens for 50 posts (vs 200k without compaction)
- **Reduction:** 87% context savings

### Reliability
- **Target:** 95%+ success rate (0-2 failures in 50 posts)
- **Error recovery:** Failed posts don't block remaining batch

### User Experience
- **Target:** Clear progress visibility (user sees each post complete)
- **Checkpoints:** Every 10 posts with stats update
- **Time estimation:** Accurate remaining time calculation

---

## Next Steps (After Phase 5 Validated)

### Optional Enhancements
1. **Phase 6:** Error recovery & resilience
   - Per-post timeout (3 min)
   - Retry failed posts
   - Resume batch after server restart

2. **Phase 1:** Slack progress improvements
   - Bot message filtering (reduce noise in CMO context)
   - Real-time progress bar in Slack

3. **Phase 4:** Contextual post count tracking
   - "Post 3 of 7" awareness
   - Handle user revisions mid-batch

---

## Contact

**Issue Reporting:**
- GitHub Issues: https://github.com/heymitch/ai-content-agent-beta/issues
- Branch: `feature/bulk-content-generation`

**Documentation:**
- Full plan: `/BULK-PLAN.md`
- Architecture: Anthropic context engineering best practices
- Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

---

**Last Updated:** 2025-01-24
**Phase:** 5 (Batch Orchestration Tools)
**Status:** ✅ Ready for Deployment Testing

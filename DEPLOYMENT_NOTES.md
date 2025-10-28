# Deployment Notes - Co-write Tools Lazy Loading

## Date: October 27, 2025

## Changes Made

### 1. **Co-write Tools Separation**
   - Moved all 15 co-write tools from `slack_bot/claude_agent_handler.py` to new `slack_bot/cowrite_tools.py`
   - Removed 387 lines of co-write tool definitions from main handler
   - Tools moved:
     - `generate_post_*` (5 tools)
     - `quality_check_*` (5 tools)
     - `apply_fixes_*` (5 tools)

### 2. **Lazy Loading Implementation**
   - Co-write tools are now only loaded when user explicitly requests collaboration
   - Default mode is BATCH (99% of requests)
   - Co-write mode triggers only on specific keywords:
     - "co-write" / "cowrite"
     - "collaborate with me"
     - "iterate with me" / "iterate with you"
     - "work with me on this"
     - "let's collaborate" / "let's iterate"

### 3. **Dynamic Tool Loading**
   - Added `_detect_cowrite_mode()` method to detect collaboration requests
   - MCP server initially loads only base tools (14 tools)
   - Co-write tools loaded dynamically when needed (+15 tools)
   - Sessions cleared when switching modes to ensure proper tool registration

### 4. **Test Coverage**
   - Added comprehensive agent routing test to `tests/test_agent_routing.py`
   - Added routing test to pre-deployment suite (`tests/pre_deploy_test.py`)
   - Tests verify:
     - Batch mode is default for normal content requests
     - Co-write mode only triggers on explicit keywords
     - System prompt emphasizes batch mode (99% rule)

## Rationale

The agent was bypassing batch orchestration and using old co-write tools even when users provided complete strategic content. This caused the agent to rewrite user's carefully crafted posts into generic AI output.

By separating co-write tools and making them opt-in only, we ensure:
1. Batch mode is truly the default
2. User's strategic content is preserved
3. Agent uses `plan_content_batch` → `execute_post_from_plan` workflow
4. Co-write tools only load when explicitly requested

## Testing

Run pre-deployment tests before deploying:
```bash
python3 tests/pre_deploy_test.py
```

The agent routing test (Test 13) should show:
- ✅ Batch mode messages correctly use batch mode
- ✅ Co-write keywords correctly trigger co-write
- ✅ System prompt emphasizes batch as default

## Files Changed

- `slack_bot/claude_agent_handler.py` - Removed co-write tools, added lazy loading
- `slack_bot/cowrite_tools.py` - NEW file with all 15 co-write tools
- `tests/pre_deploy_test.py` - Added agent routing test
- `scripts/remove_cowrite_tools.py` - Utility script used for separation

## Deployment Steps

1. Commit changes:
```bash
git add .
git commit -m "Implement co-write tools lazy loading to enforce batch mode as default"
```

2. Push to repository:
```bash
git push origin main
```

3. Deploy to Replit and test with sample messages:
   - "Create 5 LinkedIn posts" → Should use batch mode
   - "Co-write a post with me" → Should load co-write tools

## Notes

- Co-write mode is stateful per handler instance
- Once co-write tools are loaded, they remain for that handler's lifetime
- Consider adding ability to switch back to batch-only mode if needed
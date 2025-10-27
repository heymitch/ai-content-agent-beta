# Bulk Content Generation - Future Improvements Plan

## Overview
This document tracks planned improvements for the bulk content generation system that are not yet implemented.

---

## 1. Optional Fact-Check Tool for SDK Agents

**Status:** 📝 Planned
**Estimated Time:** 1.5-2 hours
**Priority:** Medium
**Dependencies:** Quality check tool must be working (✅ Fixed in commit a76910b)

### Problem Statement
Currently, the `quality_check` tool skips fact verification entirely to avoid tool_use/tool_result conflicts. Claims are marked as "NEEDS VERIFICATION" but never actually verified.

### Proposed Solution
Create a standalone `fact_check_claims` tool that SDK agents can optionally call to verify specific claims without causing tool conflicts.

### Architecture Design

#### New Standalone Tool
```python
@tool(
    "fact_check_claims",
    "Verify specific claims using web search (OPTIONAL - call after quality_check if needed)",
    {
        "claims": list,  # [{"claim": str, "type": str}]
        "search_depth": str  # "quick" or "thorough"
    }
)
async def fact_check_claims(args):
    # Uses Tavily API directly (no nested tool contexts)
    # Returns structured verification results
    # Gracefully handles API failures
```

#### Integration Points
- Add to all 5 SDK agents as 7th tool in MCP server
- Update SDK agent workflow prompts to make it optional
- Modify apply_fixes to use fact_check results

#### When to Call
- Post mentions specific people/companies
- Post cites statistics or percentages
- Post references news events or dates
- Skip for: opinions, frameworks, content from provided context

### Implementation Steps

1. **Create Shared Tool (30 min)**
   - New file: `agents/shared_tools.py`
   - Implement fact_check_claims with Tavily
   - Structured input/output with error handling

2. **Update SDK Agents (20 min)**
   - Import and register in all 5 agents
   - Add to MCP server as 7th tool

3. **Update Prompts (20 min)**
   - Modify workflow to include optional fact_check
   - Add decision logic for when to call

4. **Update apply_fixes (15 min)**
   - Accept optional fact_check results
   - Integrate verification into fixes

5. **Testing (15 min)**
   - Verify no tool conflicts
   - Test optional calling logic
   - Check Airtable output

### Expected Output
```json
{
  "verified_claims": [
    {
      "claim": "OpenAI raised $6.6B in October 2024",
      "status": "verified",
      "source": "Reuters, Oct 2 2024"
    }
  ],
  "unverified_claims": [
    {
      "claim": "Sarah Chen, CMO at TechCorp",
      "status": "no_results",
      "note": "No public records found"
    }
  ],
  "searches_performed": 2,
  "summary": "1 of 2 claims verified"
}
```

### Benefits
- Resolves current verification gap
- Optional & flexible based on content type
- No tool_use/tool_result conflicts
- Better UX with clear verification status
- Single shared tool vs duplicated code

### Risk Mitigation
- Tavily API limits: Graceful fallback to "unverified"
- Performance: Only called when needed
- Complexity: Simple verify-and-return design
- Conflicts: Clean separation from quality_check

---

## 2. [Placeholder for Next Improvement]

**Status:** 📝 Planned
**Estimated Time:** TBD
**Priority:** TBD
**Dependencies:** TBD

### Problem Statement
[To be added]

### Proposed Solution
[To be added]

---

## Implementation Order

Based on dependencies and priority:

1. ✅ Fix quality_check tool conflicts (COMPLETED - commit a76910b)
2. 📝 Optional fact_check_claims tool (1.5-2 hours)
3. 📝 [Other improvements to be added]

---

## Notes

- This plan is for future improvements that are not immediately critical
- Each improvement should be implemented and tested independently
- Consider bundling related improvements into single PR when possible
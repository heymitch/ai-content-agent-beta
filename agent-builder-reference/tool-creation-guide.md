# Tool Creation Guide for Claude Agent SDK

## Overview
This guide covers how to add new tools to your Claude Agent SDK implementation.

---

## Table of Contents
1. [Tool Structure Basics](#tool-structure-basics)
2. [Tool Schema Patterns](#tool-schema-patterns)
3. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
4. [Testing Your Tools](#testing-your-tools)

---

## 1. Tool Structure Basics

### Minimum Viable Tool
```python
from claude_agent_sdk import tool

@tool(
    "tool_name",
    "Clear description of what this tool does",
    {"param1": str, "param2": int}
)
async def tool_name(args):
    """Docstring for the tool"""
    param1 = args.get('param1', '')
    param2 = args.get('param2', 0)

    # Your logic here
    result = "your result"

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }
```

### Tool Components
- **Name**: Snake_case identifier
- **Description**: What the agent sees - be specific about when to use it
- **Schema**: Parameter definitions (simple dict or JSON Schema)
- **Handler**: Async function that processes the tool call

---

## 2. Tool Schema Patterns

### Simple Schema (Required Parameters Only)
```python
{"query": str, "count": int}
```

### JSON Schema (With Optional Parameters)
```python
{
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "platform": {"type": ["string", "null"], "description": "Optional platform filter"},
        "count": {"type": "integer", "default": 5}
    },
    "required": ["query"]  # Only query is required
}
```

**Key Lesson**: If you want optional parameters, use JSON Schema format with a `"required"` array.

---

## 3. Common Pitfalls & Solutions

### Issue #1: String "None" vs Actual None
**Problem**: Agent passes string `"None"` instead of null/None
```python
# Broken - platform filter searches for literal "None"
platform = args.get('platform')  # Gets "None" string
```

**Solution**: Convert string representations to actual None
```python
platform = args.get('platform')
if platform in ("None", "null", ""):
    platform = None
```

**Reference**: Fixed in branch `fix/direct-api-linkedin-agent` (commit a8c9efe)

### Issue #2: Tool Schema Forces Required Parameters
**Problem**: Simple schema makes all params required
```python
# WRONG - Agent must provide platform even if not needed
{"query": str, "platform": str}
```

**Solution**: Use JSON Schema with explicit required array
```python
# RIGHT - Only query required
{
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "platform": {"type": ["string", "null"]}
    },
    "required": ["query"]
}
```

**Reference**: Fixed in branch `fix/direct-api-linkedin-agent` (commit 0e6e69a)

### Issue #3: Tool Description Biases Agent Behavior
**Problem**: Description says "search high-performing examples" → agent adds "high performing" to every query

**Solution**: Be explicit about NOT modifying user input
```python
# WRONG
"Search proven content examples for best practices"

# RIGHT
"Search content examples using semantic search. Use the user's exact query words without adding qualifiers."
```

**Reference**: Fixed in branch `fix/direct-api-linkedin-agent` (commit 0e6e69a)

### Issue #4: Async I/O Blocking Event Loop
**Problem**: Synchronous operations (database calls, API requests) block the async event loop

**Solution**: Use `run_in_executor` for blocking operations
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,
    lambda: blocking_function(param1, param2)
)
```

---

## 4. Testing Your Tools

### Test Checklist
- [ ] Tool appears in agent's tool list
- [ ] Required parameters work
- [ ] Optional parameters default correctly
- [ ] String "None" converts to actual None
- [ ] Returns expected result format
- [ ] Async execution doesn't block
- [ ] Error handling works

### Quick Test Script
```python
# Test the tool function directly
from your_module import your_tool_function

result = your_tool_function(
    query="test",
    platform=None,  # Test with None
    match_count=5
)

print(result)
```
# Agent Setup Guide for Claude Agent SDK

## Overview
This guide covers setting up Claude Agent SDK agents with proper tool integration, system prompts, and common configuration patterns.

---

## Table of Contents
1. [Basic Agent Structure](#basic-agent-structure)
2. [System Prompt Design](#system-prompt-design)
3. [Tool Registration Patterns](#tool-registration-patterns)
4. [Common Configuration Issues](#common-configuration-issues)
5. [Session Management](#session-management)

---

## 1. Basic Agent Structure

### Minimum Agent Setup
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

# 1. Define tools
@tool("my_tool", "Description", {"param": str})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "result"}]}

# 2. Create MCP server with tools
mcp_server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0",
    tools=[my_tool]
)

# 3. Configure agent options
options = ClaudeAgentOptions(
    mcp_servers={"tools": mcp_server},
    allowed_tools=["mcp__tools__*"],
    system_prompt="Your agent's instructions",
    model="claude-sonnet-4-5-20250929",
    continue_conversation=True
)

# 4. Create and use client
client = ClaudeSDKClient(options=options)
await client.connect()
await client.query("User message")
```

### Key Components
- **MCP Server**: Container for your tools
- **Agent Options**: Configuration for Claude model
- **System Prompt**: Agent's behavior instructions
- **Session Management**: Conversation continuity

---

## 2. System Prompt Design

### Structure Pattern
```
**YOUR IDENTITY:**
- Who the agent is
- What domain they operate in

**YOUR CAPABILITIES:**
1. tool_name_1 - When to use it
2. tool_name_2 - When to use it

**WORKFLOW:**
1. Step-by-step process
2. Decision tree for different scenarios

**CRITICAL RULES:**
- Hard constraints
- Error patterns to avoid
```

### Common Mistakes

#### Mistake #1: Tool Not Listed in Capabilities
**Problem**: Agent doesn't know tool exists
```python
# System prompt lists:
# 1. search_knowledge_base
# 2. search_company_documents
# Missing: search_content_examples ← Tool exists but agent won't use it
```

**Solution**: Always list ALL tools in capabilities section
```python
**YOUR CAPABILITIES:**
1. web_search - For current events
2. search_knowledge_base - Internal docs
3. search_company_documents - User uploads
4. search_content_examples - Example content (use user's EXACT query)
```

**Reference**: Fixed in `fix/direct-api-linkedin-agent` (commit 0e6e69a)

#### Mistake #2: Ambiguous Tool Descriptions
**Problem**: Agent chooses wrong tool or modifies queries

**Solution**: Be explicit about behavior
```python
# WRONG
"Search content examples for inspiration"
→ Agent thinks it should only search when user wants "inspiration"

# RIGHT
"Semantic search across 700+ content examples. Use user's EXACT query words without adding qualifiers."
→ Agent passes query verbatim
```

#### Mistake #3: Conflicting Instructions
**Problem**: System prompt says one thing, tool description says another

**Solution**: Keep them aligned
```python
# System prompt: "Leave platform=None to search all platforms"
# Tool schema: {"platform": str}  ← CONFLICT: Required parameter
# Fix: Use JSON Schema with "required": ["query"] only
```

---

## 3. Tool Registration Patterns

### Pattern 1: Static Tool Set
```python
# All tools loaded at startup
tools = [tool1, tool2, tool3]
mcp_server = create_sdk_mcp_server(name="tools", version="1.0.0", tools=tools)
```

### Pattern 2: Lazy Loading (Conditional Tools)
```python
# Load tools only when needed
base_tools = [tool1, tool2]

if user_requests_cowrite_mode:
    from module import cowrite_tools
    all_tools = base_tools + cowrite_tools
    # Recreate MCP server with new tool list
    mcp_server = create_sdk_mcp_server(name="tools", version="1.0.0", tools=all_tools)
```

**Reference**: Implemented in `slack_bot/claude_agent_handler.py` (_detect_cowrite_mode)

### Pattern 3: Dynamic Tool Registration
```python
# Register tools from multiple modules
from module1 import tools as module1_tools
from module2 import tools as module2_tools

all_tools = module1_tools + module2_tools
```

---

## 4. Common Configuration Issues

### Issue #1: Session Invalidation
**Problem**: Prompt changes don't reflect in active sessions

**Solution**: Invalidate sessions when prompt changes
```python
# Track prompt version
self.prompt_version = hashlib.md5(self.system_prompt.encode()).hexdigest()[:8]

# Store per-session version
self._session_prompt_versions[thread_ts] = self.prompt_version

# Invalidate if changed
if self._session_prompt_versions[thread_ts] != self.prompt_version:
    del self._thread_sessions[thread_ts]  # Force new session
```

**Reference**: Implemented in `slack_bot/claude_agent_handler.py` (_get_or_create_session)

### Issue #2: Tool Name Conflicts
**Problem**: Two tools with same name from different modules

**Solution**: Use unique, descriptive names
```python
# WRONG
@tool("search", ...)  # Too generic

# RIGHT
@tool("search_content_examples", ...)
@tool("search_company_documents", ...)
```

### Issue #3: MCP Server Not Found
**Problem**: Agent can't access tools

**Check**:
1. MCP server created before ClaudeSDKClient?
2. Server passed in `mcp_servers` dict?
3. `allowed_tools` pattern matches tool names?

```python
# Correct setup
mcp_server = create_sdk_mcp_server(...)  # 1. Create server
options = ClaudeAgentOptions(
    mcp_servers={"tools": mcp_server},  # 2. Pass server
    allowed_tools=["mcp__tools__*"]     # 3. Allow pattern
)
```

---

## 5. Session Management

### Session Lifecycle
```python
# 1. Get or create session (per thread/user)
client = await self._get_or_create_session(thread_ts)

# 2. Check if already connected
if thread_ts not in self._connected_sessions:
    await client.connect()
    self._connected_sessions.add(thread_ts)

# 3. Send query
await client.query(message)

# 4. Collect response
async for msg in client.receive_response():
    # Process messages
```

### Session Caching Strategy
- **Key by**: User ID, thread ID, or conversation context
- **Invalidate when**: Prompt changes, session expires, error occurs
- **Cleanup**: Remove old sessions periodically

```python
# Cleanup pattern
MAX_CONCURRENT_SESSIONS = 3
SESSION_TTL = 1800  # 30 minutes

if len(sessions) > MAX_CONCURRENT_SESSIONS:
    # Remove oldest
```

**Reference**: Implemented in `slack_bot/claude_agent_handler.py` (_cleanup_old_sessions)

---

## Testing Checklist

### Agent Startup
- [ ] Agent creates successfully
- [ ] All tools register correctly
- [ ] System prompt loads
- [ ] First query works

### Tool Execution
- [ ] Agent selects correct tool
- [ ] Parameters pass correctly
- [ ] Results return to agent
- [ ] Agent incorporates results in response

### Session Management
- [ ] Multiple conversations don't conflict
- [ ] Session caching works
- [ ] Invalidation triggers correctly
- [ ] Memory doesn't leak

---

## Next Steps
1. Read [Tool Creation Guide](./tool-creation-guide.md)
2. Review `slack_bot/claude_agent_handler.py` for real implementation
3. Test with simple tools before complex workflows

---

## Reference Implementations
- **Full agent handler**: `slack_bot/claude_agent_handler.py`
- **Tool definitions**: `slack_bot/claude_agent_handler.py` (@tool decorators)
- **System prompt**: `slack_bot/claude_agent_handler.py` (self.system_prompt)

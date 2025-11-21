# Prompt for Replit Agent: Add Chuck Norris Facts Tool

## Context
You are adding a new tool to the Claude Agent SDK implementation that fetches random Chuck Norris facts. This tool will be used by the content creation agent to generate posts based on Chuck Norris facts.

## Files to Modify
- `slack_bot/claude_agent_handler.py` - Add the tool here

## Reference Documents
- `agent-builder-reference/tool-creation-guide.md` - Follow the patterns in this guide

## API Information
- **API**: Chuck Norris Internet Database - https://api.chucknorris.io/
- **Endpoint**: `https://api.chucknorris.io/jokes/random`
- **Method**: GET
- **Authentication**: None required (free, no API key)
- **Response Format**: JSON with structure:
  ```json
  {
    "value": "Chuck Norris can divide by zero.",
    "url": "https://api.chucknorris.io/jokes/...",
    "categories": []
  }
  ```

## Requirements

### 1. Tool Definition
Add a new tool called `get_chuck_norris_fact` to `slack_bot/claude_agent_handler.py`

**Tool Description**: "Get a random Chuck Norris fact to use as inspiration for content creation. Returns a humorous Chuck Norris fact that can be used as a hook or theme for posts."

**Schema**: Simple - no parameters required (always returns random fact)

### 2. Tool Implementation
- Use `httpx.AsyncClient` for HTTP requests (already imported in the file)
- Follow the async pattern shown in other tools
- Return format must match the standard tool response structure:
  ```python
  {
      "content": [{
          "type": "text",
          "text": "Chuck Norris can divide by zero."
      }]
  }
  ```

### 3. Error Handling
- Handle API errors gracefully
- Return error message if API is unreachable
- Include timeout (10 seconds max)

### 4. Tool Registration
- Add the tool to `self.base_tools` list (around line 1636)
- Place it after the search tools, before batch orchestration tools
- Add to system prompt's capabilities list (around line 1217)

### 5. System Prompt Update
Add to the **YOUR CAPABILITIES** section:
```
10. get_chuck_norris_fact - Get random Chuck Norris fact for content inspiration
```

## Expected Behavior
After implementation:
1. User asks: "Get me a Chuck Norris fact"
2. Agent calls: `get_chuck_norris_fact()`
3. API returns: Random fact
4. Agent responds: "Chuck Norris doesn't do pushups. He pushes the Earth down."

Then user can say: "Create a LinkedIn post based on that Chuck Norris fact" and the agent will use the fact as inspiration.

## Testing Steps
1. Add the tool code
2. Restart the Slack bot
3. Test: "@agent get me a Chuck Norris fact"
4. Verify: Agent returns a Chuck Norris fact
5. Test: "@agent create a LinkedIn post based on that Chuck Norris fact"
6. Verify: Agent creates content using the fact as theme

## Code Placement Hints
- **Where to add the @tool decorator**: After `analyze_past_content` (line ~204), before `search_past_posts` (line ~210)
- **Where to add to base_tools**: In `__init__` method, around line 1648
- **Where to update system prompt**: Around line 1222 in the capabilities list

## Important Patterns to Follow (from tool-creation-guide.md)
1. Use `@tool` decorator with clear description
2. Make the function `async`
3. Use `httpx.AsyncClient()` within async context manager
4. Return dict with `{"content": [{"type": "text", "text": result}]}`
5. Add error handling with try/except
6. Keep timeout reasonable (10 seconds)

## Success Criteria
- [ ] Tool appears in agent's tool list
- [ ] Agent can call the tool successfully
- [ ] Returns random Chuck Norris fact
- [ ] Can be used as inspiration for content creation
- [ ] No errors in console/logs

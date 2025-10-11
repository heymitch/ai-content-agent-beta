"""
Plan Mode Handler using Claude Agent SDK with TodoWrite
Allows users to create structured plans that delegate to subagents
"""
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query
from claude_agent_sdk.tool import tool
import json
from typing import Dict, List, Any, Optional
import asyncio

# Import subagent orchestrators
from agents.agentic_linkedin_orchestrator import AgenticLinkedInOrchestrator
from agents.agentic_twitter_orchestrator import AgenticTwitterOrchestrator
from agents.agentic_email_orchestrator import AgenticEmailOrchestrator


@tool(
    name="create_execution_plan",
    description="Create a structured plan with todos that will be delegated to subagents",
    input_schema={
        "task_description": str,
        "todos": List[Dict[str, Any]]  # List of todo items with content, priority, agent_type
    }
)
async def create_execution_plan(args: dict[str, Any]) -> dict[str, Any]:
    """
    Create an execution plan that will be delegated to subagents

    Each todo should have:
    - content: What needs to be done
    - agent_type: Which subagent will handle it (linkedin, twitter, email, research)
    - priority: high/medium/low
    - dependencies: List of todo IDs this depends on
    """
    task_description = args.get('task_description', '')
    todos = args.get('todos', [])

    # Format the plan for display
    plan_text = f"📋 **Execution Plan:** {task_description}\n\n"

    for i, todo in enumerate(todos, 1):
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo.get('priority', 'medium'), "⚪")
        agent = todo.get('agent_type', 'general')
        content = todo.get('content', '')

        plan_text += f"{i}. {priority_emoji} [{agent}] {content}\n"

        if todo.get('dependencies'):
            plan_text += f"   └─ Depends on: {', '.join(map(str, todo['dependencies']))}\n"

    return {
        "content": [{
            "type": "text",
            "text": plan_text
        }],
        "metadata": {
            "todos": todos,
            "requires_approval": True
        }
    }


@tool(
    name="execute_plan_item",
    description="Execute a single item from the plan using the appropriate subagent",
    input_schema={
        "todo_id": int,
        "content": str,
        "agent_type": str,
        "context": Optional[Dict[str, Any]]
    }
)
async def execute_plan_item(args: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a single plan item by delegating to the appropriate subagent
    """
    todo_id = args.get('todo_id', 0)
    content = args.get('content', '')
    agent_type = args.get('agent_type', 'general')
    context = args.get('context', {})

    result_text = f"✅ Executing: {content}\n"

    try:
        if agent_type == 'linkedin':
            orchestrator = AgenticLinkedInOrchestrator()
            result = await orchestrator.create_content(
                topic=content,
                user_id=context.get('user_id', 'default')
            )
            result_text += f"LinkedIn post created with score: {result.get('score', 0)}/100"

        elif agent_type == 'twitter':
            orchestrator = AgenticTwitterOrchestrator()
            result = await orchestrator.create_content(
                topic=content,
                format_type=context.get('format_type', 'thread')
            )
            result_text += f"Twitter content created: {result.get('format_type')}"

        elif agent_type == 'email':
            orchestrator = AgenticEmailOrchestrator()
            result = await orchestrator.create_content(
                topic=content,
                email_type=context.get('email_type', 'value')
            )
            result_text += f"Email created: {result.get('email_type')} email"

        elif agent_type == 'research':
            # Use web search for research tasks
            from tools.search_tools import web_search
            result = web_search(query=content, max_results=10)
            result_text += f"Research complete: {len(json.loads(result).get('results', []))} sources found"

        else:
            result_text += f"⚠️ Unknown agent type: {agent_type}"

    except Exception as e:
        result_text += f"❌ Error: {str(e)}"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


class PlanModeHandler:
    """
    Handles plan mode where users can create structured plans
    that get delegated to subagents for execution
    """

    def __init__(self, memory_handler=None):
        """Initialize plan mode handler"""
        self.memory = memory_handler
        self.active_plans: Dict[str, Dict] = {}  # thread_ts -> plan data

        # System prompt for planning
        self.system_prompt = """You are a strategic planning assistant that creates structured execution plans.

**YOUR ROLE:**
Create detailed, actionable plans that can be delegated to specialized subagents.

**AVAILABLE SUBAGENTS:**
- linkedin: Creates LinkedIn posts with hooks, proof, and quality checks
- twitter: Creates Twitter threads, single posts, or reply guys
- email: Creates value emails, indirect pitch, or direct pitch
- research: Searches web for information, trends, and examples

**PLANNING GUIDELINES:**
1. Break complex requests into specific, actionable tasks
2. Assign each task to the most appropriate subagent
3. Set priorities (high/medium/low) based on importance
4. Define dependencies when tasks must happen in sequence
5. Keep each task focused and single-purpose

**PLAN STRUCTURE:**
Each todo item should specify:
- Clear, specific content/task description
- Which subagent will handle it
- Priority level
- Any dependencies on other tasks

Always use create_execution_plan to structure the plan properly."""

        # Tools for planning
        self.tools = [
            create_execution_plan,
            execute_plan_item
        ]

        # Agent options
        self.options = ClaudeAgentOptions(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,  # Lower temp for structured planning
            system_prompt=self.system_prompt,
            tools=self.tools
        )

        print("📋 Plan Mode Handler initialized")

    async def create_plan(
        self,
        request: str,
        user_id: str,
        thread_ts: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Create an execution plan for a user request

        Returns:
            Dict with 'plan_text' and 'todos' for execution
        """

        # Prompt for plan creation
        planning_prompt = f"""
User ({user_id}) requests: {request}

Create a detailed execution plan for this request.
Break it down into specific tasks for our subagents.
Use create_execution_plan to structure the plan.

Thread: {thread_ts}
Channel: {channel_id}
"""

        try:
            # Use Claude to create the plan
            response = await query(
                prompt=planning_prompt,
                options=self.options
            )

            # Extract plan from response
            if hasattr(response, 'metadata') and response.metadata.get('todos'):
                todos = response.metadata['todos']
                plan_text = response.content if hasattr(response, 'content') else str(response)

                # Store plan for this thread
                self.active_plans[thread_ts] = {
                    'todos': todos,
                    'user_id': user_id,
                    'channel_id': channel_id,
                    'status': 'pending_approval'
                }

                return {
                    'success': True,
                    'plan_text': plan_text,
                    'todos': todos,
                    'requires_approval': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract plan from response'
                }

        except Exception as e:
            print(f"❌ Plan creation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def execute_plan(
        self,
        thread_ts: str,
        approved: bool = True
    ) -> str:
        """
        Execute an approved plan by delegating todos to subagents

        Args:
            thread_ts: Thread identifier
            approved: Whether the plan is approved

        Returns:
            Status message
        """

        if thread_ts not in self.active_plans:
            return "❌ No active plan found for this thread"

        plan = self.active_plans[thread_ts]

        if not approved:
            del self.active_plans[thread_ts]
            return "❌ Plan cancelled"

        plan['status'] = 'executing'
        todos = plan['todos']
        results = []

        # Execute each todo
        for i, todo in enumerate(todos):
            # Check dependencies
            deps = todo.get('dependencies', [])
            if deps:
                # Wait for dependencies to complete
                # (In a real implementation, this would check completion status)
                await asyncio.sleep(0.1)

            # Execute this todo
            result = await execute_plan_item({
                'todo_id': i + 1,
                'content': todo['content'],
                'agent_type': todo['agent_type'],
                'context': {
                    'user_id': plan['user_id'],
                    'channel_id': plan['channel_id']
                }
            })

            results.append(result)

            # Update progress (in real implementation, would update TodoWrite)
            print(f"📋 Plan progress: {i+1}/{len(todos)} tasks complete")

        # Mark plan complete
        plan['status'] = 'completed'
        del self.active_plans[thread_ts]

        return f"✅ Plan execution complete! {len(todos)} tasks executed."

    def get_plan_status(self, thread_ts: str) -> Optional[Dict]:
        """Get the status of a plan for a thread"""
        return self.active_plans.get(thread_ts)
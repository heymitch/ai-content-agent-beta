"""
Anthropic Tool Conversion and Execution
Converts Python functions to Anthropic tool schema and handles execution
"""

import inspect
import json
from typing import Any, Callable, Dict, List


def convert_function_to_anthropic_tool(func: Callable) -> Dict[str, Any]:
    """
    Convert a Python function to Anthropic tool schema

    Args:
        func: Python function with type hints and docstring

    Returns:
        Anthropic tool schema dict
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        # Get type annotation
        param_type = param.annotation

        # Convert Python type to JSON schema type
        json_type = "string"  # default
        if param_type == int:
            json_type = "integer"
        elif param_type == float:
            json_type = "number"
        elif param_type == bool:
            json_type = "boolean"
        elif param_type == list or str(param_type).startswith('list'):
            json_type = "array"
        elif param_type == dict:
            json_type = "object"

        properties[param_name] = {
            "type": json_type,
            "description": f"Parameter: {param_name}"
        }

        # Check if required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "name": func.__name__,
        "description": doc.split('\n')[0] if doc else f"Tool: {func.__name__}",
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }


def convert_tools_to_anthropic_format(tools_list: List[Callable]) -> List[Dict[str, Any]]:
    """Convert list of functions to Anthropic tools format"""
    return [convert_function_to_anthropic_tool(func) for func in tools_list]


def execute_tool(tool_name: str, tool_input: Dict[str, Any], available_tools: Dict[str, Callable]) -> str:
    """
    Execute a tool by name with given input

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters as dict
        available_tools: Dict mapping tool names to functions

    Returns:
        Tool execution result as string
    """
    if tool_name not in available_tools:
        return f"Error: Tool '{tool_name}' not found"

    try:
        tool_func = available_tools[tool_name]
        result = tool_func(**tool_input)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

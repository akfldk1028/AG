"""
MCP tool definitions and server configs for SDK integration.

Two types of functions:
- Schema functions (*_tools): Reference schemas for documentation/validation.
- MCP config functions (*_mcp_config): ClaudeAgentOptions.mcp_servers configs
  for actual SDK integration.
"""

from typing import Any, Dict, List


def shared_memory_tools(base_url: str = "http://localhost:8101") -> List[Dict[str, Any]]:
    """
    SharedMemory access tools (wraps port 8101 REST API).

    Returns tool schemas for:
    - get_shared: Retrieve a value by key
    - set_shared: Store a key-value pair
    - list_events: List recent events
    """
    return [
        {
            "name": "get_shared",
            "description": "Retrieve a value from SharedMemory by key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key to retrieve."},
                },
                "required": ["key"],
            },
            "_base_url": base_url,
        },
        {
            "name": "set_shared",
            "description": "Store a key-value pair in SharedMemory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Storage key."},
                    "value": {"type": "string", "description": "Value to store."},
                },
                "required": ["key", "value"],
            },
            "_base_url": base_url,
        },
        {
            "name": "list_events",
            "description": "List recent events from SharedMemory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max events to return.",
                        "default": 20,
                    },
                },
            },
            "_base_url": base_url,
        },
    ]


def project_tools(project_root: str = ".") -> List[Dict[str, Any]]:
    """
    Project management tool schemas.

    Returns tool schemas for:
    - list_tasks: List project tasks
    - get_task_status: Get status of a specific task
    - update_progress: Update task progress
    """
    return [
        {
            "name": "list_tasks",
            "description": "List all tasks in the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "all"],
                        "default": "all",
                    },
                },
            },
            "_project_root": project_root,
        },
        {
            "name": "get_task_status",
            "description": "Get the current status of a task by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task identifier."},
                },
                "required": ["task_id"],
            },
            "_project_root": project_root,
        },
        {
            "name": "update_progress",
            "description": "Update the progress of a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "progress": {
                        "type": "number",
                        "description": "Progress percentage (0-100).",
                    },
                    "message": {"type": "string", "description": "Status message."},
                },
                "required": ["task_id", "progress"],
            },
            "_project_root": project_root,
        },
    ]


def autogen_tools(base_url: str = "http://localhost:8081") -> List[Dict[str, Any]]:
    """
    AutoGen Studio integration tool schemas.

    Returns tool schemas for:
    - list_teams: List available teams
    - get_session_runs: Get runs for a session
    - create_session: Create a new session
    """
    return [
        {
            "name": "list_teams",
            "description": "List all AutoGen Studio teams.",
            "parameters": {"type": "object", "properties": {}},
            "_base_url": base_url,
        },
        {
            "name": "get_session_runs",
            "description": "Get all runs for an AutoGen Studio session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "integer", "description": "Session ID."},
                },
                "required": ["session_id"],
            },
            "_base_url": base_url,
        },
        {
            "name": "create_session",
            "description": "Create a new AutoGen Studio session with a team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer", "description": "Team ID to use."},
                    "name": {"type": "string", "description": "Session name."},
                },
                "required": ["team_id"],
            },
            "_base_url": base_url,
        },
    ]


# ========================================
# MCP Server Configs (for ClaudeAgentOptions.mcp_servers)
# ========================================

def shared_memory_mcp_config(base_url: str = "http://localhost:8101") -> Dict[str, Dict]:
    """SharedMemory MCP server config for ClaudeAgentOptions.mcp_servers."""
    return {
        "shared-memory": {
            "type": "sse",
            "url": f"{base_url}/mcp",
        }
    }


def autogen_mcp_config(base_url: str = "http://localhost:8081") -> Dict[str, Dict]:
    """AutoGen Studio MCP server config for ClaudeAgentOptions.mcp_servers."""
    return {
        "autogen-studio": {
            "type": "sse",
            "url": f"{base_url}/mcp",
        }
    }

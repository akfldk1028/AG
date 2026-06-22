"""
AG_Cohub SDK - Claude Agent SDK modular wrapper.

Public API:
    from AG_Cohub.sdk import ClaudeSDK, ToolProfile, AgentConfig, get_preset
    from AG_Cohub.sdk import get_oauth_token, validate_token
    from AG_Cohub.sdk import ProjectContext, ContextManager
    from AG_Cohub.sdk import quality_hook, logging_hook, security_hook, merge_hooks
    from AG_Cohub.sdk import shared_memory_mcp_config, autogen_mcp_config
"""

from .auth import get_oauth_token, validate_token
from .config import (
    ToolProfile,
    PermissionMode,
    AgentConfig,
    ROLE_PRESETS,
    get_preset,
)
from .client import ClaudeSDK, SDKResult
from .context import ProjectContext, ContextManager
from .hooks import quality_hook, logging_hook, security_hook, merge_hooks
from .tools import (
    shared_memory_tools, project_tools, autogen_tools,
    shared_memory_mcp_config, autogen_mcp_config,
)

__all__ = [
    # auth
    "get_oauth_token", "validate_token",
    # config
    "ToolProfile", "PermissionMode", "AgentConfig", "ROLE_PRESETS", "get_preset",
    # client
    "ClaudeSDK", "SDKResult",
    # context
    "ProjectContext", "ContextManager",
    # hooks (SDK-native: dict[HookEvent, list[HookMatcher]])
    "quality_hook", "logging_hook", "security_hook", "merge_hooks",
    # tools (schemas=reference, mcp_config=SDK integration)
    "shared_memory_tools", "project_tools", "autogen_tools",
    "shared_memory_mcp_config", "autogen_mcp_config",
]

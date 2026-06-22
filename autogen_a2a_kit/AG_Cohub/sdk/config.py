"""
SDK configuration: tool profiles, permission modes, agent configs.

Defines role-based presets that map to Claude Agent SDK options.
"""

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ToolProfile(Enum):
    """Tool access levels for agents."""
    TEXT_ONLY = "text_only"      # tools=[] (reviewers, analysts)
    READER = "reader"            # Read/Glob/Grep/WebSearch (context gathering)
    CODER = "coder"              # Read/Write/Edit/Bash/Glob/Grep (code generation)
    FULL_AGENT = "full_agent"    # tools=None (all default tools enabled)


class PermissionMode(Enum):
    """Claude Agent SDK permission modes."""
    DEFAULT = "default"          # Ask for confirmation each time
    ACCEPT_EDITS = "acceptEdits" # Auto-approve file modifications
    PLAN_ONLY = "plan"           # Planning only, no execution


# Mapping from ToolProfile to SDK tools list
TOOLS_MAP: Dict[ToolProfile, Optional[List[str]]] = {
    ToolProfile.TEXT_ONLY: [],
    ToolProfile.READER: ["Read", "Glob", "Grep", "WebSearch"],
    ToolProfile.CODER: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    ToolProfile.FULL_AGENT: None,  # All default tools
}


@dataclass
class AgentConfig:
    """Per-agent SDK configuration."""
    name: str
    profile: ToolProfile = ToolProfile.TEXT_ONLY
    permission_mode: PermissionMode = PermissionMode.DEFAULT
    max_turns: int = 1
    max_budget_usd: Optional[float] = None
    cwd: Optional[str] = None
    system_prompt: Optional[str] = None
    output_schema: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Construct from a JSON-serializable dict (for ClaudeCLIClientConfig)."""
        if not data:
            return cls(name="default")
        profile_str = data.get("profile", "text_only")
        perm_str = data.get("permission_mode", "default")
        return cls(
            name=data.get("name", "default"),
            profile=ToolProfile(profile_str),
            permission_mode=PermissionMode(perm_str),
            max_turns=data.get("max_turns", 1),
            max_budget_usd=data.get("max_budget_usd"),
            cwd=data.get("cwd"),
            system_prompt=data.get("system_prompt"),
            output_schema=data.get("output_schema"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        d = {
            "name": self.name,
            "profile": self.profile.value,
            "permission_mode": self.permission_mode.value,
            "max_turns": self.max_turns,
        }
        if self.max_budget_usd is not None:
            d["max_budget_usd"] = self.max_budget_usd
        if self.cwd is not None:
            d["cwd"] = self.cwd
        if self.system_prompt is not None:
            d["system_prompt"] = self.system_prompt
        if self.output_schema is not None:
            d["output_schema"] = self.output_schema
        return d


# Pre-defined role presets
ROLE_PRESETS: Dict[str, AgentConfig] = {
    "generator": AgentConfig(
        name="generator", profile=ToolProfile.CODER, max_turns=3,
    ),
    "critic": AgentConfig(
        name="critic", profile=ToolProfile.TEXT_ONLY, max_turns=1,
    ),
    "reviewer": AgentConfig(
        name="reviewer", profile=ToolProfile.READER, max_turns=2,
    ),
    "planner": AgentConfig(
        name="planner", profile=ToolProfile.READER, max_turns=2,
    ),
    "full": AgentConfig(
        name="full", profile=ToolProfile.FULL_AGENT, max_turns=5,
        permission_mode=PermissionMode.ACCEPT_EDITS,
    ),
}


def get_preset(name: str) -> AgentConfig:
    """Return an independent copy of a role preset (mutable-safe)."""
    if name not in ROLE_PRESETS:
        raise KeyError(f"Unknown preset: {name}. Available: {list(ROLE_PRESETS.keys())}")
    return copy.deepcopy(ROLE_PRESETS[name])

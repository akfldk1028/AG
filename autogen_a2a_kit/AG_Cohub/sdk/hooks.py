"""
Hooks for Claude Agent SDK tool execution.

SDK expects hooks as:
    ClaudeAgentOptions(hooks={
        "PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[async_cb])],
        "PostToolUse": [HookMatcher(matcher="Bash", hooks=[async_cb])],
    })

Each callback signature (async required):
    async def cb(input: dict, tool_use_id: str|None, ctx: dict) -> dict
    Returns: {"continue_": True} or {"decision": "block", "reason": "..."}
"""

import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

# SDK types - graceful fallback if not installed
try:
    from claude_agent_sdk import HookMatcher
    _SDK_HOOKS = True
except ImportError:
    _SDK_HOOKS = False


def _make_matcher(pattern: str, callbacks: list) -> object:
    """Create HookMatcher if SDK available, else return placeholder dict."""
    if _SDK_HOOKS:
        return HookMatcher(matcher=pattern, hooks=callbacks)
    return {"matcher": pattern, "hooks": callbacks}


def quality_hook() -> Dict[str, list]:
    """
    Code quality check hook (PostToolUse on Write|Edit).

    Logs file path and content size after write operations.
    Returns: hooks dict for ClaudeAgentOptions.
    """
    async def _quality_cb(input: dict, tool_use_id: Optional[str], ctx: dict) -> dict:
        tool_name = input.get("tool_name", "")
        if tool_name in ("Write", "Edit"):
            tool_input = input.get("tool_input", {})
            fp = tool_input.get("file_path", "unknown")
            content = tool_input.get("content", "")
            print(f"[quality_hook] {tool_name} -> {fp} ({len(content)} chars)")
        return {"continue_": True}

    return {"PostToolUse": [_make_matcher("Write|Edit", [_quality_cb])]}


def logging_hook(log_path: Optional[Path] = None) -> Dict[str, list]:
    """
    Tool usage logging hook (PostToolUse on all tools).

    Logs every tool invocation with timestamp to file.
    Returns: hooks dict for ClaudeAgentOptions.
    """
    if log_path is None:
        log_path = Path.home() / ".autogenstudio" / "sdk_tools.log"

    async def _log_cb(input: dict, tool_use_id: Optional[str], ctx: dict) -> dict:
        tool_name = input.get("tool_name", "unknown")
        ts = datetime.datetime.now().isoformat()
        entry = {
            "timestamp": ts,
            "tool": tool_name,
            "tool_use_id": tool_use_id,
            "input_keys": list((input.get("tool_input") or {}).keys()),
        }
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return {"continue_": True}

    return {"PostToolUse": [_make_matcher(".*", [_log_cb])]}


def security_hook(allowed_dirs: Optional[List[str]] = None) -> Dict[str, list]:
    """
    File access security hook (PreToolUse on Write|Edit|Bash).

    Blocks operations on files outside allowed directories.
    Returns: hooks dict for ClaudeAgentOptions.
    """
    allowed = [str(Path(d).resolve()) for d in (allowed_dirs or [])]

    async def _security_cb(input: dict, tool_use_id: Optional[str], ctx: dict) -> dict:
        if not allowed:
            return {"continue_": True}

        tool_input = input.get("tool_input", {})

        # Collect paths to check: file_path for Write/Edit, command paths for Bash
        paths_to_check = []
        fp = tool_input.get("file_path", "")
        if fp:
            paths_to_check.append(fp)

        # For Bash tool, block entirely when security_hook is active
        cmd = tool_input.get("command", "")
        if cmd and not fp:
            return {"decision": "block", "reason": f"Bash blocked by security_hook: {cmd[:80]}"}

        if not paths_to_check:
            return {"continue_": True}

        allowed_paths = [Path(d).resolve() for d in allowed]
        for p in paths_to_check:
            resolved = Path(p).resolve()
            if not any(resolved == ad or resolved.is_relative_to(ad) for ad in allowed_paths):
                return {"decision": "block", "reason": f"Access denied: {p} outside allowed dirs"}

        return {"continue_": True}

    return {"PreToolUse": [_make_matcher("Write|Edit|Bash", [_security_cb])]}


def merge_hooks(*hook_dicts: Dict[str, list]) -> Dict[str, list]:
    """Merge multiple hook dicts into one (concatenates matcher lists per event)."""
    merged: Dict[str, list] = {}
    for hd in hook_dicts:
        for event, matchers in hd.items():
            merged.setdefault(event, []).extend(matchers)
    return merged

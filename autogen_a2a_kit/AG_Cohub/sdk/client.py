"""
ClaudeSDK - Core wrapper around claude-agent-sdk query().

Provides:
- query(): Single-turn call (backward-compatible with model_factory)
- conversation(): Multi-turn dialogue with memory
"""

import sys
import time
import datetime
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

from .config import AgentConfig, ToolProfile, PermissionMode, TOOLS_MAP

# SDK availability
try:
    from claude_agent_sdk import (
        query as claude_sdk_query,
        ClaudeAgentOptions,
        AssistantMessage as SDKAssistantMessage,
        UserMessage as SDKUserMessage,
        ResultMessage as SDKResultMessage,
        TextBlock as SDKTextBlock,
        ToolUseBlock as SDKToolUseBlock,
        ToolResultBlock as SDKToolResultBlock,
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# Diagnostic log (file-based, survives stderr redirect)
_LOG_PATH = pathlib.Path.home() / ".autogenstudio" / "model_factory.log"


def _log_to_file(msg: str):
    """Append a timestamped line to the diagnostic log."""
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


@dataclass
class SDKResult:
    """Result from a ClaudeSDK query or conversation turn."""
    text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_seconds: float = 0.0
    tool_outputs: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class ClaudeSDK:
    """Claude Agent SDK wrapper - query (single-turn) + conversation (multi-turn)."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self.model = model

    @property
    def available(self) -> bool:
        return SDK_AVAILABLE

    async def query(
        self,
        prompt: str,
        config: Optional[AgentConfig] = None,
        context: Optional["ProjectContext"] = None,
        hooks: Optional[dict] = None,
    ) -> SDKResult:
        """
        Single query call (superset of old model_factory._create_via_sdk).

        Args:
            prompt: User prompt text.
            config: Agent configuration (profile, max_turns, etc.).
            context: Project context (cwd, relevant files, previous results).
            hooks: List of Hook objects for pre/post-tool callbacks.

        Returns:
            SDKResult with text, token usage, and timing.
        """
        if not SDK_AVAILABLE:
            return SDKResult(
                success=False,
                error="claude-agent-sdk not installed",
            )

        config = config or AgentConfig(name="default")
        options = self._build_options(config, context, hooks)

        # Inject context into prompt if available
        if context:
            from .context import ContextManager
            prompt = ContextManager.inject_to_prompt(context, prompt)

        content_parts = []
        tool_outputs = []
        input_tokens = 0
        output_tokens = 0
        t0 = time.monotonic()

        try:
            async for message in claude_sdk_query(prompt=prompt, options=options):
                if isinstance(message, SDKAssistantMessage):
                    for block in message.content:
                        if isinstance(block, SDKTextBlock):
                            content_parts.append(block.text)
                        elif isinstance(block, SDKToolUseBlock):
                            # Capture tool execution with clear markers
                            tool_input = block.input or {}
                            if block.name in ("Write", "Edit") and "content" in tool_input:
                                fp = tool_input.get("file_path", "file")
                                code = tool_input["content"]
                                marker = f"\n[TOOL EXECUTED: {block.name}] -> {fp}"
                                extracted = f"{marker}\n```\n{code}\n```"
                                content_parts.append(extracted)
                                tool_outputs.append(fp)
                            elif block.name == "Bash" and "command" in tool_input:
                                cmd_str = tool_input["command"]
                                marker = f"\n[TOOL EXECUTED: Bash] $ {cmd_str}"
                                content_parts.append(marker)
                                tool_outputs.append(cmd_str)
                            elif block.name == "Read" and "file_path" in tool_input:
                                fp = tool_input["file_path"]
                                marker = f"\n[TOOL EXECUTED: Read] -> {fp}"
                                content_parts.append(marker)
                                tool_outputs.append(fp)
                            else:
                                marker = f"\n[TOOL EXECUTED: {block.name}]"
                                content_parts.append(marker)
                                tool_outputs.append(block.name)
                elif isinstance(message, SDKUserMessage):
                    # Tool results from SDK (after tool execution)
                    if hasattr(message, "content"):
                        for block in (message.content if isinstance(message.content, list) else [message.content]):
                            if isinstance(block, SDKToolResultBlock):
                                result_text = ""
                                if hasattr(block, "content") and block.content:
                                    if isinstance(block.content, str):
                                        result_text = block.content[:200]
                                    elif isinstance(block.content, list):
                                        for rb in block.content:
                                            if hasattr(rb, "text"):
                                                result_text += rb.text[:200]
                                if result_text:
                                    content_parts.append(f"\n[TOOL RESULT]: {result_text}")
                elif isinstance(message, SDKResultMessage):
                    if hasattr(message, "usage") and message.usage:
                        u = message.usage
                        if isinstance(u, dict):
                            input_tokens += u.get("input_tokens", 0)
                            output_tokens += u.get("output_tokens", 0)
                        else:
                            input_tokens += getattr(u, "input_tokens", 0)
                            output_tokens += getattr(u, "output_tokens", 0)

            elapsed = time.monotonic() - t0
            text = "\n".join(content_parts) if content_parts else ""
            ok_msg = (
                f"SDK OK ({elapsed:.1f}s, model={self.model}, "
                f"in={input_tokens}, out={output_tokens}, "
                f"text_chars={len(text)})"
            )
            print(f"[model_factory] {ok_msg}", file=sys.stderr)
            _log_to_file(ok_msg)

            return SDKResult(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                elapsed_seconds=elapsed,
                tool_outputs=tool_outputs,
                success=True,
            )

        except Exception as sdk_err:
            elapsed = time.monotonic() - t0
            fail_msg = (
                f"SDK FAIL ({elapsed:.1f}s): "
                f"{type(sdk_err).__name__}: {sdk_err} | "
                f"model={self.model}, prompt_len={len(prompt)}"
            )
            print(f"[model_factory] {fail_msg}", file=sys.stderr)
            _log_to_file(fail_msg)

            return SDKResult(
                success=False,
                error=str(sdk_err),
                elapsed_seconds=elapsed,
            )

    async def conversation(
        self,
        initial_prompt: str,
        config: Optional[AgentConfig] = None,
        max_exchanges: int = 10,
    ) -> List[SDKResult]:
        """
        Multi-turn conversation (future: uses ClaudeSDKClient session).

        Currently implemented as sequential single-turn queries
        where each turn's output feeds as context to the next.
        """
        config = config or AgentConfig(name="default")
        results = []
        current_prompt = initial_prompt

        for i in range(max_exchanges):
            result = await self.query(prompt=current_prompt, config=config)
            results.append(result)

            if not result.success or not result.text.strip():
                break

            # Next turn uses previous output as context
            current_prompt = (
                f"Previous response:\n{result.text}\n\n"
                f"Continue from where you left off."
            )

        return results

    def _build_options(
        self,
        config: AgentConfig,
        context: Optional["ProjectContext"] = None,
        hooks: Optional[dict] = None,
    ) -> "ClaudeAgentOptions":
        """Convert AgentConfig + ProjectContext + hooks -> ClaudeAgentOptions."""
        tools = TOOLS_MAP[config.profile]

        kwargs = {
            "model": self.model,
            "tools": tools,
            "max_turns": config.max_turns,
        }

        if hooks:
            kwargs["hooks"] = hooks

        if config.system_prompt:
            kwargs["system_prompt"] = config.system_prompt

        # cwd: config.cwd > context.cwd > None
        cwd = config.cwd
        if not cwd and context and context.cwd:
            cwd = context.cwd
        if cwd:
            kwargs["cwd"] = cwd

        if config.permission_mode != PermissionMode.DEFAULT:
            kwargs["permission_mode"] = config.permission_mode.value

        if config.output_schema:
            kwargs["output_format"] = {
                "type": "json_schema",
                "schema": config.output_schema,
            }

        if config.max_budget_usd is not None:
            kwargs["max_budget_usd"] = config.max_budget_usd

        return ClaudeAgentOptions(**kwargs)

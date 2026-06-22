"""
Model Factory for AutoGen Studio
================================

AutoGen Studio에서 다양한 LLM 모델을 사용할 수 있게 해주는 팩토리.

지원 모델:
- OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- Anthropic: claude-3-5-sonnet, claude-3-5-haiku, claude-sonnet-4-5, claude-opus-4-5
- Google: gemini-1.5-pro, gemini-1.5-flash
- Ollama: llama3, mistral, mixtral (로컬)

사용법:
    from model_factory import get_model_client, list_available_models

    # Claude 모델 사용
    client = get_model_client("claude-sonnet-4-5")

    # 사용 가능한 모델 목록
    models = list_available_models()

★ Auto-Claude 동기화:
   AG/Auto-Claude 파이프라인에서 모델이 Claude로 자동 매핑됩니다.
   이 파일을 사용하면 AutoGen Studio에서도 Claude 모델을 직접 사용할 수 있습니다.
"""

import asyncio
import json
import os
import shutil
import subprocess
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union

# SDK modular package (auth, config, client, context, hooks, tools)
from .sdk.config import AgentConfig, ToolProfile
from .sdk.client import ClaudeSDK, SDKResult


# ========================================
# Model Provider Imports
# ========================================

try:
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from autogen_ext.models.anthropic import AnthropicChatCompletionClient
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from autogen_ext.models.ollama import OllamaChatCompletionClient
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# AutoGen Core types for ChatCompletionClient
try:
    from autogen_core.models import (
        ChatCompletionClient,
        CreateResult,
        LLMMessage,
        ModelInfo,
        RequestUsage,
        SystemMessage,
        UserMessage,
        AssistantMessage,
    )
    from autogen_core import FunctionCall
    from autogen_core.tools import Tool, ToolSchema
    from autogen_core import Component
    from pydantic import BaseModel
    from typing_extensions import Self
    AUTOGEN_CORE_AVAILABLE = True
except ImportError:
    AUTOGEN_CORE_AVAILABLE = False


# ========================================
# Claude Agent SDK (via sdk/ package)
# ========================================

from .sdk.client import SDK_AVAILABLE as CLAUDE_SDK_AVAILABLE, _log_to_file

import sys as _sys
_sys.stderr.write(
    f"[model_factory] CLAUDE_SDK_AVAILABLE={CLAUDE_SDK_AVAILABLE}, "
    f"AUTOGEN_CORE={AUTOGEN_CORE_AVAILABLE}\n"
)

_log_to_file(f"LOADED: SDK={CLAUDE_SDK_AVAILABLE}, AUTOGEN_CORE={AUTOGEN_CORE_AVAILABLE}")


# ========================================
# Claude CLI ChatCompletionClient (Max 구독 OAuth)
# ========================================

if AUTOGEN_CORE_AVAILABLE:

    class ClaudeCLIClientConfig(BaseModel):
        """Configuration for ClaudeCLIChatCompletionClient."""
        model: str = "claude-sonnet-4-5-20250929"
        agent_config: Optional[dict] = None  # AgentConfig as dict (JSON teams)

    class ClaudeCLIChatCompletionClient(ChatCompletionClient, Component[ClaudeCLIClientConfig]):
        """
        Claude Agent SDK를 통한 ChatCompletionClient 구현.
        Max 구독(OAuth 로그인)으로 API 키 없이 Claude 모델 사용.

        claude-agent-sdk가 있으면 SDK (빠름, 세션 재사용),
        없으면 subprocess fallback (느림).

        SDK logic delegated to sdk/ package (ClaudeSDK, AgentConfig, ToolProfile).
        """

        component_type = "model"
        component_config_schema = ClaudeCLIClientConfig
        component_provider_override = "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient"

        def __init__(
            self,
            model: str = "claude-sonnet-4-5-20250929",
            agent_config: Optional[dict] = None,
        ):
            self._model = model
            self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
            self._use_sdk = CLAUDE_SDK_AVAILABLE
            self._agent_config = AgentConfig.from_dict(agent_config or {})
            self._sdk = ClaudeSDK(model=model) if CLAUDE_SDK_AVAILABLE else None

            # Diagnostic logging
            _log_to_file(
                f"INIT: model={model}, agent_config={agent_config}, "
                f"profile={self._agent_config.profile.value}, "
                f"perm={self._agent_config.permission_mode.value}, "
                f"max_turns={self._agent_config.max_turns}, "
                f"cwd={self._agent_config.cwd}"
            )

            # claude CLI 존재 확인
            if not shutil.which("claude"):
                raise FileNotFoundError(
                    "Claude CLI not found. Install from https://code.claude.com\n"
                    "Then run: claude /login"
                )

        async def create(
            self,
            messages: Sequence[LLMMessage],
            *,
            tools: Sequence[Union[Tool, ToolSchema]] = (),
            json_output: Optional[Any] = None,
            extra_create_args: Mapping[str, Any] = {},
            cancellation_token: Optional[Any] = None,
            **kwargs,
        ) -> CreateResult:
            """메시지 전송하고 결과 반환. SDK 우선, subprocess fallback."""
            # 도구 이름 → {description, parameters} 매핑
            tool_map: Dict[str, Dict[str, Any]] = {}
            if tools:
                for t in tools:
                    schema = t.schema if isinstance(t, Tool) else t
                    if isinstance(schema, dict):
                        name = schema.get("name", "")
                        desc = schema.get("description", "")
                        params = schema.get("parameters", {})
                    else:
                        name = getattr(schema, "name", "")
                        desc = getattr(schema, "description", "")
                        params = getattr(schema, "parameters", {})
                    if name:
                        tool_map[name] = {"description": desc, "parameters": params}

            # 메시지를 텍스트로 변환
            system_parts = []
            conversation_turns = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    system_parts.append(msg.content)
                elif isinstance(msg, UserMessage):
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    conversation_turns.append(("user", content))
                elif isinstance(msg, AssistantMessage):
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    conversation_turns.append(("assistant", content))

            # 도구 설명 + 파라미터 스키마를 시스템 프롬프트에 주입
            if tool_map:
                import json as _json
                tool_lines = ["[사용 가능한 도구]"]
                for name, info in tool_map.items():
                    desc = info.get("description", "")
                    params = info.get("parameters", {})
                    props = params.get("properties", {})
                    required = params.get("required", [])
                    if props:
                        # Show full parameter schema
                        param_desc = []
                        for pname, pschema in props.items():
                            ptype = pschema.get("type", "any")
                            pdesc = pschema.get("description", "")
                            req = " (필수)" if pname in required else ""
                            param_desc.append(f"    - {pname}: {ptype}{req} — {pdesc}")
                        tool_lines.append(f"- {name}: {desc}")
                        tool_lines.append(f"  파라미터:")
                        tool_lines.extend(param_desc)
                    else:
                        tool_lines.append(f"- {name}: {desc} (파라미터 없음)")
                tool_lines.append(
                    "\n도구를 사용하려면 응답에 정확히 다음 형식을 포함하세요:\n"
                    '[TOOL_CALL: 도구이름] {"파라미터명": "값", ...}\n'
                    "파라미터가 없는 도구는 JSON 부분을 생략하세요.\n"
                    '예1: [TOOL_CALL: analyze_land] {"pnu_or_address": "강남구 역삼동 677", "include_law": true}\n'
                    "예2: [TOOL_CALL: transfer_to_support_agent]"
                )
                system_parts.append("\n".join(tool_lines))

            # Selector prompt 감지: 단일 메시지 + 역할 선택 패턴
            is_selector = (
                len(conversation_turns) == 1
                and not system_parts
                and ("이름만 반환" in conversation_turns[0][1] or "Read the above conversation" in conversation_turns[0][1])
            )

            # 대화 턴이 1개면 단순 프롬프트, 여러 개면 대화 기록 형식
            if len(conversation_turns) <= 1:
                prompt = conversation_turns[0][1] if conversation_turns else ""
            else:
                parts = ["=== 대화 기록 ==="]
                for role, content in conversation_turns:
                    label = "사용자" if role == "user" else "이전 에이전트"
                    parts.append(f"\n[{label}]:\n{content}")
                parts.append("\n=== 위 대화를 기반으로 당신의 차례입니다. 시스템 프롬프트의 역할에 따라 응답하세요. ===")
                prompt = "\n".join(parts)

            if is_selector:
                # Selector prompt: 간결한 응답 유도
                system_parts.append(
                    "중요: 반드시 선택한 이름 하나만 출력하세요. 설명이나 분석을 절대 포함하지 마세요. "
                    "예: advocate 또는 critic 또는 judge"
                )

            # Truncate prompt to avoid Windows command line limit (32K chars)
            # SDK internally passes prompt via --print -- <prompt> on command line
            _MAX_PROMPT_CHARS = 28000
            if len(prompt) > _MAX_PROMPT_CHARS:
                _keep_start = min(8000, _MAX_PROMPT_CHARS // 4)
                _keep_end = _MAX_PROMPT_CHARS - _keep_start - 60
                _orig_len = len(prompt)
                prompt = (
                    prompt[:_keep_start]
                    + "\n\n[... 이전 대화 일부 생략 (원본 길이: "
                    + str(_orig_len) + " chars) ...]\n\n"
                    + prompt[-_keep_end:]
                )
                print(
                    f"[model_factory] PROMPT TRUNCATED: {_orig_len} -> {len(prompt)} chars",
                    file=_sys.stderr,
                )

            if self._use_sdk:
                result = await self._create_via_sdk(prompt, system_parts)
            else:
                result = await self._create_via_subprocess(prompt, system_parts, extra_create_args)

            # Selector 응답 후처리: 마지막 줄에서 이름만 추출
            if is_selector and isinstance(result.content, str):
                text = result.content.strip()
                # 마지막 줄에서 이름 추출
                last_line = text.strip().split("\n")[-1].strip()
                # 알파벳/밑줄만 추출
                import re
                name_match = re.search(r'\b([a-z][a-z_]+)\b', last_line)
                if name_match:
                    result = CreateResult(
                        finish_reason=result.finish_reason,
                        content=name_match.group(1),
                        usage=result.usage,
                        cached=False,
                    )

            # 도구 호출 파싱: 응답 텍스트에서 [TOOL_CALL: name] {...} 또는 transfer_to_* 패턴 감지
            if tool_map and isinstance(result.content, str):
                import re
                import json as _json
                text = result.content

                # Pattern 1: [TOOL_CALL: name] followed by optional JSON arguments
                match = re.search(
                    r'\[TOOL_CALL:\s*(\S+)\]\s*(\{[^}]*\})?',
                    text,
                    re.DOTALL,
                )
                if match and match.group(1) in tool_map:
                    call_name = match.group(1)
                    raw_args = match.group(2)
                    # Parse JSON arguments if present
                    if raw_args:
                        try:
                            parsed = _json.loads(raw_args)
                            arguments = _json.dumps(parsed, ensure_ascii=False)
                        except _json.JSONDecodeError:
                            arguments = "{}"
                    else:
                        arguments = "{}"
                    return CreateResult(
                        finish_reason="function_calls",
                        content=[FunctionCall(id=f"call_{call_name}", arguments=arguments, name=call_name)],
                        usage=result.usage,
                        cached=False,
                    )

                # Pattern 1b: [TOOL_CALL: name] followed by multi-line JSON (```json block)
                match_block = re.search(
                    r'\[TOOL_CALL:\s*(\S+)\]\s*```(?:json)?\s*(\{[\s\S]*?\})\s*```',
                    text,
                )
                if match_block and match_block.group(1) in tool_map:
                    call_name = match_block.group(1)
                    try:
                        parsed = _json.loads(match_block.group(2))
                        arguments = _json.dumps(parsed, ensure_ascii=False)
                    except _json.JSONDecodeError:
                        arguments = "{}"
                    return CreateResult(
                        finish_reason="function_calls",
                        content=[FunctionCall(id=f"call_{call_name}", arguments=arguments, name=call_name)],
                        usage=result.usage,
                        cached=False,
                    )

                # Pattern 2: tool name as whole word in SHORT text (for handoff tools like transfer_to_*)
                # Only apply when text is short to avoid false positives in discussion text
                stripped = text.strip()
                if len(stripped) < 200:
                    for name in tool_map:
                        if re.search(r'\b' + re.escape(name) + r'\b', stripped):
                            return CreateResult(
                                finish_reason="function_calls",
                                content=[FunctionCall(id=f"call_{name}", arguments="{}", name=name)],
                                usage=result.usage,
                                cached=False,
                            )

            return result

        async def _create_via_sdk(
            self, prompt: str, system_parts: list[str]
        ) -> CreateResult:
            """Delegate to ClaudeSDK.query(). Falls back to subprocess on failure."""
            import sys

            system_prompt = "\n\n".join(system_parts) if system_parts else None
            config = AgentConfig(
                name=self._agent_config.name,
                profile=self._agent_config.profile,
                permission_mode=self._agent_config.permission_mode,
                max_turns=self._agent_config.max_turns,
                system_prompt=system_prompt,
                cwd=self._agent_config.cwd,
                max_budget_usd=self._agent_config.max_budget_usd,
                output_schema=self._agent_config.output_schema,
            )

            # Diagnostic: log the exact config being sent to SDK
            from .sdk.config import TOOLS_MAP
            tools_list = TOOLS_MAP.get(config.profile)
            _log_to_file(
                f"SDK_CALL: profile={config.profile.value}, "
                f"tools={tools_list}, "
                f"perm={config.permission_mode.value}, "
                f"max_turns={config.max_turns}, "
                f"cwd={config.cwd}, "
                f"prompt_len={len(prompt)}, "
                f"sys_len={len(system_prompt) if system_prompt else 0}, "
                f"prompt_preview={prompt[:200]!r}"
            )

            result = await self._sdk.query(prompt=prompt, config=config)

            if not result.success:
                print(
                    f"[model_factory] SDK FAIL: {result.error}\n  Falling back to subprocess...",
                    file=sys.stderr,
                )
                return await self._create_via_subprocess(prompt, system_parts, {})

            usage = RequestUsage(
                prompt_tokens=result.input_tokens,
                completion_tokens=result.output_tokens,
            )
            self._total_usage = RequestUsage(
                prompt_tokens=self._total_usage.prompt_tokens + usage.prompt_tokens,
                completion_tokens=self._total_usage.completion_tokens + usage.completion_tokens,
            )

            return CreateResult(
                finish_reason="stop",
                content=result.text,
                usage=usage,
                cached=False,
            )

        async def _create_via_subprocess(
            self, prompt: str, system_parts: list[str], extra_create_args: Mapping[str, Any]
        ) -> CreateResult:
            """subprocess fallback - claude-agent-sdk 미설치 시 사용."""
            import sys
            import time as _time

            timeout_sec = int(extra_create_args.get("timeout", 600))
            t0 = _time.monotonic()

            cmd = [
                "claude", "-p", prompt,
                "--output-format", "json",
                "--model", self._model,
                "--max-turns", "1",
            ]

            if system_parts:
                cmd.extend(["--append-system-prompt", "\n\n".join(system_parts)])

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    encoding="utf-8",
                )
            )
            elapsed = _time.monotonic() - t0
            sub_msg = f"SUBPROCESS ({elapsed:.1f}s, model={self._model})"
            print(f"[model_factory] {sub_msg}", file=sys.stderr)
            _log_to_file(sub_msg)

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            try:
                response_data = json.loads(result.stdout)
                if isinstance(response_data, dict):
                    content = response_data.get("result", result.stdout)
                    usage_data = response_data.get("usage", {})
                    input_tokens = usage_data.get("input_tokens", 0)
                    output_tokens = usage_data.get("output_tokens", 0)
                else:
                    content = result.stdout
                    input_tokens = 0
                    output_tokens = 0
            except json.JSONDecodeError:
                content = result.stdout
                input_tokens = 0
                output_tokens = 0

            usage = RequestUsage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
            )
            self._total_usage = RequestUsage(
                prompt_tokens=self._total_usage.prompt_tokens + usage.prompt_tokens,
                completion_tokens=self._total_usage.completion_tokens + usage.completion_tokens,
            )

            return CreateResult(
                finish_reason="stop",
                content=content,
                usage=usage,
                cached=False,
            )

        async def create_stream(self, *args, **kwargs) -> AsyncGenerator:
            """스트리밍은 미지원 - create()로 대체."""
            raise NotImplementedError("Streaming not supported for Claude CLI client")

        def actual_usage(self) -> RequestUsage:
            return self._total_usage

        def total_usage(self) -> RequestUsage:
            return self._total_usage

        @property
        def capabilities(self) -> ModelInfo:
            return {
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
                "family": "claude",
            }

        @property
        def model_info(self) -> ModelInfo:
            return self.capabilities

        def count_tokens(self, messages: Sequence[LLMMessage], *args, **kwargs) -> int:
            return sum(len(str(m.content)) // 4 for m in messages)

        @property
        def remaining_tokens(self) -> int:
            return 200000  # Claude Max는 사실상 무제한

        async def close(self) -> None:
            """리소스 정리."""
            pass

        def _to_config(self) -> ClaudeCLIClientConfig:
            return ClaudeCLIClientConfig(
                model=self._model,
                agent_config=self._agent_config.to_dict(),
            )

        @classmethod
        def _from_config(cls, config: ClaudeCLIClientConfig) -> Self:
            return cls(model=config.model, agent_config=config.agent_config)


# ========================================
# Model Catalog
# ========================================

# OpenAI Models
OPENAI_MODELS = {
    "gpt-4o": {"full_name": "gpt-4o", "provider": "openai"},
    "gpt-4o-mini": {"full_name": "gpt-4o-mini", "provider": "openai"},
    "gpt-4-turbo": {"full_name": "gpt-4-turbo", "provider": "openai"},
    "gpt-4": {"full_name": "gpt-4", "provider": "openai"},
    "gpt-3.5-turbo": {"full_name": "gpt-3.5-turbo", "provider": "openai"},
    "o1": {"full_name": "o1", "provider": "openai"},
    "o1-mini": {"full_name": "o1-mini", "provider": "openai"},
}

# Anthropic (Claude) Models ★
ANTHROPIC_MODELS = {
    # Claude 4.5 (Latest)
    "claude-opus-4-5": {"full_name": "claude-opus-4-5-20251101", "provider": "anthropic"},
    "claude-sonnet-4-5": {"full_name": "claude-sonnet-4-5-20250929", "provider": "anthropic"},
    "claude-haiku-4-5": {"full_name": "claude-haiku-4-5-20251001", "provider": "anthropic"},

    # Claude 3.5
    "claude-3-5-sonnet": {"full_name": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
    "claude-3-5-haiku": {"full_name": "claude-3-5-haiku-20241022", "provider": "anthropic"},

    # Claude 3
    "claude-3-opus": {"full_name": "claude-3-opus-20240229", "provider": "anthropic"},
    "claude-3-sonnet": {"full_name": "claude-3-sonnet-20240229", "provider": "anthropic"},
    "claude-3-haiku": {"full_name": "claude-3-haiku-20240307", "provider": "anthropic"},

    # Aliases
    "claude": {"full_name": "claude-sonnet-4-5-20250929", "provider": "anthropic"},  # Default
}

# Ollama (Local) Models
OLLAMA_MODELS = {
    "llama3": {"full_name": "llama3", "provider": "ollama"},
    "llama3.1": {"full_name": "llama3.1", "provider": "ollama"},
    "llama3.2": {"full_name": "llama3.2", "provider": "ollama"},
    "mistral": {"full_name": "mistral", "provider": "ollama"},
    "mixtral": {"full_name": "mixtral", "provider": "ollama"},
    "codellama": {"full_name": "codellama", "provider": "ollama"},
    "deepseek-coder": {"full_name": "deepseek-coder", "provider": "ollama"},
}

# Combined catalog
ALL_MODELS = {**OPENAI_MODELS, **ANTHROPIC_MODELS, **OLLAMA_MODELS}


# ========================================
# Model Factory Functions
# ========================================

def get_model_client(
    model_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> Any:
    """
    모델 이름으로 적절한 클라이언트 생성.

    Args:
        model_name: 모델 이름 (예: "claude-sonnet-4-5", "gpt-4o-mini")
        api_key: API 키 (없으면 환경변수에서 읽음)
        base_url: 커스텀 base URL (Ollama 등)
        **kwargs: 추가 클라이언트 옵션

    Returns:
        ChatCompletionClient 인스턴스

    Raises:
        ValueError: 지원하지 않는 모델
        ImportError: 필요한 패키지가 설치되지 않음
    """
    model_lower = model_name.lower().strip()

    # 모델 정보 조회
    model_info = ALL_MODELS.get(model_lower)

    if not model_info:
        # 패턴 매칭으로 provider 추정
        if "claude" in model_lower:
            model_info = {"full_name": model_name, "provider": "anthropic"}
        elif "gpt" in model_lower or "o1" in model_lower:
            model_info = {"full_name": model_name, "provider": "openai"}
        elif "llama" in model_lower or "mistral" in model_lower:
            model_info = {"full_name": model_name, "provider": "ollama"}
        else:
            raise ValueError(
                f"Unknown model: {model_name}\n"
                f"Available models: {list(ALL_MODELS.keys())}"
            )

    provider = model_info["provider"]
    full_name = model_info["full_name"]

    # Provider별 클라이언트 생성
    if provider == "anthropic":
        # ★ Claude Max OAuth 우선 사용 (API 키 불필요)
        # 우선순위: api_key 인자 > ANTHROPIC_API_KEY > Claude CLI (Max 구독 OAuth)
        explicit_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if explicit_api_key:
            # API 키 사용 시 anthropic 패키지 필요
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "AnthropicChatCompletionClient is not available.\n"
                    "Install with: pip install autogen-ext[anthropic]"
                )
            return AnthropicChatCompletionClient(
                model=full_name,
                api_key=explicit_api_key,
                **kwargs
            )

        # API 키 없으면 Claude CLI 래퍼 사용 (Max 구독 OAuth)
        # ★ anthropic 패키지 없어도 CLI/SDK 래퍼는 작동
        if AUTOGEN_CORE_AVAILABLE and shutil.which("claude"):
            return ClaudeCLIChatCompletionClient(model=full_name)

        raise ValueError(
            "Claude 인증 정보를 찾을 수 없습니다.\n"
            "다음 중 하나를 설정하세요:\n"
            "  1. Claude Max: 'claude' 실행 후 /login (OAuth 토큰 자동 저장)\n"
            "  2. API 키: ANTHROPIC_API_KEY 환경변수 설정"
        )

    elif provider == "openai":
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAIChatCompletionClient is not available.\n"
                "Install with: pip install autogen-ext[openai]"
            )

        return OpenAIChatCompletionClient(
            model=full_name,
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            **kwargs
        )

    elif provider == "ollama":
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "OllamaChatCompletionClient is not available.\n"
                "Install with: pip install autogen-ext[ollama]"
            )

        return OllamaChatCompletionClient(
            model=full_name,
            host=base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def list_available_models() -> dict:
    """
    사용 가능한 모델 목록 반환.

    Returns:
        {provider: [model_names]} 형태의 딕셔너리
    """
    # Claude는 API 패키지 없어도 CLI/SDK로 사용 가능
    claude_available = ANTHROPIC_AVAILABLE or CLAUDE_SDK_AVAILABLE or bool(shutil.which("claude"))
    result = {
        "openai": [] if not OPENAI_AVAILABLE else list(OPENAI_MODELS.keys()),
        "anthropic": [] if not claude_available else list(ANTHROPIC_MODELS.keys()),
        "ollama": [] if not OLLAMA_AVAILABLE else list(OLLAMA_MODELS.keys()),
    }
    return result


def get_recommended_model(task_type: str = "general") -> str:
    """
    작업 유형에 따른 권장 모델 반환.

    Args:
        task_type: 작업 유형 (general, coding, creative, fast)

    Returns:
        권장 모델 이름
    """
    recommendations = {
        "general": "claude-sonnet-4-5",
        "coding": "claude-sonnet-4-5",
        "creative": "claude-opus-4-5",
        "reasoning": "claude-opus-4-5",
        "fast": "claude-3-5-haiku",
        "cheap": "gpt-4o-mini",
        "local": "llama3",
    }
    return recommendations.get(task_type, "claude-sonnet-4-5")


def check_provider_availability() -> dict:
    """
    각 provider의 가용성 확인.

    Returns:
        {provider: bool} 형태의 딕셔너리
    """
    return {
        "openai": OPENAI_AVAILABLE,
        "anthropic": ANTHROPIC_AVAILABLE,
        "ollama": OLLAMA_AVAILABLE,
    }


# ========================================
# CLI Test
# ========================================

if __name__ == "__main__":
    print("=== Model Factory Status ===\n")

    # Provider 가용성
    print("Provider Availability:")
    for provider, available in check_provider_availability().items():
        status = "OK" if available else "NO"
        print(f"  [{status}] {provider}")

    # 사용 가능한 모델
    print("\nAvailable Models:")
    for provider, models in list_available_models().items():
        if models:
            print(f"\n  {provider}:")
            for m in models[:5]:  # 최대 5개만 표시
                print(f"    - {m}")
            if len(models) > 5:
                print(f"    ... and {len(models) - 5} more")

    # 권장 모델
    print("\nRecommended Models:")
    for task in ["general", "coding", "creative", "fast"]:
        print(f"  {task:10} → {get_recommended_model(task)}")

    # 테스트 클라이언트 생성
    print("\n=== Client Creation Test ===\n")
    try:
        client = get_model_client("claude-sonnet-4-5")
        sdk_tag = "(SDK)" if CLAUDE_SDK_AVAILABLE else "(subprocess)"
        print(f"[OK] Created Claude client: {type(client).__name__} {sdk_tag}")
    except Exception as e:
        print(f"[FAIL] Claude client error: {e}")

    if OPENAI_AVAILABLE:
        try:
            client = get_model_client("gpt-4o-mini")
            print(f"[OK] Created OpenAI client: {type(client).__name__}")
        except Exception as e:
            print(f"[FAIL] OpenAI client error: {e}")

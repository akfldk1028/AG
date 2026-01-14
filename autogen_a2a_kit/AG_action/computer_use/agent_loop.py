"""
Computer Use Agent Loop
========================

Claude API를 직접 호출하여 Computer Use 실행.

공식 패턴 기반:
https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo

Features:
- FSM 기반 상태 관리 (fsm/ 모듈 연동)
- Prompt Caching 지원
- Image Truncation 지원

Usage:
    agent = ComputerUseAgent()
    result = await agent.run("Chrome에서 구글 검색해줘")
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

# Anthropic SDK
try:
    from anthropic import Anthropic, APIError, RateLimitError, AuthenticationError
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("[ComputerUse] anthropic SDK not installed. Run: pip install anthropic")

# FSM 연동 (상대 import)
from ..fsm import FSMController, State, Event

# Resolution Scaling 지원 (상대 import)
from ..primitives import ScalingTarget, ScalingInfo

from .tool_executor import ToolExecutor


@dataclass
class AgentCallbacks:
    """Agent 콜백 (확장성)"""
    on_tool_start: Optional[Callable[[str, Dict], None]] = None
    on_tool_end: Optional[Callable[[str, Dict, Dict], None]] = None
    on_screenshot: Optional[Callable[[bytes], None]] = None
    on_api_response: Optional[Callable[[Any], None]] = None
    on_state_change: Optional[Callable[[State, State], None]] = None


@dataclass
class AgentResult:
    """Agent 실행 결과"""
    success: bool
    response: str = ""
    iterations: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    fsm_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "response": self.response,
            "iterations": self.iterations,
            "tool_calls_count": len(self.tool_calls),
            "error": self.error,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at else None
            ),
            "fsm_history": self.fsm_history,
        }


class ComputerUseAgent:
    """
    Computer Use Agent

    Claude API를 직접 호출하여 컴퓨터 제어.

    Features:
    - FSM 기반 상태 관리 (fsm/ 모듈 연동)
    - 자동 스크린샷 캡처
    - Tool 실행 및 결과 전송
    - Prompt Caching 지원 (비용 절감)
    - Image Truncation 지원 (토큰 효율)
    - Callback 시스템 (확장성)

    Args:
        model: Claude 모델 (기본: claude-sonnet-4-20250514)
        max_iterations: 최대 반복 횟수 (기본: 20)
        display_width: 화면 너비 (기본: 1920)
        display_height: 화면 높이 (기본: 1080)
        dry_run: 테스트 모드 (실제 실행 안함)
        max_recent_images: 유지할 최근 이미지 수 (토큰 절약)
        screenshot_delay: 스크린샷 전 대기 시간 (기본: 2.0초)
        system_prompt: 커스텀 시스템 프롬프트 (선택)
        scaling_target: Resolution Scaling 대상 (XGA, WXGA, NONE)
        callbacks: 콜백 핸들러

    Note:
        Prompt Caching은 GA - cache_control로 자동 적용 (비용 90%, 지연 85% 절감)
        Resolution Scaling: XGA(1024x768)는 토큰 최소화, WXGA(1280x800)는 균형잡힌 선택
    """

    # 지원 모델
    SUPPORTED_MODELS = [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-sonnet-4-5-20250514",
    ]

    # Beta flags
    COMPUTER_USE_BETA = "computer-use-2025-01-24"
    # NOTE: prompt-caching-2024-07-31 is no longer needed (GA since Dec 2024)

    # 기본 System Prompt (공식 패턴)
    DEFAULT_SYSTEM_PROMPT = """You are a computer use agent that can control a desktop computer.
You have access to a computer with a display, and you can take screenshots, click, type, and run commands.

Important guidelines:
- Always take a screenshot first to understand the current state
- Use precise coordinates when clicking
- Wait for UI to settle after actions before taking another screenshot
- For GUI applications, they may take time to appear after launching
"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_iterations: int = 20,
        display_width: int = 1920,
        display_height: int = 1080,
        dry_run: bool = False,
        max_recent_images: int = 3,
        screenshot_delay: float = 2.0,
        system_prompt: Optional[str] = None,
        scaling_target: ScalingTarget = ScalingTarget.NONE,
        callbacks: Optional[AgentCallbacks] = None,
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.display_width = display_width
        self.display_height = display_height
        self.dry_run = dry_run
        self.max_recent_images = max_recent_images
        self.screenshot_delay = screenshot_delay
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.scaling_target = scaling_target
        self.callbacks = callbacks or AgentCallbacks()

        # FSM Controller 사용 (기존 AgentState 대체)
        self.fsm = FSMController()
        self._messages: List[Dict] = []

        # Resolution Scaling 정보 (좌표 변환용)
        self._scaling_info: Optional[ScalingInfo] = None

        # 클라이언트 초기화
        self._client = None
        if HAS_ANTHROPIC and not dry_run:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self._client = Anthropic(api_key=api_key)
            else:
                print("[ComputerUse] ANTHROPIC_API_KEY not set")

        # Tool Executor
        self.executor = ToolExecutor(dry_run=dry_run)

    @property
    def tools(self) -> List[Dict[str, Any]]:
        """
        Computer Use Tools 정의

        Note:
            Resolution Scaling 활성화 시 스케일된 크기를 Claude에게 전달.
            Claude가 반환하는 좌표도 스케일된 크기 기준이므로 변환 필요.
        """
        # 스케일링 활성화 시 스케일된 크기 사용
        if self._scaling_info and self._scaling_info.enabled:
            width = self._scaling_info.scaled_width
            height = self._scaling_info.scaled_height
        else:
            width = self.display_width
            height = self.display_height

        return [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": width,
                "display_height_px": height,
            },
            {
                "type": "bash_20250124",
                "name": "bash",
            },
            {
                "type": "text_editor_20250728",  # Claude 4 모델용
                "name": "str_replace_based_edit_tool",
            },
        ]

    @property
    def betas(self) -> List[str]:
        """사용할 beta flags (Computer Use만 필요)"""
        # NOTE: Prompt Caching은 2024년 12월부터 GA - beta header 불필요
        return [self.COMPUTER_USE_BETA]

    @property
    def state(self) -> State:
        """현재 FSM 상태 (호환성)"""
        return self.fsm.state.current

    async def run(
        self,
        user_request: str,
        initial_screenshot: bool = True,
    ) -> AgentResult:
        """
        Agent Loop 실행 (FSM 기반)

        Args:
            user_request: 사용자 요청
            initial_screenshot: 초기 스크린샷 포함 여부

        Returns:
            AgentResult
        """
        result = AgentResult(
            success=False,
            started_at=datetime.now(),
        )

        if not self._client and not self.dry_run:
            result.error = "Anthropic client not initialized"
            result.completed_at = datetime.now()
            return result

        try:
            # FSM 시작
            await self.fsm.start(user_request)
            self._messages = []

            # 초기 스크린샷 (FSM: IDLE → SCREENSHOT)
            screenshot_data = None
            if initial_screenshot:
                # Screenshot Delay - UI 안정화 대기 (공식 패턴: 2.0s)
                if self.screenshot_delay > 0:
                    await asyncio.sleep(self.screenshot_delay)

                # Resolution Scaling 적용
                if self.scaling_target != ScalingTarget.NONE:
                    screenshot, scaling_info = self.executor.computer.screen.screenshot_scaled(
                        target=self.scaling_target
                    )
                    self._scaling_info = scaling_info
                    if screenshot.success:
                        screenshot_data = screenshot.base64_data
                else:
                    screenshot = self.executor.screenshot()
                    self._scaling_info = ScalingInfo(enabled=False)
                    if screenshot.get("success"):
                        screenshot_data = screenshot.get("base64_data", "")

                if screenshot_data and self.callbacks.on_screenshot:
                    self.callbacks.on_screenshot(screenshot_data)

            # 메시지 구성
            content = [{"type": "text", "text": user_request}]
            if screenshot_data:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_data,
                    },
                })

            self._messages.append({"role": "user", "content": content})

            # FSM: SCREENSHOT → ANALYZE (스크린샷 촬영 완료)
            await self.fsm.on_screenshot_taken(
                screenshot_data.encode() if screenshot_data else b"",
                {"width": self.display_width, "height": self.display_height}
            )

            # Agent Loop
            for i in range(self.max_iterations):
                result.iterations = i + 1

                # Dry run 모드
                if self.dry_run:
                    print(f"[DRY_RUN] Iteration {i+1}: Would call Claude API")
                    await asyncio.sleep(0.1)
                    result.success = True
                    result.response = f"[DRY_RUN] Completed after {i+1} iterations"
                    break

                # Image Truncation (토큰 절약)
                self._truncate_images()

                # 1. Claude API 호출 (FSM: ANALYZE)
                response = self._call_api()
                if not response:
                    await self.fsm.error("API call failed")
                    result.error = "API call failed"
                    break

                if self.callbacks.on_api_response:
                    self.callbacks.on_api_response(response)

                # 2. tool_use 추출
                tool_uses = self._extract_tool_uses(response)

                # 3. tool_use가 없으면 완료
                if not tool_uses:
                    result.success = True
                    result.response = self._extract_text(response)
                    await self.fsm.complete(result.response)
                    break

                # FSM: ANALYZE → ACTION (액션 결정됨)
                for tool_use in tool_uses:
                    await self.fsm.on_action_decided(
                        tool_use.get("name"),
                        tool_use.get("input", {})
                    )

                # 4. Tool 실행
                tool_results = []
                for tool_use in tool_uses:
                    tool_name = tool_use.get("name")
                    tool_input = tool_use.get("input", {})

                    if self.callbacks.on_tool_start:
                        self.callbacks.on_tool_start(tool_name, tool_input)

                    tool_result = await self._execute_tool(tool_use)
                    tool_results.append(tool_result)

                    if self.callbacks.on_tool_end:
                        self.callbacks.on_tool_end(tool_name, tool_input, tool_result)

                    result.tool_calls.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": "success" if tool_result else "failed",
                    })

                # FSM: ACTION → VERIFY (액션 완료)
                await self.fsm.on_action_done({"tool_results": tool_results})

                # 5. 결과 전송 (FSM: VERIFY → ANALYZE 또는 COMPLETE)
                self._messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                self._messages.append({
                    "role": "user",
                    "content": tool_results,
                })

                # 검증 결과 - 계속 진행 (VERIFY → ANALYZE loop)
                await self.fsm.on_verify_result(is_complete=False, reason="continue")

            else:
                # 최대 반복 도달
                await self.fsm.error(f"Max iterations ({self.max_iterations}) reached")
                result.error = f"Max iterations ({self.max_iterations}) reached"

        except RateLimitError as e:
            await self.fsm.error(f"Rate limit: {e}")
            result.error = f"Rate limit exceeded. Please wait and retry."
        except AuthenticationError as e:
            await self.fsm.error(f"Auth error: {e}")
            result.error = "Invalid API key"
        except Exception as e:
            await self.fsm.error(str(e))
            result.error = str(e)

        result.completed_at = datetime.now()
        result.fsm_history = self.fsm.state.history
        return result

    def _truncate_images(self):
        """
        Image Truncation - 오래된 이미지 제거 (토큰 절약)

        공식 구현: _maybe_filter_to_n_most_recent_images
        """
        if self.max_recent_images <= 0:
            return

        image_count = 0
        # 역순으로 순회하며 최근 이미지만 유지
        for msg in reversed(self._messages):
            if not isinstance(msg.get("content"), list):
                continue

            new_content = []
            for item in msg["content"]:
                if isinstance(item, dict) and item.get("type") == "image":
                    if image_count < self.max_recent_images:
                        new_content.append(item)
                        image_count += 1
                    # else: 이미지 제거 (placeholder로 대체)
                    else:
                        new_content.append({
                            "type": "text",
                            "text": "[Image truncated for token efficiency]"
                        })
                else:
                    new_content.append(item)

            msg["content"] = new_content

    def _apply_cache_control(self):
        """
        Prompt Cache Control 적용 (공식 패턴)

        최근 3개 메시지에 cache_control 마커 추가.
        cache_control은 비용 90%, 지연 85% 절감.
        """
        # 최근 3개 conversation turn에만 cache breakpoint
        cache_turns = 3
        turn_count = 0

        for msg in reversed(self._messages):
            if turn_count >= cache_turns:
                break

            content = msg.get("content")
            if isinstance(content, list) and content:
                # 마지막 content item에 cache_control 추가
                last_item = content[-1]
                if isinstance(last_item, dict) and "cache_control" not in last_item:
                    last_item["cache_control"] = {"type": "ephemeral"}
            elif isinstance(content, str):
                # 문자열인 경우 dict로 변환
                msg["content"] = [{
                    "type": "text",
                    "text": content,
                    "cache_control": {"type": "ephemeral"}
                }]

            turn_count += 1

    def _call_api(self):
        """Claude API 호출 (System Prompt + Prompt Caching 지원)"""
        try:
            # Cache Control 적용
            self._apply_cache_control()

            # System Prompt with cache_control (공식 패턴)
            system = [{
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"}
            }]

            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                tools=self.tools,
                messages=self._messages,
                betas=self.betas,
            )
            return response
        except RateLimitError:
            raise  # 상위에서 처리
        except AuthenticationError:
            raise  # 상위에서 처리
        except APIError as e:
            print(f"[ComputerUse] API Error: {e}")
            return None
        except Exception as e:
            print(f"[ComputerUse] Unexpected Error: {e}")
            return None

    def _extract_tool_uses(self, response) -> List[Dict]:
        """tool_use 블록 추출"""
        tool_uses = []
        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_uses

    def _extract_text(self, response) -> str:
        """텍스트 응답 추출"""
        texts = []
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                texts.append(block.text)
        return "\n".join(texts)

    async def _execute_tool(self, tool_use: Dict) -> Dict:
        """
        Tool 실행

        Note:
            Resolution Scaling 활성화 시 좌표 변환 수행.
            Claude가 반환하는 좌표는 스케일된 이미지 기준이므로
            원본 화면 좌표로 변환 후 실행.
        """
        tool_name = tool_use.get("name")
        tool_input = tool_use.get("input", {})
        tool_id = tool_use.get("id")

        # Resolution Scaling: 좌표 변환 (computer tool의 coordinate 필드)
        if (
            tool_name == "computer"
            and self._scaling_info
            and self._scaling_info.enabled
            and "coordinate" in tool_input
        ):
            coord = tool_input["coordinate"]
            if isinstance(coord, (list, tuple)) and len(coord) == 2:
                original_x, original_y = self._scaling_info.to_original_coords(
                    coord[0], coord[1]
                )
                tool_input["coordinate"] = [original_x, original_y]
                # 디버깅용 로그
                print(f"[Scaling] Coordinate: {coord} → [{original_x}, {original_y}]")

        # 실행
        result = self.executor.execute(tool_name, tool_input)

        # tool_result 형식으로 반환
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": self._format_tool_result(tool_name, result),
        }

    def _format_tool_result(self, tool_name: str, result: Dict) -> Any:
        """Tool 결과 포맷팅"""
        if tool_name == "computer" and result.get("action") == "screenshot":
            # 스크린샷은 이미지로 반환
            if result.get("success") and result.get("base64_data"):
                return [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": result.get("base64_data"),
                        },
                    }
                ]

        # 나머지는 텍스트로
        if result.get("success"):
            return result.get("output", "Action completed")
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    def reset(self):
        """상태 초기화"""
        self.fsm.reset()
        self._messages = []
        self._scaling_info = None


# CLI 테스트
async def main():
    """테스트"""
    agent = ComputerUseAgent(dry_run=True)

    print("=== Computer Use Agent Test (Dry Run) ===")
    result = await agent.run("스크린샷 찍어줘")
    print(f"Result: {result.to_dict()}")


if __name__ == "__main__":
    asyncio.run(main())

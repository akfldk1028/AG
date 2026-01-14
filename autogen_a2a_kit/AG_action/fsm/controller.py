"""
FSM Controller
===============

Computer Use Actions의 FSM 컨트롤러.

사용법:
    controller = FSMController()

    # 사용자 요청 시작
    await controller.start("Chrome에서 구글 검색해줘")

    # 상태 확인
    print(controller.state.current)  # State.SCREENSHOT

    # 스크린샷 완료 후
    await controller.on_screenshot_taken(screenshot_data)

    # 분석 결과로 액션 실행
    await controller.on_action_decided("left_click", {"coordinate": [150, 300]})
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field

from .states import State, FSMState
from .transitions import Event, TransitionTable


@dataclass
class ActionRequest:
    """액션 요청"""
    action_type: str  # screenshot, left_click, type, key, etc.
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action_type,
            **self.params,
        }


class FSMController:
    """
    FSM Controller

    Computer Use 액션의 상태 관리.
    """

    def __init__(self):
        self.state = FSMState()
        self.transitions = TransitionTable()
        self._action_queue: List[ActionRequest] = []
        self._listeners: Dict[str, List[Callable]] = {}
        self._max_iterations = 20  # 무한 루프 방지
        self._current_iteration = 0

    # ========================================
    # Event Handlers
    # ========================================

    async def start(self, user_request: str) -> bool:
        """사용자 요청으로 시작"""
        if not self.state.is_idle:
            return False

        self._current_iteration = 0

        success = self.transitions.fire(
            Event.USER_REQUEST,
            self.state,
            {"user_request": user_request}
        )

        if success:
            await self._emit("state_changed", self.state)
            await self._emit("start", {"request": user_request})

        return success

    async def on_screenshot_taken(self, screenshot: bytes, metadata: Dict = None) -> bool:
        """스크린샷 촬영 완료"""
        if self.state.current != State.SCREENSHOT:
            return False

        success = self.transitions.fire(
            Event.SCREENSHOT_TAKEN,
            self.state,
            {
                "screenshot": screenshot,
                "screenshot_metadata": metadata or {},
            }
        )

        if success:
            await self._emit("state_changed", self.state)
            await self._emit("screenshot_ready", {"screenshot": screenshot})

        return success

    async def on_action_decided(
        self,
        action_type: str,
        params: Dict[str, Any] = None
    ) -> bool:
        """액션 결정됨 (LLM 분석 결과)"""
        if self.state.current != State.ANALYZE:
            return False

        request = ActionRequest(action_type, params or {})
        self._action_queue.append(request)

        success = self.transitions.fire(
            Event.ACTION_DECIDED,
            self.state,
            {"action_request": request.to_dict()}
        )

        if success:
            await self._emit("state_changed", self.state)
            await self._emit("action_ready", request.to_dict())

        return success

    async def on_action_done(self, result: Dict[str, Any] = None) -> bool:
        """액션 실행 완료"""
        if self.state.current != State.ACTION:
            return False

        success = self.transitions.fire(
            Event.ACTION_DONE,
            self.state,
            {"action_result": result or {}}
        )

        if success:
            self._current_iteration += 1
            await self._emit("state_changed", self.state)
            await self._emit("action_complete", result)

        return success

    async def on_verify_result(self, is_complete: bool, reason: str = "") -> bool:
        """검증 결과"""
        if self.state.current != State.VERIFY:
            return False

        # 무한 루프 방지
        if self._current_iteration >= self._max_iterations:
            return await self.complete(f"Max iterations ({self._max_iterations}) reached")

        if is_complete:
            return await self.complete(reason)
        else:
            return await self.need_more(reason)

    async def need_more(self, reason: str = "") -> bool:
        """추가 작업 필요 → ANALYZE로 돌아감"""
        if self.state.current != State.VERIFY:
            return False

        success = self.transitions.fire(
            Event.NEED_MORE,
            self.state,
            {"reason": reason}
        )

        if success:
            await self._emit("state_changed", self.state)
            await self._emit("need_more", {"reason": reason})

        return success

    async def complete(self, result: str = "") -> bool:
        """작업 완료"""
        if self.state.current not in {State.VERIFY, State.ANALYZE}:
            return False

        success = self.transitions.fire(
            Event.TASK_COMPLETE,
            self.state,
            {"final_result": result}
        )

        if success:
            await self._emit("state_changed", self.state)
            await self._emit("complete", {
                "result": result,
                "iterations": self._current_iteration,
                "history": self.state.history,
            })

        return success

    async def error(self, error_msg: str) -> bool:
        """에러 발생"""
        success = self.transitions.fire(
            Event.ERROR,
            self.state,
            {"error": error_msg}
        )

        if success:
            self.state.error = error_msg
            await self._emit("state_changed", self.state)
            await self._emit("error", {"error": error_msg})

        return success

    async def recover(self) -> bool:
        """에러/완료에서 복구"""
        if self.state.current not in {State.ERROR, State.COMPLETE}:
            return False

        success = self.transitions.fire(
            Event.RECOVER,
            self.state,
        )

        if success:
            self.state.error = None
            await self._emit("state_changed", self.state)
            await self._emit("recovered", {})

        return success

    def reset(self):
        """완전 초기화"""
        self.state.reset()
        self._action_queue.clear()
        self._current_iteration = 0

    # ========================================
    # Utility Methods
    # ========================================

    def get_next_action(self) -> Optional[ActionRequest]:
        """다음 실행할 액션"""
        if self._action_queue:
            return self._action_queue.pop(0)
        return None

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            "state": self.state.to_dict(),
            "iteration": self._current_iteration,
            "max_iterations": self._max_iterations,
            "pending_actions": len(self._action_queue),
        }

    # ========================================
    # Event System
    # ========================================

    def on(self, event: str, callback: Callable):
        """이벤트 리스너 등록"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable = None):
        """이벤트 리스너 제거"""
        if event not in self._listeners:
            return
        if callback:
            self._listeners[event] = [
                cb for cb in self._listeners[event] if cb != callback
            ]
        else:
            self._listeners[event] = []

    async def _emit(self, event: str, data: Any):
        """이벤트 발생"""
        if event not in self._listeners:
            return

        for callback in self._listeners[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                print(f"[FSM] Event handler error: {e}")

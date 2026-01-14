"""
Computer Use Executor
======================

모든 Computer Use Action을 통합 실행.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from enum import Enum

from .mouse import MouseActions, MouseAction
from .keyboard import KeyboardActions, KeyboardAction
from .screen import ScreenActions, ScreenAction


class ActionType(Enum):
    """Computer Use Action 타입"""
    # Screen
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    ZOOM = "zoom"

    # Mouse
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    TRIPLE_CLICK = "triple_click"
    MOUSE_MOVE = "mouse_move"
    SCROLL = "scroll"
    LEFT_CLICK_DRAG = "left_click_drag"
    LEFT_MOUSE_DOWN = "left_mouse_down"
    LEFT_MOUSE_UP = "left_mouse_up"

    # Keyboard
    TYPE = "type"
    KEY = "key"
    HOLD_KEY = "hold_key"


@dataclass
class ExecutionResult:
    """실행 결과"""
    action_type: str
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action_type,
            "success": self.success,
            "result": self.result,
            "error": self.error,
        }


class ComputerUseExecutor:
    """
    Computer Use Action Executor

    Claude Computer Use API의 모든 액션을 실행.

    사용법:
        executor = ComputerUseExecutor()

        # 스크린샷
        result = executor.execute("screenshot")

        # 클릭
        result = executor.execute("left_click", coordinate=[150, 300])

        # 텍스트 입력
        result = executor.execute("type", text="Hello World")
    """

    def __init__(self, dry_run: bool = False):
        """
        Args:
            dry_run: True면 실제 실행 없이 로그만
        """
        self.dry_run = dry_run
        self.mouse = MouseActions(dry_run)
        self.keyboard = KeyboardActions(dry_run)
        self.screen = ScreenActions(dry_run)

    def execute(self, action: str, **params) -> ExecutionResult:
        """
        Action 실행

        Args:
            action: 액션 타입 (screenshot, left_click, type, etc.)
            **params: 액션 파라미터

        Returns:
            ExecutionResult
        """
        try:
            action_type = ActionType(action)
        except ValueError:
            return ExecutionResult(
                action,
                False,
                {},
                f"Unknown action: {action}"
            )

        try:
            result = self._dispatch(action_type, params)
            return ExecutionResult(
                action,
                result.success if hasattr(result, 'success') else True,
                result.to_dict() if hasattr(result, 'to_dict') else {"data": result},
                result.error if hasattr(result, 'error') else None,
            )
        except Exception as e:
            return ExecutionResult(action, False, {}, str(e))

    def _dispatch(self, action_type: ActionType, params: Dict[str, Any]):
        """액션 디스패치"""

        # Screen Actions
        if action_type == ActionType.SCREENSHOT:
            region = params.get("region")
            return self.screen.screenshot(region)

        elif action_type == ActionType.WAIT:
            seconds = params.get("seconds", 1.0)
            return self.screen.wait(seconds)

        elif action_type == ActionType.ZOOM:
            region = params.get("region")
            return self.screen.zoom(region)

        # Mouse Actions
        elif action_type == ActionType.LEFT_CLICK:
            coord = self._get_coordinate(params)
            return self.mouse.left_click(coord)

        elif action_type == ActionType.RIGHT_CLICK:
            coord = self._get_coordinate(params)
            return self.mouse.right_click(coord)

        elif action_type == ActionType.MIDDLE_CLICK:
            coord = self._get_coordinate(params)
            return self.mouse.middle_click(coord)

        elif action_type == ActionType.DOUBLE_CLICK:
            coord = self._get_coordinate(params)
            return self.mouse.double_click(coord)

        elif action_type == ActionType.TRIPLE_CLICK:
            coord = self._get_coordinate(params)
            return self.mouse.triple_click(coord)

        elif action_type == ActionType.MOUSE_MOVE:
            coord = self._get_coordinate(params)
            return self.mouse.mouse_move(coord)

        elif action_type == ActionType.SCROLL:
            coord = self._get_coordinate(params)
            delta_x = params.get("delta_x", 0)
            delta_y = params.get("delta_y", 0)
            return self.mouse.scroll(coord, delta_x, delta_y)

        elif action_type == ActionType.LEFT_CLICK_DRAG:
            start = tuple(params.get("start_coordinate", [0, 0]))
            end = tuple(params.get("end_coordinate", [0, 0]))
            return self.mouse.left_click_drag(start, end)

        elif action_type == ActionType.LEFT_MOUSE_DOWN:
            coord = self._get_coordinate(params)
            return self.mouse.left_mouse_down(coord)

        elif action_type == ActionType.LEFT_MOUSE_UP:
            coord = self._get_coordinate(params)
            return self.mouse.left_mouse_up(coord)

        # Keyboard Actions
        elif action_type == ActionType.TYPE:
            text = params.get("text", "")
            return self.keyboard.type(text)

        elif action_type == ActionType.KEY:
            key = params.get("key", "")
            return self.keyboard.key(key)

        elif action_type == ActionType.HOLD_KEY:
            key = params.get("key", "")
            duration = params.get("duration", 1.0)
            return self.keyboard.hold_key(key, duration)

        else:
            raise ValueError(f"Unhandled action: {action_type}")

    def _get_coordinate(self, params: Dict[str, Any]) -> Tuple[int, int]:
        """좌표 추출"""
        coord = params.get("coordinate", [0, 0])
        if isinstance(coord, (list, tuple)) and len(coord) >= 2:
            return (int(coord[0]), int(coord[1]))
        return (0, 0)

    # ========================================
    # 편의 메서드
    # ========================================

    def screenshot(self) -> ExecutionResult:
        """스크린샷"""
        return self.execute("screenshot")

    def click(self, x: int, y: int) -> ExecutionResult:
        """클릭"""
        return self.execute("left_click", coordinate=[x, y])

    def type_text(self, text: str) -> ExecutionResult:
        """텍스트 입력"""
        return self.execute("type", text=text)

    def press_key(self, key: str) -> ExecutionResult:
        """키 입력"""
        return self.execute("key", key=key)

    def wait(self, seconds: float = 1.0) -> ExecutionResult:
        """대기"""
        return self.execute("wait", seconds=seconds)

    def get_screen_size(self) -> Tuple[int, int]:
        """화면 크기"""
        return self.screen.get_screen_size()

"""
Mouse Actions
==============

Computer Use API의 마우스 관련 Action.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from enum import Enum


class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class MouseAction:
    """마우스 액션 결과"""
    action: str
    coordinate: Tuple[int, int]
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "coordinate": list(self.coordinate),
            "success": self.success,
            "error": self.error,
        }


class MouseActions:
    """
    Mouse Action Primitives

    Claude Computer Use API의 마우스 액션들.
    실제 구현은 pyautogui 또는 플랫폼별 API 사용.
    """

    def __init__(self, dry_run: bool = False):
        """
        Args:
            dry_run: True면 실제 실행 없이 로그만
        """
        self.dry_run = dry_run
        self._gui = None
        self._init_gui()

    def _init_gui(self):
        """GUI 라이브러리 초기화"""
        if self.dry_run:
            return

        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # 코너로 마우스 이동시 중지
            pyautogui.PAUSE = 0.1  # 액션 간 딜레이
            self._gui = pyautogui
        except ImportError:
            print("[MouseActions] pyautogui not installed. Running in dry_run mode.")
            self.dry_run = True

    def left_click(self, coordinate: Tuple[int, int]) -> MouseAction:
        """왼쪽 클릭"""
        return self._click(coordinate, MouseButton.LEFT)

    def right_click(self, coordinate: Tuple[int, int]) -> MouseAction:
        """오른쪽 클릭"""
        return self._click(coordinate, MouseButton.RIGHT)

    def middle_click(self, coordinate: Tuple[int, int]) -> MouseAction:
        """중간 클릭"""
        return self._click(coordinate, MouseButton.MIDDLE)

    def double_click(self, coordinate: Tuple[int, int]) -> MouseAction:
        """더블 클릭"""
        x, y = coordinate
        action_name = "double_click"

        if self.dry_run:
            print(f"[DRY_RUN] double_click at ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.doubleClick(x, y)
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def triple_click(self, coordinate: Tuple[int, int]) -> MouseAction:
        """트리플 클릭"""
        x, y = coordinate
        action_name = "triple_click"

        if self.dry_run:
            print(f"[DRY_RUN] triple_click at ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.tripleClick(x, y)
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def mouse_move(self, coordinate: Tuple[int, int]) -> MouseAction:
        """마우스 이동"""
        x, y = coordinate
        action_name = "mouse_move"

        if self.dry_run:
            print(f"[DRY_RUN] mouse_move to ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.moveTo(x, y)
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def scroll(
        self,
        coordinate: Tuple[int, int],
        delta_x: int = 0,
        delta_y: int = 0
    ) -> MouseAction:
        """스크롤"""
        x, y = coordinate
        action_name = "scroll"

        if self.dry_run:
            print(f"[DRY_RUN] scroll at ({x}, {y}) delta=({delta_x}, {delta_y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.moveTo(x, y)
            # pyautogui는 vertical scroll만 지원
            if delta_y != 0:
                self._gui.scroll(delta_y)
            # horizontal scroll은 플랫폼별 처리 필요
            if delta_x != 0:
                self._gui.hscroll(delta_x)
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def left_click_drag(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ) -> MouseAction:
        """드래그"""
        action_name = "left_click_drag"

        if self.dry_run:
            print(f"[DRY_RUN] drag from {start} to {end}")
            return MouseAction(action_name, start, True)

        try:
            self._gui.moveTo(start[0], start[1])
            self._gui.drag(
                end[0] - start[0],
                end[1] - start[1],
                duration=0.5
            )
            return MouseAction(action_name, end, True)
        except Exception as e:
            return MouseAction(action_name, start, False, str(e))

    def left_mouse_down(self, coordinate: Tuple[int, int]) -> MouseAction:
        """마우스 버튼 누르기"""
        x, y = coordinate
        action_name = "left_mouse_down"

        if self.dry_run:
            print(f"[DRY_RUN] mouse_down at ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.moveTo(x, y)
            self._gui.mouseDown()
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def left_mouse_up(self, coordinate: Tuple[int, int]) -> MouseAction:
        """마우스 버튼 떼기"""
        x, y = coordinate
        action_name = "left_mouse_up"

        if self.dry_run:
            print(f"[DRY_RUN] mouse_up at ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.moveTo(x, y)
            self._gui.mouseUp()
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

    def _click(
        self,
        coordinate: Tuple[int, int],
        button: MouseButton
    ) -> MouseAction:
        """클릭 공통 로직"""
        x, y = coordinate
        action_name = f"{button.value}_click"

        if self.dry_run:
            print(f"[DRY_RUN] {action_name} at ({x}, {y})")
            return MouseAction(action_name, coordinate, True)

        try:
            self._gui.click(x, y, button=button.value)
            return MouseAction(action_name, coordinate, True)
        except Exception as e:
            return MouseAction(action_name, coordinate, False, str(e))

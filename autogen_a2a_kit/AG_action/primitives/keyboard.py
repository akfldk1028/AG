"""
Keyboard Actions
=================

Computer Use API의 키보드 관련 Action.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time


@dataclass
class KeyboardAction:
    """키보드 액션 결과"""
    action: str
    value: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "value": self.value,
            "success": self.success,
            "error": self.error,
        }


class KeyboardActions:
    """
    Keyboard Action Primitives

    Claude Computer Use API의 키보드 액션들.
    """

    # 특수 키 매핑 (Computer Use API → pyautogui)
    KEY_MAP = {
        "Return": "enter",
        "Escape": "escape",
        "Tab": "tab",
        "Backspace": "backspace",
        "Delete": "delete",
        "Up": "up",
        "Down": "down",
        "Left": "left",
        "Right": "right",
        "Home": "home",
        "End": "end",
        "Page_Up": "pageup",
        "Page_Down": "pagedown",
        "space": "space",
        "Control_L": "ctrl",
        "Control_R": "ctrl",
        "Alt_L": "alt",
        "Alt_R": "alt",
        "Shift_L": "shift",
        "Shift_R": "shift",
        "Super_L": "win",
        "Super_R": "win",
        "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4",
        "F5": "f5", "F6": "f6", "F7": "f7", "F8": "f8",
        "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
    }

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._gui = None
        self._init_gui()

    def _init_gui(self):
        """GUI 라이브러리 초기화"""
        if self.dry_run:
            return

        try:
            import pyautogui
            self._gui = pyautogui
        except ImportError:
            print("[KeyboardActions] pyautogui not installed. Running in dry_run mode.")
            self.dry_run = True

    def type(self, text: str) -> KeyboardAction:
        """
        텍스트 입력

        Args:
            text: 입력할 텍스트

        Note:
            Computer Use API에서는 한 번에 한 글자씩 입력하기도 하고,
            여러 글자를 한꺼번에 입력하기도 함.
        """
        action_name = "type"

        if self.dry_run:
            print(f"[DRY_RUN] type: '{text}'")
            return KeyboardAction(action_name, text, True)

        try:
            # typewrite는 영문만 지원, write는 다국어 지원
            self._gui.write(text, interval=0.02)
            return KeyboardAction(action_name, text, True)
        except Exception as e:
            return KeyboardAction(action_name, text, False, str(e))

    def key(self, key: str) -> KeyboardAction:
        """
        특수 키 입력

        Args:
            key: 키 이름 (예: "Return", "Escape", "ctrl+c")

        Note:
            조합키는 "ctrl+c", "shift+Tab" 형식으로 입력
        """
        action_name = "key"

        if self.dry_run:
            print(f"[DRY_RUN] key: '{key}'")
            return KeyboardAction(action_name, key, True)

        try:
            # 조합키 처리 (예: ctrl+c, shift+Tab)
            if "+" in key:
                keys = key.split("+")
                mapped_keys = [self._map_key(k.strip()) for k in keys]
                self._gui.hotkey(*mapped_keys)
            else:
                mapped_key = self._map_key(key)
                self._gui.press(mapped_key)

            return KeyboardAction(action_name, key, True)
        except Exception as e:
            return KeyboardAction(action_name, key, False, str(e))

    def hold_key(self, key: str, duration: float = 1.0) -> KeyboardAction:
        """
        키를 누른 상태로 유지

        Args:
            key: 키 이름
            duration: 유지 시간 (초)
        """
        action_name = "hold_key"

        if self.dry_run:
            print(f"[DRY_RUN] hold_key: '{key}' for {duration}s")
            return KeyboardAction(action_name, key, True)

        try:
            mapped_key = self._map_key(key)
            self._gui.keyDown(mapped_key)
            time.sleep(duration)
            self._gui.keyUp(mapped_key)
            return KeyboardAction(action_name, key, True)
        except Exception as e:
            return KeyboardAction(action_name, key, False, str(e))

    def hotkey(self, *keys: str) -> KeyboardAction:
        """
        조합키 입력

        Args:
            keys: 키들 (예: "ctrl", "c")
        """
        action_name = "hotkey"
        key_str = "+".join(keys)

        if self.dry_run:
            print(f"[DRY_RUN] hotkey: '{key_str}'")
            return KeyboardAction(action_name, key_str, True)

        try:
            mapped_keys = [self._map_key(k) for k in keys]
            self._gui.hotkey(*mapped_keys)
            return KeyboardAction(action_name, key_str, True)
        except Exception as e:
            return KeyboardAction(action_name, key_str, False, str(e))

    def _map_key(self, key: str) -> str:
        """Computer Use API 키 이름 → pyautogui 키 이름"""
        return self.KEY_MAP.get(key, key.lower())

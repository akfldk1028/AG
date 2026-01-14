"""
Computer Use Primitives
========================

Claude Computer Use API의 Action primitives.

Actions:
- Mouse: left_click, right_click, double_click, mouse_move, scroll, drag
- Keyboard: type, key
- Screen: screenshot, wait, screenshot_scaled

Features:
- Resolution Scaling (XGA/WXGA)
- Coordinate transformation
"""

from .mouse import MouseActions
from .keyboard import KeyboardActions
from .screen import ScreenActions, ScalingTarget, ScalingInfo
from .executor import ComputerUseExecutor

__all__ = [
    "MouseActions",
    "KeyboardActions",
    "ScreenActions",
    "ScalingTarget",
    "ScalingInfo",
    "ComputerUseExecutor",
]

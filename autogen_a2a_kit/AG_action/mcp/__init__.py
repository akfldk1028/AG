"""
AG_action MCP Server
=====================

Model Context Protocol 기반 Action Server.

Tools:
- computer: Computer Use 액션 실행
- fsm_control: FSM 상태 관리

Resources:
- fsm://state: 현재 FSM 상태
- screenshot://latest: 최신 스크린샷
"""

from .server import ActionMCPServer
from .handlers import ComputerToolHandler, FSMResourceHandler

__all__ = [
    "ActionMCPServer",
    "ComputerToolHandler",
    "FSMResourceHandler",
]

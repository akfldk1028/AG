# AG-CLI Studio Integration
"""
AutoGen Studio와 AG-CLI 통합 모듈

- cli_agent.py: CollaborativeAgent를 A2A 프로토콜로 노출
- websocket_bridge.py: Message Bus 대화를 WebSocket으로 중계
"""
from pathlib import Path

__version__ = "0.1.0"
__all__ = ["CLIAgent", "create_cli_a2a_agent"]

# AG-CLI MCP Servers
"""
MCP (Model Context Protocol) 서버들

- message_bus.py: 에이전트 간 대화 라우팅
- shared_memory.py: 정보 공유 및 이벤트 발행
- autogen_studio_server.py: AutoGen Studio API + WS 실행을 MCP 도구로 노출
"""
from pathlib import Path

__version__ = "0.2.0"
__all__ = ["message_bus", "shared_memory", "autogen_studio_server"]

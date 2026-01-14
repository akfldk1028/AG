"""
Computer Use - Claude API 직접 연동
====================================

MCP 없이 Claude API를 직접 호출하여 Computer Use 실행.

Features:
- FSM 기반 상태 관리
- Prompt Caching 지원
- Image Truncation 지원
- Callback 시스템

Usage:
    from computer_use import ComputerUseAgent, AgentCallbacks

    # 기본 사용
    agent = ComputerUseAgent()
    result = await agent.run("Chrome에서 구글 검색해줘")

    # 콜백과 함께 사용
    callbacks = AgentCallbacks(
        on_tool_start=lambda name, input: print(f"Tool: {name}"),
        on_screenshot=lambda data: save_screenshot(data),
    )
    agent = ComputerUseAgent(callbacks=callbacks)
"""

from .agent_loop import ComputerUseAgent, AgentCallbacks, AgentResult
from .tool_executor import ToolExecutor

__all__ = [
    "ComputerUseAgent",
    "AgentCallbacks",
    "AgentResult",
    "ToolExecutor",
]

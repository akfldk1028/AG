"""
AG_action - Computer Use Action Module
=======================================

Claude Computer Use API 기반 컴퓨터 제어 모듈.

Modules:
- computer_use: Claude API 직접 연동 (핵심!)
- primitives: 로컬 실행 (pyautogui)
- fsm: 상태 관리
- registry: Direct Action 레지스트리
- agents: A2A Agent
- mcp: 외부 도구 연동 (선택)

Quick Start:
    from AG_action import ComputerUseAgent

    agent = ComputerUseAgent()
    result = await agent.run("Chrome에서 구글 검색해줘")

Architecture:
    ┌─────────────────────────────────────────┐
    │            ComputerUseAgent             │
    │         (computer_use/agent_loop.py)    │
    ├─────────────────────────────────────────┤
    │  Claude API  │  FSM Controller  │ Tools │
    │   (Direct)   │   (fsm/)         │       │
    ├──────────────┴──────────────────┴───────┤
    │              ToolExecutor               │
    │       (computer_use/tool_executor.py)   │
    ├─────────────────────────────────────────┤
    │             Primitives                  │
    │    (mouse, keyboard, screen, bash)      │
    └─────────────────────────────────────────┘
"""

# Core - Computer Use (Claude API Direct)
from .computer_use import (
    ComputerUseAgent,
    AgentCallbacks,
    AgentResult,
    ToolExecutor,
)

# FSM
from .fsm import (
    FSMController,
    State,
    Event,
)

# Primitives
from .primitives import (
    ComputerUseExecutor,
    MouseActions,
    KeyboardActions,
    ScreenActions,
    ScalingTarget,
    ScalingInfo,
)

# Registry
from .registry import (
    ActionRegistry,
    Action,
    ActionParam,
    ActionExecution,
    ExecutionType,
)

# Agents
from .agents import (
    ActionExecutor,
)

# Schema Validation (선택)
try:
    from .schemas import validate_action
except ImportError:
    validate_action = None

__version__ = "0.5.0"  # Phase 6: AutoGen Studio Gallery 연동
__all__ = [
    # Core
    "ComputerUseAgent",
    "AgentCallbacks",
    "AgentResult",
    "ToolExecutor",
    # FSM
    "FSMController",
    "State",
    "Event",
    # Primitives
    "ComputerUseExecutor",
    "MouseActions",
    "KeyboardActions",
    "ScreenActions",
    "ScalingTarget",
    "ScalingInfo",
    # Registry
    "ActionRegistry",
    "Action",
    "ActionParam",
    "ActionExecution",
    "ExecutionType",
    # Agents
    "ActionExecutor",
    # Schema
    "validate_action",
]

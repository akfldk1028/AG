"""
AG_action Integration Module for AutoGen Studio
================================================

이 모듈은 AG_action (Computer Use + Direct Action)을 AutoGen Studio에 연동합니다.

Architecture:
    AG_action (원본)          →  ag_action (어댑터)  →  AutoGen Studio
    ├── computer_use/             ├── tools.py            ├── gallery/builder.py
    ├── primitives/               └── __init__.py         └── Gallery UI
    ├── registry/
    └── actions/

Key Principles:
    1. AG_action 원본 코드는 건드리지 않음
    2. 이 모듈은 "어댑터" 역할만 수행
    3. AutoGen의 FunctionTool 형식으로 변환

Usage in builder.py:
    from autogenstudio.ag_action import (
        AG_ACTION_AVAILABLE,
        execute_action_tool,
        list_actions_tool,
    )

    if AG_ACTION_AVAILABLE:
        builder.add_tool(execute_action_tool.dump_component(), ...)

Version: 0.5.0
"""

import sys
import os
from pathlib import Path

# AG_action 경로 추가
# 방법 1: 환경변수 (가장 확실)
# 방법 2: 상위 디렉토리 탐색
# 방법 3: 하드코딩 경로 (개발용)

_ag_action_parent = None

def _is_real_ag_action(path: Path) -> bool:
    """진짜 AG_action 모듈인지 확인 (registry, computer_use 폴더 존재 여부)"""
    return (
        (path / "__init__.py").exists() and
        (path / "registry").exists() and
        (path / "computer_use").exists()
    )

# 방법 1: 환경변수
if os.environ.get("AG_ACTION_PATH"):
    _env_path = Path(os.environ["AG_ACTION_PATH"])
    if _is_real_ag_action(_env_path):
        _ag_action_parent = _env_path.parent
        sys.path.insert(0, str(_ag_action_parent))

# 방법 2: 상위 디렉토리 탐색 (AG_action 폴더 찾기)
if not _ag_action_parent:
    _search_dir = Path(__file__).resolve().parent
    for _ in range(15):  # 최대 15단계 상위까지 탐색
        _search_dir = _search_dir.parent
        _candidate = _search_dir / "AG_action"
        if _candidate.exists() and _is_real_ag_action(_candidate):
            _ag_action_parent = _search_dir
            sys.path.insert(0, str(_ag_action_parent))
            break

# 방법 3: 하드코딩 경로 (개발용 fallback)
if not _ag_action_parent:
    _hardcoded_paths = [
        Path("D:/Data/22_AG/autogen_a2a_kit"),
        Path.home() / "autogen_a2a_kit",
    ]
    for _path in _hardcoded_paths:
        if _is_real_ag_action(_path / "AG_action"):
            _ag_action_parent = _path
            sys.path.insert(0, str(_ag_action_parent))
            break

# AG_action 가용성 플래그
AG_ACTION_AVAILABLE = False
AG_ACTION_ERROR = None

try:
    from AG_action import (
        ActionRegistry,
        Action,
        ActionParam,
        ActionExecution,
        ExecutionType,
    )
    AG_ACTION_AVAILABLE = True
except ImportError as e:
    AG_ACTION_ERROR = str(e)
    # Graceful degradation - 에러 시에도 모듈은 로드됨
    ActionRegistry = None
    Action = None
    ActionParam = None
    ActionExecution = None
    ExecutionType = None

# Tools export (AG_action 사용 가능할 때만)
from .tools import (
    execute_action_tool,
    list_actions_tool,
    get_action_info_tool,
    create_ag_action_agent,
)

__version__ = "0.5.0"
__all__ = [
    # Availability
    "AG_ACTION_AVAILABLE",
    "AG_ACTION_ERROR",
    # Tools
    "execute_action_tool",
    "list_actions_tool",
    "get_action_info_tool",
    # Agent Factory
    "create_ag_action_agent",
    # Re-exports (if available)
    "ActionRegistry",
    "Action",
    "ActionParam",
    "ActionExecution",
    "ExecutionType",
]

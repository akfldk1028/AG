"""
AG_action Tools for AutoGen Studio
====================================

AG_action의 Direct Action을 AutoGen FunctionTool로 변환.

이 파일의 함수들은 builder.py에서 Gallery에 등록됩니다:
- execute_action: Direct Action 실행
- list_actions: Action 목록 조회
- get_action_info: Action 상세 정보

Production 원칙:
- #2: Direct Function Calls - 비추론 작업은 LLM 없이 직접 실행
- #7: Workflow와 MCP 분리 - Action은 독립 모듈로 관리
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

from autogen_core.tools import FunctionTool

# AG_action 경로 설정 (상위 디렉토리 탐색)
# 주의: Windows는 대소문자 구분 안함, ag_action vs AG_action 구분 필요
_ag_action_parent = None
_search_dir = Path(__file__).resolve().parent

def _is_real_ag_action(path: Path) -> bool:
    """진짜 AG_action 모듈인지 확인 (registry, computer_use 폴더 존재 여부)"""
    return (
        (path / "__init__.py").exists() and
        (path / "registry").exists() and
        (path / "computer_use").exists()
    )

for _ in range(15):
    _search_dir = _search_dir.parent
    _candidate = _search_dir / "AG_action"
    if _candidate.exists() and _is_real_ag_action(_candidate):
        _ag_action_parent = _search_dir
        if str(_ag_action_parent) not in sys.path:
            sys.path.insert(0, str(_ag_action_parent))
        break

# Fallback: 하드코딩 경로 (개발용)
if not _ag_action_parent:
    _hardcoded = Path("D:/Data/22_AG/autogen_a2a_kit")
    if _is_real_ag_action(_hardcoded / "AG_action"):
        _ag_action_parent = _hardcoded
        sys.path.insert(0, str(_hardcoded))

# AG_action import 시도
_AG_ACTION_AVAILABLE = False
_ActionRegistry = None
_ActionExecutor = None

try:
    from AG_action import ActionRegistry, ActionExecutor
    _AG_ACTION_AVAILABLE = True
    _ActionRegistry = ActionRegistry
    _ActionExecutor = ActionExecutor
except ImportError:
    pass


# ==============================================================================
# Tool Functions (AutoGen에서 호출)
# ==============================================================================

def execute_action(
    action_name: str,
    params: Optional[Dict[str, Any]] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Direct Action 실행 (빌드, 테스트, 배포 등)

    AG_action의 ActionExecutor를 사용하여 YAML에 정의된 액션을 실행합니다.
    LLM 없이 subprocess로 직접 실행되어 빠르고 결정론적입니다.

    Args:
        action_name: 실행할 Action 이름 (예: "frontend_build", "unit_test", "eslint")
        params: 액션 파라미터 (옵션)
        project_root: 프로젝트 루트 경로 (옵션, 기본값: 현재 작업 디렉토리)

    Returns:
        실행 결과:
        - status: "success" | "failure" | "timeout" | "skipped"
        - action_name: 실행된 액션 이름
        - stdout: 표준 출력
        - stderr: 표준 에러
        - return_code: 종료 코드
        - duration: 실행 시간 (초)

    Example:
        >>> execute_action("frontend_build")
        {"status": "success", "stdout": "Build completed", ...}

        >>> execute_action("unit_test", {"coverage": True})
        {"status": "success", "stdout": "All tests passed", ...}
    """
    if not _AG_ACTION_AVAILABLE:
        return {
            "status": "failure",
            "action_name": action_name,
            "stderr": "AG_action module not available. Install AG_action first.",
            "return_code": -1,
        }

    try:
        executor = _ActionExecutor(project_root=project_root)

        # asyncio 이벤트 루프 처리
        try:
            loop = asyncio.get_running_loop()
            # 이미 이벤트 루프가 실행 중이면 새 태스크로 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = loop.run_in_executor(
                    pool,
                    lambda: asyncio.run(executor.execute(action_name, params))
                )
                # 동기적으로 대기
                result = asyncio.get_event_loop().run_until_complete(result)
        except RuntimeError:
            # 이벤트 루프가 없으면 새로 생성
            result = asyncio.run(executor.execute(action_name, params))

        return result.to_dict()

    except Exception as e:
        return {
            "status": "failure",
            "action_name": action_name,
            "stderr": f"Execution error: {str(e)}",
            "return_code": -1,
        }


def list_actions(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    사용 가능한 Direct Action 목록 조회

    AG_action에 등록된 모든 액션 목록을 반환합니다.
    카테고리별 필터링이 가능합니다.

    Args:
        category: 필터링할 카테고리 (옵션)
            - "build": 빌드 액션 (frontend_build, backend_build, docker_build)
            - "test": 테스트 액션 (unit_test, e2e_test)
            - "lint": 린트 액션 (eslint, prettier)
            - "git": Git 액션 (commit, push)
            - None: 모든 액션

    Returns:
        Action 목록:
        - name: 액션 이름
        - category: 카테고리
        - description: 설명
        - triggers: 트리거 키워드

    Example:
        >>> list_actions()
        [{"name": "frontend_build", "category": "build", ...}, ...]

        >>> list_actions("test")
        [{"name": "unit_test", "category": "test", ...}]
    """
    if not _AG_ACTION_AVAILABLE:
        return [{
            "error": "AG_action module not available",
            "available_categories": ["build", "test", "lint", "git", "deploy"],
        }]

    try:
        registry = _ActionRegistry.get_instance()
        actions = registry.list(category)
        return actions
    except Exception as e:
        return [{"error": f"Failed to list actions: {str(e)}"}]


def get_action_info(action_name: str) -> Dict[str, Any]:
    """
    특정 Action의 상세 정보 조회

    Args:
        action_name: Action 이름

    Returns:
        Action 상세 정보:
        - name, category, description
        - execution: 실행 설정 (type, commands, timeout)
        - params: 파라미터 목록
        - triggers: 트리거 키워드

    Example:
        >>> get_action_info("frontend_build")
        {
            "name": "frontend_build",
            "category": "build",
            "execution": {"type": "direct", "commands": ["npm run build"]},
            ...
        }
    """
    if not _AG_ACTION_AVAILABLE:
        return {
            "error": "AG_action module not available",
            "action_name": action_name,
        }

    try:
        registry = _ActionRegistry.get_instance()
        action = registry.get(action_name, layer=2)  # Layer 2: execution info

        if not action:
            return {
                "error": f"Action not found: {action_name}",
                "available_actions": [a["name"] for a in registry.list()],
            }

        return action.to_dict(layer=2)
    except Exception as e:
        return {"error": f"Failed to get action info: {str(e)}"}


def get_registry_stats() -> Dict[str, Any]:
    """
    AG_action Registry 통계

    Returns:
        - total_actions: 총 액션 수
        - categories: 카테고리별 액션 수
        - total_triggers: 총 트리거 수
        - available: AG_action 사용 가능 여부
    """
    if not _AG_ACTION_AVAILABLE:
        return {
            "available": False,
            "error": "AG_action module not available",
        }

    try:
        registry = _ActionRegistry.get_instance()
        stats = registry.stats()
        stats["available"] = True
        return stats
    except Exception as e:
        return {
            "available": False,
            "error": f"Failed to get stats: {str(e)}",
        }


# ==============================================================================
# FunctionTool Instances (builder.py에서 사용)
# ==============================================================================

execute_action_tool = FunctionTool(
    execute_action,
    name="execute_action",
    description="Execute a Direct Action (build, test, lint, deploy) without LLM. Fast and deterministic.",
)

list_actions_tool = FunctionTool(
    list_actions,
    name="list_actions",
    description="List available Direct Actions. Filter by category: build, test, lint, git, deploy.",
)

get_action_info_tool = FunctionTool(
    get_action_info,
    name="get_action_info",
    description="Get detailed information about a specific Action including execution config and parameters.",
)


# ==============================================================================
# Agent Factory (builder.py에서 사용)
# ==============================================================================

def create_ag_action_agent(model_client):
    """
    AG_action Agent 생성

    Direct Action을 실행할 수 있는 AssistantAgent를 생성합니다.

    Args:
        model_client: AutoGen 모델 클라이언트

    Returns:
        AssistantAgent with AG_action tools
    """
    from autogen_agentchat.agents import AssistantAgent

    return AssistantAgent(
        name="action_agent",
        description="빌드, 테스트, 배포 등 Direct Action 실행 전문가",
        system_message="""당신은 Direct Action 실행 전문가입니다.

사용 가능한 도구:
1. list_actions - 사용 가능한 액션 목록 조회
2. get_action_info - 특정 액션의 상세 정보 조회
3. execute_action - 액션 실행

작업 순서:
1. 먼저 list_actions로 사용 가능한 액션을 확인하세요
2. 필요하면 get_action_info로 상세 정보를 확인하세요
3. execute_action으로 액션을 실행하세요

주의사항:
- Direct Action은 LLM 없이 직접 실행되어 빠르고 결정론적입니다
- 실행 전 파라미터가 올바른지 확인하세요
- 실패 시 stderr를 확인하고 원인을 파악하세요

완료 시 "TERMINATE"라고 말하세요.""",
        model_client=model_client,
        tools=[execute_action_tool, list_actions_tool, get_action_info_tool],
    )


# ==============================================================================
# 테스트
# ==============================================================================

if __name__ == "__main__":
    print("=== AG_action Tools Test ===")
    print(f"AG_ACTION_AVAILABLE: {_AG_ACTION_AVAILABLE}")
    print(f"AG_action parent: {_ag_action_parent}")
    print(f"sys.path[0]: {sys.path[0] if sys.path else 'empty'}")

    if _AG_ACTION_AVAILABLE:
        print("\n--- Registry Stats ---")
        print(get_registry_stats())

        print("\n--- Actions List ---")
        for action in list_actions():
            print(f"  - {action.get('name', 'N/A')}: {action.get('description', 'N/A')}")
    else:
        print("\nAG_action not available. Check the path.")

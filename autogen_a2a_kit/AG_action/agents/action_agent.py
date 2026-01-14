"""
AG_action A2A Agent
====================

AutoGen Studio와 연동되는 Action Agent.

Production 원칙:
- #3: Single Tool Per Agent - 도구 수 최소화
- #4: Single Responsibility - Action 실행만 담당
"""

import os
import sys
import asyncio
import argparse

# Google ADK
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# A2A Protocol
from google.adk.a2a import A2AServer

# 로컬 모듈
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
from registry import ActionRegistry, get_registry
from agents.executor import ActionExecutor, ExecutionResult


# ============================================
# Tool Functions (FunctionTool용)
# ============================================

def list_actions(category: str = None) -> dict:
    """
    사용 가능한 Action 목록 조회

    Args:
        category: 카테고리 필터 (build, test, lint, deploy, git 등)

    Returns:
        Action 목록
    """
    registry = get_registry()

    if category:
        actions = registry.list(category)
    else:
        actions = registry.list()

    return {
        "actions": actions,
        "categories": registry.categories(),
        "total": len(actions),
    }


def get_action_info(action_name: str) -> dict:
    """
    특정 Action의 상세 정보 조회

    Args:
        action_name: Action 이름 (예: frontend_build, unit_test)

    Returns:
        Action 상세 정보 (Layer 2까지)
    """
    registry = get_registry()
    action = registry.get(action_name, layer=2)

    if not action:
        return {"error": f"Action not found: {action_name}"}

    return action.to_dict(layer=2)


async def execute_action(action_name: str, params: dict = None) -> dict:
    """
    Action 실행

    Args:
        action_name: 실행할 Action 이름
        params: 파라미터 (옵션)

    Returns:
        실행 결과
    """
    executor = ActionExecutor()
    result = await executor.execute(action_name, params or {})
    return result.to_dict()


def execute_action_sync(action_name: str, params: dict = None) -> dict:
    """
    Action 실행 (동기 버전 - FunctionTool용)

    Args:
        action_name: 실행할 Action 이름
        params: 파라미터 (옵션)

    Returns:
        실행 결과
    """
    return asyncio.run(execute_action(action_name, params))


def find_action_by_text(text: str) -> dict:
    """
    자연어 텍스트로 Action 찾기

    Args:
        text: 사용자 입력 (예: "프론트 빌드해줘", "테스트 실행")

    Returns:
        매칭된 Action 또는 추천 목록
    """
    registry = get_registry()
    action = registry.find_by_trigger(text)

    if action:
        return {
            "found": True,
            "action": action.to_dict(layer=1),
            "suggestion": f"'{action.name}' Action을 실행하시겠습니까?",
        }

    # 매칭 실패 시 전체 목록 반환
    return {
        "found": False,
        "suggestion": "매칭되는 Action이 없습니다.",
        "available_actions": registry.list(),
    }


# ============================================
# A2A Agent 정의
# ============================================

# 시스템 프롬프트
SYSTEM_PROMPT = """You are an Action Agent specialized in executing automated tasks.

Your capabilities:
- Build: frontend_build, backend_build, docker_build
- Test: unit_test, e2e_test
- Lint: eslint, prettier
- Deploy: vercel_deploy
- Git: git_commit

When a user requests a task:
1. Use find_action_by_text to identify the appropriate action
2. Use get_action_info to check required parameters
3. Use execute_action to run the action
4. Report the result clearly

Always confirm before executing potentially destructive actions (deploy, git push).
Respond in Korean.
"""

# Agent 생성
action_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="action_agent",
    description="빌드, 테스트, 배포 등 반복 작업 자동화 전문가. 프론트엔드/백엔드 빌드, 테스트 실행, 린트, Git 커밋 등을 처리합니다.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(list_actions),
        FunctionTool(get_action_info),
        FunctionTool(execute_action_sync),
        FunctionTool(find_action_by_text),
    ],
)


# ============================================
# A2A Server
# ============================================

def create_app():
    """FastAPI 앱 생성 (A2A 프로토콜)"""
    return A2AServer(action_agent).create_app()


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description="AG_action A2A Agent")
    parser.add_argument("--port", type=int, default=8120, help="Server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    args = parser.parse_args()

    # Registry 초기화
    registry = get_registry()
    stats = registry.stats()
    print(f"[ActionAgent] Loaded {stats['total_actions']} actions")
    print(f"[ActionAgent] Categories: {list(stats['categories'].keys())}")

    # 서버 시작
    import uvicorn
    print(f"\n[ActionAgent] Starting server at http://{args.host}:{args.port}")
    print(f"[ActionAgent] A2A endpoint: http://{args.host}:{args.port}/")

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

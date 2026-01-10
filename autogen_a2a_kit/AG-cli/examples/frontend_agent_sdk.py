# Frontend Agent with Claude Agent SDK Integration
# A2A 에이전트 + Claude Agent SDK 통합 예제 (Python 네이티브)
"""
사용법:
    pip install claude-agent-sdk
    python frontend_agent_sdk.py

이 에이전트는:
1. Google ADK로 A2A 서버 실행
2. 요청을 받으면 Claude Agent SDK 호출 (Python 네이티브)
3. frontend/ 폴더에 React/TypeScript 코드 작성
4. 세션 관리, 훅 등 고급 기능 지원
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# .env 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from: {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed")

# Claude Agent SDK 임포트 (설치 필요: pip install claude-agent-sdk)
try:
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ResultMessage
    )
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    print("[WARN] claude-agent-sdk not installed. Run: pip install claude-agent-sdk")
    CLAUDE_SDK_AVAILABLE = False

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# 환경 변수 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    sys.exit(1)

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent


def execute_frontend_code_sync(task: str, subfolder: str = "") -> dict:
    """Claude Agent SDK로 frontend/ 폴더에 코드 작성 (동기 래퍼)

    Args:
        task: 수행할 작업 설명
        subfolder: frontend/ 내의 하위 폴더

    Returns:
        실행 결과
    """
    if not CLAUDE_SDK_AVAILABLE:
        return {
            "success": False,
            "error": "claude-agent-sdk가 설치되지 않았습니다. pip install claude-agent-sdk"
        }

    # asyncio 이벤트 루프에서 실행
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        execute_frontend_code_async(task, subfolder)
    )


async def execute_frontend_code_async(task: str, subfolder: str = "") -> dict:
    """Claude Agent SDK로 frontend/ 폴더에 코드 작성 (비동기)

    Args:
        task: 수행할 작업 설명
        subfolder: frontend/ 내의 하위 폴더

    Returns:
        실행 결과
    """
    # 프로젝트 폴더 설정
    frontend_path = PROJECT_ROOT / "project" / "frontend"
    if subfolder:
        frontend_path = frontend_path / subfolder
    frontend_path.mkdir(parents=True, exist_ok=True)

    print(f"\n[Claude SDK] 작업 시작: {task[:50]}...")
    print(f"[Claude SDK] 작업 폴더: {frontend_path}")

    # Claude Agent SDK 옵션 설정
    options = ClaudeAgentOptions(
        cwd=str(frontend_path),
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",  # 파일 편집 자동 승인
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
Additional Rules for Frontend Development:
- You are a React/TypeScript expert
- Use TailwindCSS for styling
- Follow component-based architecture
- Include proper TypeScript types
- Add loading and error states
"""
        }
    )

    try:
        result_text = ""
        tools_used = []
        session_id = None
        total_cost = 0

        # Claude SDK 쿼리 실행
        async for message in query(prompt=task, options=options):
            # 결과 메시지 처리
            if isinstance(message, ResultMessage):
                session_id = message.session_id
                total_cost = message.total_cost_usd or 0
                print(f"[Claude SDK] 완료! 세션: {session_id}")

            # 어시스턴트 메시지 처리
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text + "\n"
                    elif isinstance(block, ToolUseBlock):
                        tools_used.append({
                            "tool": block.name,
                            "input": str(block.input)[:100]
                        })
                        print(f"[Claude SDK] 도구 사용: {block.name}")

        return {
            "success": True,
            "result": result_text.strip() or "작업 완료",
            "session_id": session_id,
            "tools_used": tools_used,
            "cost_usd": total_cost
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def execute_frontend_code_with_session(
    task: str,
    session_id: Optional[str] = None
) -> dict:
    """Claude SDK Client로 세션 유지하며 코드 작성

    세션을 유지하면 이전 대화 컨텍스트를 기억합니다.

    Args:
        task: 수행할 작업
        session_id: 이전 세션 ID (재개시)

    Returns:
        실행 결과
    """
    frontend_path = PROJECT_ROOT / "project" / "frontend"
    frontend_path.mkdir(parents=True, exist_ok=True)

    options = ClaudeAgentOptions(
        cwd=str(frontend_path),
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        resume=session_id  # 세션 재개
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            # 쿼리 전송
            await client.query(task)

            result_text = ""
            new_session_id = None

            # 응답 수신
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_text += block.text
                elif isinstance(message, ResultMessage):
                    new_session_id = message.session_id

            return {
                "success": True,
                "result": result_text,
                "session_id": new_session_id
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_frontend_files(pattern: str = "*") -> dict:
    """frontend/ 폴더의 파일 목록 조회"""
    frontend_path = PROJECT_ROOT / "project" / "frontend"

    if not frontend_path.exists():
        return {"files": [], "message": "frontend/ 폴더가 아직 없습니다"}

    files = []
    for f in frontend_path.rglob(pattern):
        if f.is_file() and "node_modules" not in str(f):
            rel_path = str(f.relative_to(frontend_path))
            files.append(rel_path)

    return {
        "files": sorted(files),
        "count": len(files),
        "root": str(frontend_path)
    }


# Frontend 전문 에이전트 (SDK 버전)
frontend_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="frontend_agent_sdk",
    description="React/TypeScript 전문가. Claude Agent SDK를 사용하여 frontend/ 폴더에 코드를 작성합니다. "
                "Python 네이티브 API로 세션 관리, 훅 등 고급 기능을 지원합니다.",
    instruction="""당신은 Frontend 개발 전문 에이전트입니다.

주요 기능:
1. execute_frontend_code_sync - Claude SDK로 코드 작성
2. list_frontend_files - 파일 목록 확인

이 에이전트는 Claude Agent SDK (Python 네이티브)를 사용합니다.
subprocess 대신 Python 라이브러리로 직접 호출하여 더 세밀한 제어가 가능합니다.

한국어로 응답해주세요.""",
    tools=[
        FunctionTool(execute_frontend_code_sync),
        FunctionTool(list_frontend_files)
    ]
)


# A2A 서버 실행
if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    PORT = 8012

    print("=" * 60)
    print("Frontend Agent - Claude Agent SDK Integration")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"SDK Available: {CLAUDE_SDK_AVAILABLE}")
    print(f"Project Root: {PROJECT_ROOT}")
    print("=" * 60)

    if not CLAUDE_SDK_AVAILABLE:
        print("\n[!] Claude Agent SDK가 설치되지 않았습니다.")
        print("    pip install claude-agent-sdk")
        print("    설치 후 다시 실행하세요.\n")

    a2a_app = to_a2a(frontend_agent, port=PORT, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=PORT)

# AG-CLI Agent - A2A Protocol Integration
"""
CollaborativeAgent를 A2A 프로토콜로 노출하는 에이전트

사용법:
    python studio/cli_agent.py --folder frontend --port 8110
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
import argparse

# 환경변수 로드
try:
    from dotenv import load_dotenv
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from: {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed")

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# 상위 디렉토리 import
sys.path.insert(0, str(Path(__file__).parent.parent))

# API 키 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    print("       .env 파일 또는 환경변수로 설정해주세요.")


# ============================================================
# Claude CLI Tool Functions
# ============================================================

# 전역 설정 (argparse로 설정됨)
WORK_FOLDER = "project"
EXPERTISE = "General"
MESSAGE_BUS_URL = "http://localhost:8100"
SHARED_MEMORY_URL = "http://localhost:8101"


def execute_claude_cli(task: str) -> dict:
    """Claude CLI를 실행하여 코드를 작성하거나 파일을 수정합니다.

    이 도구는 Claude Code CLI를 subprocess로 실행하여 실제 파일 작업을 수행합니다.
    작업은 지정된 폴더 내에서만 수행됩니다.

    Args:
        task: 수행할 작업 설명 (예: "React Button 컴포넌트 만들어줘")

    Returns:
        Claude CLI 실행 결과를 담은 딕셔너리
    """
    work_dir = Path(WORK_FOLDER)
    work_dir.mkdir(parents=True, exist_ok=True)

    # 시스템 프롬프트 구성
    system_prompt = f"""You are a {EXPERTISE} expert.
You can ONLY modify files in the {WORK_FOLDER}/ folder.
Do NOT modify files outside this folder.
Write clean, well-documented code."""

    cmd = [
        "claude",
        "-p", task,
        "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",
        "--output-format", "json",
        "--append-system-prompt", system_prompt
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(work_dir),
            timeout=300  # 5분 타임아웃
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr,
                "task": task,
                "folder": WORK_FOLDER
            }

        # JSON 파싱 시도
        try:
            output = json.loads(result.stdout)
            return {
                "success": True,
                "output": output,
                "task": task,
                "folder": WORK_FOLDER
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout,
                "task": task,
                "folder": WORK_FOLDER
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout - 작업이 5분을 초과했습니다",
            "task": task,
            "folder": WORK_FOLDER
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Claude CLI를 찾을 수 없습니다. Claude Code가 설치되어 있는지 확인하세요.",
            "task": task,
            "folder": WORK_FOLDER
        }


def list_files() -> dict:
    """작업 폴더의 파일 목록을 조회합니다.

    Returns:
        파일 목록을 담은 딕셔너리
    """
    work_dir = Path(WORK_FOLDER)
    if not work_dir.exists():
        return {"files": [], "error": f"{WORK_FOLDER}/ 폴더가 없습니다", "count": 0}

    files = []
    for f in work_dir.rglob("*"):
        if f.is_file():
            # node_modules 등 제외
            if "node_modules" in str(f) or ".git" in str(f):
                continue
            files.append(str(f.relative_to(work_dir)))

    return {
        "files": files[:100],  # 최대 100개
        "count": len(files),
        "folder": WORK_FOLDER
    }


def read_file(file_path: str) -> dict:
    """작업 폴더 내의 파일 내용을 읽습니다.

    Args:
        file_path: 읽을 파일 경로 (작업 폴더 기준 상대 경로)

    Returns:
        파일 내용을 담은 딕셔너리
    """
    work_dir = Path(WORK_FOLDER)
    target = work_dir / file_path

    # 보안: 작업 폴더 외부 접근 방지
    try:
        target.resolve().relative_to(work_dir.resolve())
    except ValueError:
        return {"error": "작업 폴더 외부 접근 불가", "file": file_path}

    if not target.exists():
        return {"error": f"파일을 찾을 수 없습니다: {file_path}", "file": file_path}

    try:
        content = target.read_text(encoding="utf-8")
        return {
            "file": file_path,
            "content": content[:10000],  # 최대 10000자
            "size": len(content)
        }
    except Exception as e:
        return {"error": str(e), "file": file_path}


def send_message(message: str, to_agent: str = "all") -> dict:
    """Message Bus를 통해 다른 에이전트에게 메시지를 보냅니다.

    Args:
        message: 보낼 메시지
        to_agent: 대상 에이전트 (기본값: "all" - 브로드캐스트)

    Returns:
        전송 결과
    """
    import httpx

    try:
        response = httpx.post(
            f"{MESSAGE_BUS_URL}/send",
            json={
                "from_agent": f"cli_{WORK_FOLDER}",
                "to_agent": to_agent,
                "message": message
            },
            timeout=5.0
        )
        return {"success": True, "sent_to": to_agent, "message": message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def share_data(key: str, data: dict) -> dict:
    """SharedMemory에 데이터를 저장합니다.

    Args:
        key: 저장할 키 (예: "api_spec", "schema")
        data: 저장할 데이터

    Returns:
        저장 결과
    """
    import httpx

    try:
        response = httpx.post(
            f"{SHARED_MEMORY_URL}/{key}",
            json=data,
            timeout=5.0
        )
        return {"success": True, "key": key, "stored": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_shared_data(key: str) -> dict:
    """SharedMemory에서 데이터를 조회합니다.

    Args:
        key: 조회할 키 (예: "api_spec", "schema")

    Returns:
        저장된 데이터
    """
    import httpx

    try:
        response = httpx.get(
            f"{SHARED_MEMORY_URL}/{key}",
            timeout=5.0
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Agent Factory
# ============================================================

def create_cli_agent(folder: str, expertise: str, description: str) -> Agent:
    """폴더 전문 Claude CLI 에이전트를 생성합니다.

    Args:
        folder: 작업 폴더 (예: "frontend", "backend")
        expertise: 전문 분야 (예: "React/TypeScript", "FastAPI/Python")
        description: 에이전트 설명

    Returns:
        Google ADK Agent 인스턴스
    """
    global WORK_FOLDER, EXPERTISE
    WORK_FOLDER = folder
    EXPERTISE = expertise

    agent = Agent(
        model=LiteLlm(model="openai/gpt-4o-mini"),
        name=f"cli_{folder}_agent",
        description=description,
        instruction=f"""당신은 {expertise} 전문 에이전트입니다.

주요 기능:
1. execute_claude_cli 도구로 Claude CLI를 실행하여 실제 코드 작성
2. list_files로 작업 폴더 파일 확인
3. read_file로 파일 내용 읽기
4. send_message로 다른 에이전트와 대화
5. share_data/get_shared_data로 정보 공유

중요:
- 모든 파일 작업은 {folder}/ 폴더에서만 수행됩니다
- 다른 폴더는 접근할 수 없습니다

한국어로 응답해주세요.""",
        tools=[
            FunctionTool(execute_claude_cli),
            FunctionTool(list_files),
            FunctionTool(read_file),
            FunctionTool(send_message),
            FunctionTool(share_data),
            FunctionTool(get_shared_data)
        ]
    )

    return agent


# ============================================================
# A2A Server Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="AG-CLI A2A Agent")
    parser.add_argument("--folder", default="project", help="작업 폴더 (기본값: project)")
    parser.add_argument("--expertise", default="General Development", help="전문 분야")
    parser.add_argument("--port", type=int, default=8110, help="A2A 서버 포트 (기본값: 8110)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본값: 127.0.0.1)")
    args = parser.parse_args()

    # 에이전트 생성
    agent = create_cli_agent(
        folder=args.folder,
        expertise=args.expertise,
        description=f"Claude CLI 기반 {args.expertise} 전문가. {args.folder}/ 폴더의 코드를 작성합니다."
    )

    print("=" * 60)
    print(f"AG-CLI Agent - {args.folder}")
    print("=" * 60)
    print(f"Folder:    {args.folder}/")
    print(f"Expertise: {args.expertise}")
    print(f"Port:      {args.port}")
    print(f"A2A URL:   http://{args.host}:{args.port}")
    print(f"Agent:     http://{args.host}:{args.port}/.well-known/agent.json")
    print("=" * 60)

    # A2A 서버 시작
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    a2a_app = to_a2a(agent, port=args.port, host=args.host)
    uvicorn.run(a2a_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

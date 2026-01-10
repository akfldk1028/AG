# Frontend Agent with Claude CLI Integration
# A2A 에이전트 + Claude CLI subprocess 통합 예제
"""
사용법:
    python frontend_agent_claude.py

이 에이전트는:
1. Google ADK로 A2A 서버 실행
2. 요청을 받으면 Claude CLI를 subprocess로 호출
3. frontend/ 폴더에 React/TypeScript 코드 작성
"""
import json
import os
import subprocess
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

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# 환경 변수 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    sys.exit(1)

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent


def execute_frontend_code(task: str, subfolder: str = "") -> dict:
    """Claude CLI로 frontend/ 폴더에 React/TypeScript 코드 작성

    Args:
        task: 수행할 작업 설명 (예: "Button 컴포넌트 만들어줘")
        subfolder: frontend/ 내의 하위 폴더 (예: "src/components")

    Returns:
        Claude CLI 실행 결과
        - success: 성공 여부
        - result: 실행 결과 또는 에러 메시지
        - session_id: Claude 세션 ID (나중에 재개 가능)
    """
    # 프로젝트 폴더 설정
    frontend_path = PROJECT_ROOT / "project" / "frontend"
    if subfolder:
        frontend_path = frontend_path / subfolder
    frontend_path.mkdir(parents=True, exist_ok=True)

    print(f"\n[Claude CLI] 작업 시작: {task[:50]}...")
    print(f"[Claude CLI] 작업 폴더: {frontend_path}")

    # Claude CLI 명령 구성
    cmd = [
        "claude", "-p", task,
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
        "--output-format", "json"
    ]

    # 시스템 프롬프트 추가 (폴더 제한)
    system_prompt = """You are a Frontend Development Expert.

EXPERTISE:
- React 18+ with TypeScript
- TailwindCSS for styling
- Zustand/Redux for state management
- React Query for data fetching

RULES:
1. You can ONLY modify files in the current directory (frontend/)
2. Use TypeScript with strict mode
3. Follow component-based architecture
4. Include proper type definitions
5. Add loading and error states to data-fetching components

CODING STANDARDS:
- Use functional components with hooks
- Export types/interfaces separately
- Add JSDoc comments for public APIs
- Use meaningful variable names"""

    cmd.extend(["--append-system-prompt", system_prompt])

    try:
        # Claude CLI 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(frontend_path),
            timeout=300,  # 5분 타임아웃
            env={**os.environ}  # 환경변수 전달
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"[Claude CLI] 에러: {error_msg[:200]}")
            return {
                "success": False,
                "error": error_msg,
                "return_code": result.returncode
            }

        # JSON 파싱 시도
        try:
            output = json.loads(result.stdout)
            print(f"[Claude CLI] 완료! 세션 ID: {output.get('session_id', 'N/A')}")
            return {
                "success": True,
                "result": output.get("result", "작업 완료"),
                "session_id": output.get("session_id"),
                "usage": output.get("usage", {})
            }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트로 반환
            print(f"[Claude CLI] 완료 (텍스트 출력)")
            return {
                "success": True,
                "result": result.stdout[:2000]  # 최대 2000자
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "타임아웃: 5분 초과"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Claude CLI가 설치되지 않았습니다. npm install -g @anthropic-ai/claude-code"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_frontend_files(pattern: str = "*") -> dict:
    """frontend/ 폴더의 파일 목록 조회

    Args:
        pattern: 파일 패턴 (예: "*.tsx", "*.ts")

    Returns:
        파일 목록
    """
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


def read_frontend_file(file_path: str) -> dict:
    """frontend/ 폴더의 파일 내용 읽기

    Args:
        file_path: frontend/ 기준 상대 경로 (예: "src/App.tsx")

    Returns:
        파일 내용
    """
    full_path = PROJECT_ROOT / "project" / "frontend" / file_path

    if not full_path.exists():
        return {"error": f"파일이 없습니다: {file_path}"}

    if not full_path.is_file():
        return {"error": f"파일이 아닙니다: {file_path}"}

    try:
        content = full_path.read_text(encoding="utf-8")
        return {
            "path": file_path,
            "content": content,
            "size": len(content),
            "lines": content.count("\n") + 1
        }
    except Exception as e:
        return {"error": str(e)}


# Frontend 전문 에이전트
frontend_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),  # 빠른 판단용 (Claude CLI가 실제 코딩)
    name="frontend_agent",
    description="React/TypeScript 전문가. Claude CLI를 사용하여 frontend/ 폴더에 코드를 작성합니다.",
    instruction="""당신은 Frontend 개발 전문 에이전트입니다.

주요 기능:
1. execute_frontend_code - Claude CLI로 실제 코드 작성
2. list_frontend_files - 파일 목록 확인
3. read_frontend_file - 파일 내용 읽기

작업 흐름:
1. 사용자 요청 분석
2. execute_frontend_code로 Claude CLI 호출
3. 결과 확인 및 보고

중요:
- Claude CLI가 실제 파일을 생성/수정합니다
- frontend/ 폴더만 수정 가능합니다
- 다른 폴더는 읽기만 가능합니다

한국어로 응답해주세요.""",
    tools=[
        FunctionTool(execute_frontend_code),
        FunctionTool(list_frontend_files),
        FunctionTool(read_frontend_file)
    ]
)


# A2A 서버 실행
if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    PORT = 8010

    print("=" * 60)
    print("Frontend Agent - Claude CLI Integration")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Frontend Folder: {PROJECT_ROOT / 'project' / 'frontend'}")
    print("=" * 60)
    print("\n테스트 방법:")
    print(f"curl -X POST http://localhost:{PORT} \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"message/send\",")
    print("       \"params\":{\"message\":{\"parts\":[{\"type\":\"text\",")
    print("       \"text\":\"Button 컴포넌트 만들어줘\"}]}}}'")
    print("=" * 60)

    a2a_app = to_a2a(frontend_agent, port=PORT, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=PORT)

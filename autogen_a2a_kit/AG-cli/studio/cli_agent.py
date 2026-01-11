# AG-CLI Agent - A2A Protocol Integration (Modular Version)
"""
CollaborativeAgent를 A2A 프로토콜로 노출하는 에이전트
실시간 로그 스트리밍 지원!

아키텍처:
    cli_agent.py          - 메인 엔트리 (이 파일)
    ├── config.py         - 전역 설정
    ├── tools/
    │   ├── claude_cli.py   - Claude CLI 실행
    │   ├── file_ops.py     - 파일 작업
    │   └── shared_folder.py - 공유 폴더
    └── utils/
        └── logging.py      - 로그 시스템

사용법:
    python studio/cli_agent.py --folder frontend --port 8110

로그 확인:
    GET http://localhost:{port}/logs/{task_id}
    GET http://localhost:{port}/logs/latest
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

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

# 모듈 import를 위한 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

# 로컬 모듈 import
from config import config
from tools import (
    execute_claude_cli,
    list_files,
    read_file,
    list_shared_files,
    read_shared_file,
    write_to_shared
)
from utils.logging import (
    get_logs,
    get_latest_task_id,
    LOG_STORE
)

# Google ADK imports
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# API 키 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    print("       .env 파일 또는 환경변수로 설정해주세요.")


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
    # 전역 설정 업데이트
    config.update(folder=folder, expertise=expertise)

    agent = Agent(
        model=LiteLlm(model="openai/gpt-4o-mini"),
        name=f"cli_{folder}_agent",
        description=description,
        instruction=f"""당신은 {expertise} 전문 에이전트입니다.

주요 기능:
1. execute_claude_cli - Claude CLI로 실제 코드 작성
2. list_files - 작업 폴더 파일 확인
3. read_file - 파일 내용 읽기
4. list_shared_files / read_shared_file / write_to_shared - 공유 폴더 관리

중요 규칙:
- 내 작업 폴더: {folder}/
- 공유 폴더: shared/ (모든 에이전트 접근 가능)
- 요청된 작업을 1회만 수행하세요. 같은 작업을 반복하지 마세요!

★★★ 작업 완료 후 반드시 ★★★
작업이 완료되면 응답 마지막에 반드시 "TASK_COMPLETE"라고 작성하세요.
이 키워드가 있어야 시스템이 작업 완료를 인식합니다.

응답 형식 예시:
```
파일을 생성했습니다.

--- Execution Log ---
  [WRITE] {folder}/test.py
    | print("Hello")
---

TASK_COMPLETE
```

한국어로 응답해주세요.""",
        tools=[
            FunctionTool(execute_claude_cli),
            FunctionTool(list_files),
            FunctionTool(read_file),
            FunctionTool(list_shared_files),
            FunctionTool(read_shared_file),
            FunctionTool(write_to_shared),
        ]
    )

    return agent


# ============================================================
# A2A Server Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="AG-CLI A2A Agent")
    parser.add_argument("--folder", default="project", help="작업 폴더 (기본값: project)")
    parser.add_argument("--shared-folder", default="shared", help="공유 폴더 (기본값: shared)")
    parser.add_argument("--expertise", default="General Development", help="전문 분야")
    parser.add_argument("--port", type=int, default=8110, help="A2A 서버 포트 (기본값: 8110)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본값: 127.0.0.1)")
    parser.add_argument("--max-turns", type=int, default=10, help="Claude CLI 최대 턴 수 (기본값: 10)")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 모드 활성화")
    args = parser.parse_args()

    # 전역 설정 업데이트
    config.update(
        folder=args.folder,
        shared_folder=args.shared_folder,
        expertise=args.expertise,
        max_turns=args.max_turns,
        verbose=args.verbose
    )

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
    print(f"Shared:    {config.SHARED_FOLDER}/ (cross-agent sharing)")
    print(f"Expertise: {args.expertise}")
    print(f"Port:      {args.port}")
    print(f"Max Turns: {args.max_turns}")
    print(f"Verbose:   {args.verbose}")
    print(f"A2A URL:   http://{args.host}:{args.port}")
    print(f"Agent:     http://{args.host}:{args.port}/.well-known/agent.json")
    print("=" * 60)

    # A2A 서버 시작
    import uvicorn
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse, StreamingResponse, JSONResponse
    from starlette.routing import Route
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    a2a_app = to_a2a(agent, port=args.port, host=args.host)

    # ============================================================
    # 로그 스트리밍 엔드포인트
    # ============================================================

    async def get_task_logs(request: Request):
        """특정 task의 로그 조회"""
        task_id = request.path_params.get("task_id", "")
        from_line = int(request.query_params.get("from_line", 0))
        logs = get_logs(task_id, from_line)
        return PlainTextResponse("\n".join(logs))

    async def get_latest_task_id_endpoint(request: Request):
        """현재 실행 중인 task ID 조회"""
        task_id = get_latest_task_id()
        return JSONResponse({
            "task_id": task_id,
            "logs_url": f"/logs/{task_id}" if task_id else None
        })

    async def stream_latest_logs(request: Request):
        """최신 task 로그 스트리밍 (SSE)"""
        async def generate():
            last_line = 0
            task_id = get_latest_task_id()
            if not task_id:
                yield "data: No active task\n\n"
                return

            yield f"data: === Streaming logs for task: {task_id} ===\n\n"

            # 5분간 로그 스트리밍
            for _ in range(300):
                current_task = get_latest_task_id()
                if task_id != current_task:
                    if current_task:
                        task_id = current_task
                        last_line = 0
                        yield f"data: === New task started: {task_id} ===\n\n"

                logs = get_logs(task_id, last_line)
                for log in logs:
                    yield f"data: {log}\n\n"
                last_line += len(logs)

                # 완료 확인
                if logs and "=== Task" in logs[-1] and ("Completed" in logs[-1] or "Failed" in logs[-1]):
                    yield "data: === Stream ended ===\n\n"
                    break

                await asyncio.sleep(0.5)

        return StreamingResponse(generate(), media_type="text/event-stream")

    async def list_all_logs(request: Request):
        """모든 task 로그 목록"""
        current_task = get_latest_task_id()
        return JSONResponse({
            "tasks": list(LOG_STORE.keys()),
            "current_task": current_task,
            "log_dir": str(config.LOG_DIR.absolute())
        })

    # 라우트 추가
    a2a_app.routes.extend([
        Route("/logs", list_all_logs, methods=["GET"]),
        Route("/logs/latest/id", get_latest_task_id_endpoint, methods=["GET"]),
        Route("/logs/latest/stream", stream_latest_logs, methods=["GET"]),
        Route("/logs/{task_id}", get_task_logs, methods=["GET"]),
    ])

    print(f"Logs API:  http://{args.host}:{args.port}/logs")
    print(f"Stream:    http://{args.host}:{args.port}/logs/latest/stream")
    print("=" * 60)

    uvicorn.run(a2a_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

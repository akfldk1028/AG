# AutoGen A2A Kit - Claude Code 지침서

## 1. A2A 에이전트 서버 - 반드시 먼저 실행!

A2A 에이전트를 사용하려면 **반드시** 서버를 먼저 실행해야 합니다.
에러 메시지 `A2A 호출 실패: All connection attempts failed` → A2A 서버 미실행!

### 에이전트 포트 정보
| Agent | Port | 경로 |
|-------|------|------|
| poetry_agent | 8003 | a2a_demo/poetry_agent/agent.py |
| philosophy_agent | 8004 | a2a_demo/philosophy_agent/agent.py |
| history_agent | 8005 | a2a_demo/history_agent/agent.py |
| calculator_agent | 8006 | a2a_demo/calculator_agent/agent.py |

### 서버 시작 명령 (PowerShell)
```powershell
# 각 창에서 실행
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\poetry_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\philosophy_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\history_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\calculator_agent; python agent.py'"
```

## 2. Google ADK 모델명 형식

**중요**: Google ADK는 `openai/gpt-4o-mini` 형식을 **지원하지 않음**!

```python
# 틀린 예
model="openai/gpt-4o-mini"  # X - Model not found 에러

# 맞는 예
model="gpt-4o-mini"  # O - 정상 작동
```

## 3. Frontend 빌드 (Windows)

```powershell
cd D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio\frontend

# 1. Clean
npx gatsby clean

# 2. Build
npx gatsby build --prefix-paths

# 3. Copy to web/ui
Copy-Item -Path "public\*" -Destination "..\autogenstudio\web\ui\" -Recurse -Force
```

## 4. 환경변수 (.env)

프로젝트 루트에 `.env` 파일 필요:
```
OPENAI_API_KEY=sk-xxx
```

위치: `D:\Data\22_AG\autogen_a2a_kit\.env`

## 5. Debate 패턴 - allow_repeated_speaker

Multi-agent debate에서 한 에이전트만 계속 선택되는 문제:
- `07_debate.json`의 `requiredConfig.allow_repeated_speaker: false` 설정
- `team-factory.ts`의 selector prompt에서 강하게 rotation 강조

## 6. AutoGen Studio 실행

```bash
cd D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8083
```

## 7. 파일 위치

- 패턴 JSON: `frontend/src/components/views/playground/chat/agentflow/patterns/data/`
- 팀 팩토리: `frontend/src/components/views/playground/chat/team-runtime/team-factory.ts`
- 패턴 로더: `frontend/src/components/views/playground/chat/agentflow/patterns/pattern-loader.ts`
- A2A 에이전트: `a2a_demo/*/agent.py`

## 8. AG-CLI: Claude CLI 기반 협업 에이전트 시스템 (★ 핵심!)

> **AG-CLI**는 Claude CLI를 기반으로 여러 에이전트가 **대화하며 협업**하는 시스템입니다.
> 모든 에이전트 간 대화가 실시간으로 표시됩니다!

### 아키텍처 개요
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DB Agent   │    │Backend Agent│    │Frontend Agent│
│  (db/)      │    │ (backend/)  │    │ (frontend/) │
└─────┬───────┘    └──────┬──────┘    └──────┬──────┘
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
       ┌──────▼──────┐        ┌───────▼───────┐
       │ Message Bus │        │ SharedMemory  │
       │  (8100)     │        │   (8101)      │
       └─────────────┘        └───────────────┘
```

### 서버 포트 정보
| Server | Port | 용도 | 파일 |
|--------|------|------|------|
| Message Bus | 8100 | 에이전트 간 대화 라우팅 | `AG-cli/mcp/message_bus.py` |
| SharedMemory | 8101 | 정보 공유, 이벤트 발행 | `AG-cli/mcp/shared_memory.py` |
| Viewer | 8100/viewer | 실시간 대화 웹 뷰어 | Message Bus 내장 |

### 서버 시작 명령 (PowerShell)
```powershell
# 터미널 1: Message Bus
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli
python mcp/message_bus.py

# 터미널 2: SharedMemory
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py

# 터미널 3: 예제 실행
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli
python examples/collaboration/run_shopping_mall.py
```

### 핵심 클래스: CollaborativeAgent

`AG-cli/agents/base_collaborative.py`의 핵심 메서드:

```python
class CollaborativeAgent:
    # 초기화 - 에이전트 이름, 작업 폴더, 전문 분야
    def __init__(self, name: str, folder: str, expertise: str):
        self.name = name
        self.work_dir = Path(folder)
        self.expertise = expertise

    # 대화 메서드들 (★ 모두 Message Bus 경유)
    async def say(self, message: str, to: str = "all"):
        """다른 에이전트에게 메시지 전송"""

    async def ask(self, question: str, to: str) -> str:
        """질문하고 응답 대기"""

    async def listen(self, timeout: float = 10.0) -> dict:
        """메시지 수신 대기"""

    # 작업 메서드 (★ Claude CLI 실행)
    async def work(self, task: str, context: dict = None) -> dict:
        """Claude CLI로 작업 실행"""

    # SharedMemory 메서드들
    async def share(self, key: str, data: dict):
        """정보를 SharedMemory에 저장"""

    async def get_shared(self, key: str) -> dict:
        """SharedMemory에서 정보 조회"""

    async def publish_event(self, event_type: str, data: dict):
        """이벤트 발행 (다른 에이전트에게 알림)"""
```

### Claude CLI 실행 방식

`CollaborativeAgent.work()`는 내부적으로 다음과 같이 Claude CLI를 실행:

```python
async def _execute_claude_cli(self, task: str, context: dict = None) -> dict:
    cmd = [
        "claude",
        "-p", task,                              # Headless 모드
        "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",  # 허용 도구
        "--output-format", "json",              # JSON 출력
        "--append-system-prompt", system_prompt  # 컨텍스트 주입
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(self.work_dir),  # 작업 폴더에서 실행
        timeout=300
    )
```

### 주요 CLI 플래그 (공식 문서 기준)
| 플래그 | 용도 | 예시 |
|--------|------|------|
| `-p` | 프롬프트 직접 전달 (헤드리스 모드) | `claude -p "코드 작성해줘"` |
| `--allowedTools` | 허용할 도구 목록 | `--allowedTools Read,Write,Edit` |
| `--output-format` | 출력 형식 | `json`, `stream-json`, `text` |
| `--append-system-prompt` | 시스템 프롬프트 추가 | `--append-system-prompt "DB 전문가"` |
| `--resume` | 이전 세션 이어하기 | `--resume` |

### 협업 흐름 예시 (Shopping Mall)

```
1. Orchestrator: 프로젝트 시작
   ↓
2. DB Agent: 스키마 설계 → SharedMemory에 저장
   → publish_event("schema_ready")
   ↓
3. Backend Agent: API 개발 (스키마 참조)
   → publish_event("api_ready")
   ↓
4. Frontend Agent: UI 개발 (API 스펙 참조)
   → publish_event("frontend_ready")
   ↓
5. Test Agent: 테스트 작성
```

### 파일 구조
```
AG-cli/
├── agents/
│   ├── __init__.py           # CollaborativeAgent 내보내기
│   └── base_collaborative.py # 핵심 클래스 (677줄)
├── mcp/
│   ├── __init__.py
│   ├── message_bus.py        # 대화 라우팅 (487줄)
│   └── shared_memory.py      # 정보 공유 (575줄)
├── examples/
│   └── collaboration/
│       └── run_shopping_mall.py  # 쇼핑몰 예제
└── docs/
    ├── COLLABORATIVE_FLOW.md # 협업 흐름 문서
    └── ARCHITECTURE.md       # 아키텍처 문서
```

### 새 에이전트 추가 (AG-CLI)

```python
from agents.base_collaborative import CollaborativeAgent

class MyAgent(CollaborativeAgent):
    def __init__(self):
        super().__init__(
            name="my_agent",        # 에이전트 이름
            folder="my_work",       # 작업 폴더
            expertise="TypeScript"  # 전문 분야
        )

    async def do_task(self):
        # 1. 다른 에이전트에게 알림
        await self.say("작업 시작합니다", to="orchestrator")

        # 2. 필요한 정보 가져오기
        api_spec = await self.get_shared("api_spec")

        # 3. Claude CLI로 작업 실행
        result = await self.work("TypeScript 코드 작성해줘", context={"api": api_spec})

        # 4. 결과 공유
        await self.share("my_result", result)
        await self.publish_event("my_task_done", {"success": True})
```

### 디버깅
```powershell
# Message Bus 로그 확인 → 터미널에 모든 대화가 컬러로 표시됨

# 실시간 웹 뷰어
# → http://localhost:8100/viewer

# SharedMemory 상태 확인
curl http://localhost:8101/schema
curl http://localhost:8101/api-spec
curl http://localhost:8101/events
```

### 주의사항
1. **서버 순서**: Message Bus → SharedMemory → 에이전트 순으로 시작
2. **포트 충돌**: 8100, 8101 포트가 사용 중이면 에러 발생
3. **Claude CLI 필수**: 각 에이전트가 `claude` 명령어를 실행하므로 Claude Code 설치 필요
4. **작업 폴더 생성**: 에이전트의 `folder`는 자동 생성되지 않음, 미리 생성 필요

## 9. 자주 발생하는 에러

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `A2A 호출 실패: All connection attempts failed` | A2A 서버 미실행 | 1번 참조 |
| `Model openai/gpt-4o-mini not found` | 잘못된 모델명 형식 | 2번 참조 |
| `Connection refused (8100/8101)` | AG-CLI 서버 미실행 | 8번 참조 |
| Frontend 변경 안 반영됨 | 빌드 안함 | 3번 참조 |
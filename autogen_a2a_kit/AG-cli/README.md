# AG-CLI: Multi-Claude Autonomous Coding System

> **📖 전체 문서 색인**: [`../DOCS_INDEX.md`](../DOCS_INDEX.md) - 모든 문서 목록 및 읽기 순서
>
> **비전**: 각 A2A 에이전트가 Claude CLI 인스턴스가 되어, 폴더별 전문성을 가지고 협업하여 자동으로 프로젝트를 생성하는 시스템

---

## 핵심 아이디어

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AG-CLI Architecture                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   User Request: "쇼핑몰 만들어줘"                                         │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────────┐                                                   │
│   │  Orchestrator   │  (작업 분해 & 분배)                                │
│   │  Claude Agent   │                                                   │
│   └────────┬────────┘                                                   │
│            │                                                             │
│   ┌────────┼────────┬────────────┬────────────┐                         │
│   ▼        ▼        ▼            ▼            ▼                         │
│ ┌──────┐ ┌──────┐ ┌──────┐   ┌──────┐   ┌──────┐                       │
│ │Front │ │Back  │ │ DB   │   │Test  │   │DevOps│                       │
│ │Agent │ │Agent │ │Agent │   │Agent │   │Agent │                       │
│ └──┬───┘ └──┬───┘ └──┬───┘   └──┬───┘   └──┬───┘                       │
│    │        │        │          │          │                            │
│    ▼        ▼        ▼          ▼          ▼                            │
│ frontend/ backend/  db/      tests/    docker/                         │
│  폴더      폴더     폴더      폴더       폴더                             │
│                                                                         │
│   ↑        ↑        ↑          ↑          ↑                            │
│   └────────┴────────┴──────────┴──────────┘                            │
│              │                                                          │
│              ▼                                                          │
│   ┌─────────────────────────────┐                                       │
│   │   Shared Memory (MCP)       │  (컨텍스트 공유)                       │
│   │   - 아키텍처 결정            │                                       │
│   │   - API 스펙                │                                       │
│   │   - 파일 상태               │                                       │
│   └─────────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 기술 스택 조사 결과

### 1. Claude Agent SDK (공식)

> **Source**: [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)

**핵심**: Claude Code의 모든 기능을 Python/TypeScript SDK로 사용 가능!

```python
# 에이전트 생성 예시
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async for message in query(
    prompt="frontend 폴더의 React 컴포넌트 구현해줘",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob"],
        agents={
            "frontend-agent": AgentDefinition(
                description="React/TypeScript 전문가",
                prompt="frontend/ 폴더만 수정. 다른 폴더 접근 금지.",
                tools=["Read", "Write", "Edit", "Glob"]
            )
        }
    )
):
    print(message)
```

**주요 기능**:
| 기능 | 설명 |
|------|------|
| Built-in Tools | Read, Write, Edit, Bash, Glob, Grep, WebSearch 등 |
| Subagents | Task tool로 전문 에이전트 스폰 (최대 10개 병렬) |
| Hooks | PreToolUse, PostToolUse 등 라이프사이클 훅 |
| MCP | 외부 시스템 연결 (DB, 브라우저 등) |
| Sessions | 세션 유지 & 재개 |

### 2. Claude CLI Headless Mode

> **Source**: [Headless Mode Docs](https://code.claude.com/docs/en/headless)

```bash
# 기본 사용
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"

# JSON 출력
claude -p "Summarize project" --output-format json

# 세션 재개
session_id=$(claude -p "Start task" --output-format json | jq -r '.session_id')
claude -p "Continue task" --resume "$session_id"
```

### 3. Agent-MCP 프레임워크

> **Source**: [Agent-MCP GitHub](https://github.com/rinadelph/Agent-MCP)

**핵심 개념**:
- **File Locking**: 동시 수정 방지
- **Task Dependencies**: 독립 작업은 병렬 실행
- **Knowledge Graph**: 아키텍처 결정, API 스펙 공유

### 4. Coding Agent Teams

> **Source**: [DevOps.com - Coding Agent Teams](https://devops.com/coding-agent-teams-the-next-frontier-in-ai-assisted-software-development/)

**역할 분담**:
- **Team Lead Agent**: 작업 분해 & 위임
- **Frontend Agent**: UI 코드 작성
- **Backend Agent**: API/서버 코드 작성
- **Test Agent**: 테스트 작성 & 실행
- **Review Agent**: 코드 리뷰 & 품질 체크

---

## 구현 방안 비교

### Option A: Claude Agent SDK 직접 사용

```
장점:
✅ 공식 SDK - 안정적
✅ Subagent 스폰 기능 내장
✅ 최대 10개 병렬 에이전트
✅ 세션 관리 내장

단점:
❌ 각 에이전트가 독립 프로세스 아님 (같은 Claude 인스턴스 내 subagent)
❌ 에이전트 간 통신이 제한적
```

**구조**:
```
┌─────────────────────────────────┐
│       Main Claude Agent         │
│   ┌───────────────────────┐    │
│   │  Task Tool (Subagent) │    │  ← 최대 10개 병렬
│   │  - frontend-agent     │    │
│   │  - backend-agent      │    │
│   │  - test-agent         │    │
│   └───────────────────────┘    │
└─────────────────────────────────┘
```

### Option B: A2A + Claude CLI 각각 실행 (★ 권장)

```
장점:
✅ 각 에이전트가 독립 Claude CLI 인스턴스
✅ 진정한 멀티프로세스
✅ 기존 A2A 인프라 재활용
✅ 에이전트별 독립 컨텍스트 윈도우

단점:
❌ 오케스트레이션 직접 구현 필요
❌ 메모리 공유 MCP 서버 필요
```

**구조**:
```
┌──────────────────────────────────────────────────────────────┐
│                    Orchestrator (A2A Server)                  │
│                    http://localhost:8000                      │
└──────────────────────┬───────────────────────────────────────┘
                       │ A2A Protocol
      ┌────────────────┼────────────────┬────────────────┐
      ▼                ▼                ▼                ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Frontend │    │ Backend  │    │   DB     │    │  Test    │
│  Agent   │    │  Agent   │    │  Agent   │    │  Agent   │
│ :8003    │    │ :8004    │    │ :8005    │    │ :8006    │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Claude   │    │ Claude   │    │ Claude   │    │ Claude   │
│ CLI      │    │ CLI      │    │ CLI      │    │ CLI      │
│ frontend/│    │ backend/ │    │ db/      │    │ tests/   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │
      └───────────────┴───────────────┴───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Shared Memory    │
                    │  (MCP Server)     │
                    │  - 아키텍처 결정   │
                    │  - API 스펙       │
                    │  - 파일 상태      │
                    └───────────────────┘
```

### Option C: 하이브리드 (A2A 오케스트레이터 + Agent SDK 워커)

```
장점:
✅ A2A로 외부 에이전트 관리
✅ Agent SDK로 세부 작업 처리
✅ 유연한 확장성

단점:
❌ 복잡한 아키텍처
❌ 두 시스템 모두 이해 필요
```

---

## 권장 구현 계획: Option B

### Phase 1: 기본 인프라 (1단계)

1. **폴더 전문 에이전트 템플릿**
   ```python
   # AG-cli/agents/folder_agent.py
   class FolderSpecialistAgent:
       def __init__(self, folder: str, expertise: str):
           self.folder = folder  # "frontend", "backend", etc.
           self.expertise = expertise  # "React/TypeScript", "FastAPI", etc.

       async def execute_task(self, task: str) -> str:
           """Claude CLI를 subprocess로 실행"""
           cmd = [
               "claude", "-p", task,
               "--allowedTools", "Read,Write,Edit,Glob,Grep",
               "--system-prompt", f"You are a {self.expertise} expert. "
                                  f"You ONLY work in the {self.folder}/ folder. "
                                  f"Do NOT modify files outside this folder."
           ]
           result = subprocess.run(cmd, capture_output=True)
           return result.stdout.decode()
   ```

2. **공유 메모리 MCP 서버**
   ```python
   # AG-cli/mcp/shared_memory.py
   class SharedMemoryServer:
       """에이전트 간 컨텍스트 공유"""

       def store_decision(self, key: str, decision: dict):
           """아키텍처 결정 저장"""

       def get_api_spec(self) -> dict:
           """현재 API 스펙 조회"""

       def lock_file(self, path: str, agent: str) -> bool:
           """파일 락 획득"""
   ```

3. **오케스트레이터**
   ```python
   # AG-cli/orchestrator.py
   class ProjectOrchestrator:
       def __init__(self):
           self.agents = {
               "frontend": FolderSpecialistAgent("frontend", "React/TypeScript"),
               "backend": FolderSpecialistAgent("backend", "FastAPI/Python"),
               "db": FolderSpecialistAgent("db", "PostgreSQL/Migrations"),
               "tests": FolderSpecialistAgent("tests", "pytest/testing"),
           }

       async def build_project(self, requirement: str):
           # 1. 요구사항 분석
           plan = await self.analyze_requirement(requirement)

           # 2. 병렬 작업 분배
           tasks = []
           for agent_name, work in plan.items():
               task = self.agents[agent_name].execute_task(work)
               tasks.append(task)

           # 3. 동시 실행
           results = await asyncio.gather(*tasks)

           # 4. 통합 & 테스트
           await self.integrate_and_test(results)
   ```

### Phase 2: A2A 통합 (2단계)

기존 A2A 인프라와 통합:

```python
# a2a_demo/frontend_agent/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import subprocess

def execute_claude_cli(task: str, folder: str = "frontend") -> dict:
    """Claude CLI 실행하여 코드 생성"""
    cmd = [
        "claude", "-p", task,
        "--allowedTools", "Read,Write,Edit,Glob",
        "--output-format", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, cwd=folder)
    return {"output": result.stdout.decode()}

frontend_agent = Agent(
    name="frontend_agent",
    description="React/TypeScript 전문가. frontend/ 폴더의 UI 코드 작성",
    tools=[FunctionTool(execute_claude_cli)]
)
```

### Phase 3: 고급 기능 (3단계)

- 코드 리뷰 에이전트
- 자동 테스트 실행
- CI/CD 통합
- 롤백 메커니즘

---

## 파일 구조

```
AG-cli/
├── README.md                    # 이 파일
├── docs/
│   ├── ARCHITECTURE.md          # 상세 아키텍처
│   ├── AGENTS.md                # 에이전트 정의
│   └── WORKFLOW.md              # 워크플로우
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # 기본 에이전트 클래스
│   ├── frontend_agent.py        # Frontend 전문
│   ├── backend_agent.py         # Backend 전문
│   ├── db_agent.py              # DB/Migration 전문
│   └── test_agent.py            # Test 전문
├── mcp/
│   ├── shared_memory.py         # 공유 메모리 서버
│   └── file_lock.py             # 파일 락 관리
├── orchestrator/
│   ├── planner.py               # 작업 계획
│   ├── coordinator.py           # 에이전트 조율
│   └── integrator.py            # 결과 통합
└── examples/
    └── shopping_mall/           # 쇼핑몰 예제
```

---

## 참고 자료

### 공식 문서
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Code Headless Mode](https://code.claude.com/docs/en/headless)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)

### 프레임워크
- [Agent-MCP](https://github.com/rinadelph/Agent-MCP) - Multi-agent coordination
- [Claude Flow](https://github.com/ruvnet/claude-flow) - Agent orchestration

### 블로그/튜토리얼
- [How to Use Claude Code Subagents](https://zachwills.net/how-to-use-claude-code-subagents-to-parallelize-development/)
- [Coding Agent Teams](https://devops.com/coding-agent-teams-the-next-frontier-in-ai-assisted-software-development/)
- [Building Agents with Claude Code's SDK](https://blog.promptlayer.com/building-agents-with-claude-codes-sdk/)

---

## 🎉 구현 완료!

### 핵심 기능 (✅ 완료)

1. **Message Bus** (`mcp/message_bus.py`)
   - 에이전트 간 실시간 대화 라우팅
   - WebSocket + REST API
   - 실시간 협업 뷰어 (http://localhost:8100/viewer)

2. **SharedMemory** (`mcp/shared_memory.py`)
   - 아키텍처 결정 저장 (스키마, API 스펙)
   - 이벤트 발행/구독
   - 파일 락 관리

3. **CollaborativeAgent** (`agents/base_collaborative.py`)
   - 대화 기능 (say, ask, listen)
   - SharedMemory 연동
   - Claude CLI 실행

4. **협업 예제** (`examples/collaboration/run_shopping_mall.py`)
   - DB → Backend → Frontend → Test 순차 협업
   - 실시간 대화 표시

---

## 🚀 빠른 시작

```bash
# 1. 필요한 라이브러리 설치
pip install fastapi uvicorn websockets httpx rich

# 2. Message Bus 시작 (터미널 1)
cd AG-cli
python mcp/message_bus.py

# 3. SharedMemory 시작 (터미널 2)
python mcp/shared_memory.py

# 4. 협업 뷰어 열기
# 브라우저에서: http://localhost:8100/viewer

# 5. 쇼핑몰 예제 실행 (터미널 3)
python examples/collaboration/run_shopping_mall.py
```

---

## 📁 파일 구조 (최신)

```
AG-cli/
├── README.md                           # 이 파일
├── docs/
│   ├── ARCHITECTURE.md                 # 상세 아키텍처
│   ├── AGENTS.md                       # 에이전트 정의
│   ├── A2A_INTEGRATION.md              # A2A 통합 가이드
│   └── COLLABORATIVE_FLOW.md           # ★ 협업 아키텍처
├── agents/
│   ├── __init__.py
│   └── base_collaborative.py           # ★ 협업 에이전트 베이스
├── mcp/
│   ├── __init__.py
│   ├── message_bus.py                  # ★ 에이전트 대화 허브
│   └── shared_memory.py                # ★ 정보 공유 서버
├── examples/
│   ├── frontend_agent_claude.py        # A2A + Claude CLI 예제
│   ├── frontend_agent_sdk.py           # A2A + SDK 예제
│   └── collaboration/
│       └── run_shopping_mall.py        # ★ 협업 예제
└── project/                            # 생성된 프로젝트 폴더
    ├── frontend/
    ├── backend/
    ├── db/
    └── tests/
```

---

## 🔧 서버 포트 정보

| 서버 | 포트 | 설명 |
|------|------|------|
| Message Bus | 8100 | 에이전트 대화 라우팅 |
| SharedMemory | 8101 | 정보 공유 |
| Frontend Agent | 8010 | (예정) A2A 에이전트 |
| Backend Agent | 8011 | (예정) A2A 에이전트 |
| DB Agent | 8012 | (예정) A2A 에이전트 |
| Test Agent | 8013 | (예정) A2A 에이전트 |

---

## 📖 상세 문서

| 문서 | 설명 |
|------|------|
| [MAINTAINER_GUIDE.md](docs/MAINTAINER_GUIDE.md) | **★ AI 유지보수 가이드 (필독!)** |
| [COLLABORATIVE_FLOW.md](docs/COLLABORATIVE_FLOW.md) | 에이전트 간 대화 아키텍처 |
| [A2A_INTEGRATION.md](docs/A2A_INTEGRATION.md) | 기존 A2A와 통합 방법 |
| [AGENTS.md](docs/AGENTS.md) | 에이전트 역할 정의 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 전체 시스템 아키텍처 |

> **Note for AI Maintainers**: 코드 수정 전 반드시 [MAINTAINER_GUIDE.md](docs/MAINTAINER_GUIDE.md)를 읽어주세요.

---

## 다음 단계

1. [x] ~~기본 CollaborativeAgent 클래스 구현~~
2. [x] ~~SharedMemory MCP 서버 구현~~
3. [x] ~~Message Bus 구현~~
4. [x] ~~협업 예제 작성~~
5. [x] ~~A2A 에이전트 서버 통합~~ (studio/cli_agent.py)
6. [x] ~~AutoGen Studio UI 연동~~ (studio/websocket_bridge.py)
7. [ ] 실제 Claude CLI 연동 테스트

---

## 🔗 AutoGen Studio 통합

AG-CLI 에이전트를 AutoGen Studio에서 사용하려면:

### 1. 서버 시작

```powershell
# 터미널 1: Message Bus
python mcp/message_bus.py

# 터미널 2: SharedMemory
python mcp/shared_memory.py

# 터미널 3: WebSocket Bridge (UI 연동)
python studio/websocket_bridge.py

# 터미널 4-7: CLI Agents (각 폴더별)
python studio/cli_agent.py --folder db --expertise PostgreSQL --port 8110
python studio/cli_agent.py --folder backend --expertise FastAPI --port 8111
python studio/cli_agent.py --folder frontend --expertise React --port 8112
python studio/cli_agent.py --folder tests --expertise pytest --port 8113
```

### 2. AutoGen Studio에서 사용

1. AutoGen Studio UI 접속: http://127.0.0.1:8081
2. "Build" 탭에서 A2A 에이전트 등록:
   - Name: `cli_db_agent`
   - URL: `http://localhost:8110`
3. 팀 생성 후 `cli_collaboration` 패턴 선택
4. 실행하면 에이전트들이 Claude CLI로 실제 코드 생성!

### 3. 실시간 대화 뷰어

- Message Bus 뷰어: http://localhost:8100/viewer
- WebSocket Bridge 뷰어: http://localhost:8102/viewer

### 포트 정보 (통합)

| 서버 | 포트 | 설명 |
|------|------|------|
| Message Bus | 8100 | 에이전트 대화 |
| SharedMemory | 8101 | 정보 공유 |
| WebSocket Bridge | 8102 | UI 연동 |
| cli_db_agent | 8110 | DB 전문 |
| cli_backend_agent | 8111 | Backend 전문 |
| cli_frontend_agent | 8112 | Frontend 전문 |
| cli_test_agent | 8113 | Test 전문 |

### 파일 구조 (studio/)

```
AG-cli/
├── studio/
│   ├── __init__.py
│   ├── cli_agent.py          # A2A 프로토콜 CLI 에이전트
│   └── websocket_bridge.py   # Message Bus → UI 브릿지
└── ...
```

### AG_Cohub 패턴

`cli_collaboration` 패턴이 `AG_Cohub/patterns/11_cli_collaboration.json`에 추가되었습니다.
이 패턴을 선택하면 4개의 CLI 에이전트가 협업합니다.

---

---

## 🔗 관련 문서

| 문서 | 내용 |
|------|------|
| **AG_Cohub/CLI_AGENT_GUIDE.md** | ⭐ CLI 에이전트 완전 가이드 (패턴 호환성, 트러블슈팅) |
| **AG_Cohub/patterns/12_pseudo_hierarchical.json** | Hierarchical 대안 패턴 |
| **AG_Cohub/patterns/07_debate.json** | 균형 로직 포함 Debate 패턴 |

### CLI 에이전트 패턴 호환성 요약

| 패턴 | 호환 | 이유 |
|------|------|------|
| Sequential | ✅ | RoundRobinGroupChat |
| Selector | ✅ | SelectorGroupChat |
| Reflection | ✅ | RoundRobinGroupChat |
| Debate | ✅ | SelectorGroupChat + 균형로직 |
| Code Execution | ✅ | SelectorGroupChat |
| **Hierarchical** | ❌ | Swarm - handoff 미지원 |
| **Pseudo-Hierarchical** | ✅ | SelectorGroupChat (대안) |

> **상세 분석**: `AG_Cohub/CLI_AGENT_GUIDE.md` 참조

---

*Created: 2025-01-10*
*Updated: 2025-01-11*
*Author: Claude Code*

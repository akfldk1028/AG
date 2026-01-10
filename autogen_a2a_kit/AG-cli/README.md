# AG-CLI: Multi-Claude Autonomous Coding System

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

## 다음 단계

1. [ ] 기본 FolderSpecialistAgent 클래스 구현
2. [ ] SharedMemory MCP 서버 구현
3. [ ] 오케스트레이터 프로토타입
4. [ ] 간단한 예제 (Todo App) 테스트
5. [ ] A2A 통합
6. [ ] AutoGen Studio UI 연동

---

*Created: 2025-01-10*
*Author: Claude Code*

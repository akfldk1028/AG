# AG_action - 모듈형 Claude Action 시스템

> **비전**: 두 가지 Action 유형으로 완전한 자동화
> 1. **Direct Actions**: 빌드, 테스트 등 반복 작업 (subprocess)
> 2. **Computer Use Actions**: GUI 자동화 (Claude API 직접 호출)

---

## 핵심 개념: Computer Use = 진짜 Action!

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Action의 두 가지 유형                           │
├───────────────────────────┬─────────────────────────────────────────┤
│     Direct Actions        │      Computer Use Actions               │
│  (빌드/테스트/배포)        │      (GUI 자동화)                        │
├───────────────────────────┼─────────────────────────────────────────┤
│  • subprocess.run()       │  • Claude API 직접 호출                  │
│  • npm build, pytest      │  • screenshot, click, type              │
│  • 결정론적, 빠름          │  • FSM 기반 상태 관리                    │
│  • MCP 불필요             │  • MCP 불필요! (beta header만 필요)      │
└───────────────────────────┴─────────────────────────────────────────┘
```

**중요**: Computer Use는 MCP가 아닌 **Claude API 직접 호출**!
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    tools=[{"type": "computer_20250124", ...}],
    betas=["computer-use-2025-01-24"],  # beta header만 있으면 됨!
)
```

---

## 연구 기반

### 핵심 논문 & 프레임워크

| 출처 | 핵심 인사이트 |
|------|-------------|
| [arXiv 2512.08769](https://arxiv.org/abs/2512.08769) | Production-Grade Agentic AI의 9가지 원칙 |
| [wshobson/agents](https://github.com/wshobson/agents) | 99개 에이전트, 107개 스킬의 모듈형 구조 |
| [claude-flow](https://github.com/ruvnet/claude-flow) | Multi-agent swarm 오케스트레이션 |
| [MCP Protocol](https://ijcesen.com/index.php/ijcesen/article/view/3678) | Tool, Resource, Prompt primitives |

### 9가지 Production 원칙 (arXiv 2512.08769)

```
1. Tool Calls Over MCP     - 직접 함수 호출이 MCP보다 안정적
2. Direct Function Calls   - 비추론 작업은 LLM 없이 직접 실행
3. Single Tool Per Agent   - 에이전트당 도구 1개로 복잡도 감소
4. Single Responsibility   - 하나의 개념적 작업만 담당
5. Externalized Prompts    - 프롬프트를 코드에서 분리
6. Responsible AI          - 멀티모델 합의로 환각 감소
7. Workflow ↔ MCP 분리    - 워크플로우와 MCP 서버 독립
8. Containerized Deploy    - Docker/K8s로 재현 가능한 배포
9. KISS                    - 단순함 유지, 복잡 로직은 LLM에게
```

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AG_action Architecture                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │  AutoGen Studio │  ←──── UI에서 Action 선택                              │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────┐        ┌─────────────────┐                            │
│   │  Action Agent   │◄──────►│  Action Registry│  ← 사용 가능한 액션 목록     │
│   │   (A2A:8120)    │        └─────────────────┘                            │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                      Action Executor                             │       │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │       │
│   │  │  Build   │  │   Test   │  │  Deploy  │  │  Lint    │ ...    │       │
│   │  │  Action  │  │  Action  │  │  Action  │  │  Action  │        │       │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │       │
│   └───────┼─────────────┼─────────────┼─────────────┼───────────────┘       │
│           │             │             │             │                        │
│           ▼             ▼             ▼             ▼                        │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    Direct Function Calls                         │       │
│   │  subprocess.run() / asyncio.create_subprocess_exec()             │       │
│   │  (LLM 없이 직접 실행 - 원칙 #2)                                   │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Action 구조 (3-Layer Progressive Disclosure)

> wshobson/agents의 스킬 구조를 차용

```yaml
# actions/build/frontend_build.yaml
---
# Layer 1: 메타데이터 (항상 로드 - ~50 tokens)
name: frontend_build
category: build
description: "React/Next.js 프론트엔드 빌드"
triggers:
  - "프론트 빌드"
  - "frontend build"
  - "npm run build"

# Layer 2: 실행 정보 (활성화 시 로드)
execution:
  type: direct  # direct | claude_cli | hybrid
  working_dir: "frontend/"
  commands:
    - "npm install"
    - "npm run build"
  timeout: 300
  retry: 2

# Layer 3: 상세 설정 (필요시 로드)
advanced:
  pre_check:
    - command: "node --version"
      expect: "v18"
  post_check:
    - path: "frontend/dist/index.html"
      exists: true
  on_failure:
    notify: true
    rollback: false
```

---

## Action 카테고리

| 카테고리 | Action 예시 | 실행 방식 |
|---------|------------|----------|
| **build** | frontend_build, backend_build, docker_build | Direct |
| **test** | unit_test, e2e_test, coverage | Direct |
| **lint** | eslint, prettier, black, ruff | Direct |
| **deploy** | vercel_deploy, docker_push, k8s_apply | Direct |
| **db** | migrate, seed, backup | Direct |
| **git** | commit, push, pr_create | Direct |
| **analyze** | bundle_analyze, security_scan | Hybrid |
| **generate** | api_docs, type_gen, schema_gen | Claude CLI |

---

## AutoGen Studio 연동

### Action Agent (A2A)

```python
# AG_action/agents/action_agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def execute_action(action_name: str, params: dict = None) -> dict:
    """Action 실행 - LLM 없이 직접 실행"""
    action = ActionRegistry.get(action_name)
    return action.execute(params)

def list_actions(category: str = None) -> list:
    """사용 가능한 Action 목록"""
    return ActionRegistry.list(category)

action_agent = Agent(
    name="action_agent",
    description="빌드, 테스트, 배포 등 반복 작업 자동화 전문가",
    tools=[
        FunctionTool(execute_action),
        FunctionTool(list_actions),
    ]
)
```

### Gallery 자동 등록

기존 `builder.py` 패턴처럼:
- `AG_action/actions/*.yaml` 자동 스캔
- Action별 메타데이터 추출
- Gallery에 "Action Agent" 등록

---

## 파일 구조

```
AG_action/
├── README.md                     # 이 파일
├── docs/
│   ├── COMPUTER_USE_ARCHITECTURE.md  # ⭐ Computer Use 아키텍처
│   ├── FSM_ARCHITECTURE.md       # FSM 상태 머신 설계
│   ├── ACTION_SPEC.md            # Direct Action YAML 스펙
│   └── STUDIO_INTEGRATION.md     # Studio 연동 가이드
│
├── computer_use/                 # ⭐ Computer Use (Claude API 직접)
│   ├── __init__.py
│   ├── agent_loop.py            # Agent Loop 구현
│   └── tool_executor.py         # tool_use 실행기
│
├── fsm/                          # FSM 상태 관리
│   ├── __init__.py
│   ├── states.py                # State 정의
│   ├── transitions.py           # Transition 로직
│   └── controller.py            # FSM Controller
│
├── primitives/                   # Computer Use Primitives (로컬 실행)
│   ├── __init__.py
│   ├── mouse.py                 # click, move, drag
│   ├── keyboard.py              # type, key
│   ├── screen.py                # screenshot, wait
│   └── executor.py              # 통합 실행기
│
├── actions/                      # Direct Actions (YAML)
│   ├── build/
│   │   ├── frontend_build.yaml
│   │   ├── backend_build.yaml
│   │   └── docker_build.yaml
│   ├── test/
│   │   └── unit_test.yaml
│   ├── lint/
│   │   └── eslint.yaml
│   └── git/
│       └── commit.yaml
│
├── registry/                     # Action Registry
│   ├── __init__.py
│   └── action_registry.py
│
├── agents/                       # A2A Agent
│   ├── __init__.py
│   ├── action_agent.py          # A2A Action Agent (8120)
│   └── executor.py              # Direct Action 실행기
│
└── mcp/                          # MCP Server (옵션 - 외부 도구용)
    ├── __init__.py
    ├── server.py
    └── handlers.py
```

---

## 실행 방식 비교

| 방식 | 언제 사용 | 장점 | 단점 |
|------|----------|------|------|
| **Direct** | 빌드, 테스트, lint | 빠름, 결정론적 | 유연성 낮음 |
| **Claude CLI** | 코드 생성, 분석 | 유연함, 컨텍스트 인식 | 느림, 비용 |
| **Hybrid** | 분석 → 실행 | 균형 | 복잡도 증가 |

### Direct 실행 (권장 - 원칙 #2)

```python
async def execute_direct(action: Action) -> Result:
    """LLM 없이 직접 실행 - 비추론 작업용"""
    for cmd in action.commands:
        proc = await asyncio.create_subprocess_exec(
            *cmd.split(),
            cwd=action.working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return Result(success=False, error=stderr.decode())
    return Result(success=True)
```

---

## 진행 현황

### Phase 1: 기본 인프라 ✅
- [x] Action YAML 스펙 정의
- [x] ActionRegistry 구현
- [x] Direct Executor 구현

### Phase 2: Computer Use ✅
- [x] FSM 상태 머신 설계
- [x] Computer Use Primitives (mouse, keyboard, screen)
- [x] Claude API 직접 호출 Agent Loop
- [x] Tool Executor (computer, bash, text_editor)
- [x] Prompt Caching 지원 (GA - 비용 90%, 지연 85% 절감)

### Phase 3: Resolution Scaling ✅
- [x] ScalingTarget enum (XGA 1024x768, WXGA 1280x800)
- [x] ScalingInfo dataclass (좌표 변환)
- [x] screenshot_scaled() 메서드
- [x] Claude 좌표 → 원본 화면 좌표 변환

### Phase 4: Clean Architecture ✅
- [x] JSON Schema 검증 (action.schema.json)
- [x] 상대 import로 통일 (sys.path hack 제거)
- [x] Python 3.8+ 호환성
- [x] 순환 의존성 없는 import chain

### Phase 5: 핵심 Actions ✅
- [x] build/frontend_build.yaml
- [x] build/backend_build.yaml
- [x] test/unit_test.yaml
- [x] lint/eslint.yaml

### Phase 6: AutoGen Studio 연동 ✅
- [x] Action Agent (A2A) 구현
- [x] AutoGen Studio Gallery 연동
- [x] ag_action 어댑터 모듈 (autogenstudio/ag_action/)
- [x] FunctionTool 변환 (execute_action, list_actions, get_action_info)
- [x] Action Agent Team 등록

### Phase 7: 고급 기능 (예정)
- [ ] Action 체이닝 (build → test → deploy)
- [ ] Computer Use + Direct Action 통합
- [ ] 롤백 메커니즘
- [ ] Playwright 테스트 통합

---

## 포트 계획

| 서비스 | 포트 | 설명 |
|--------|------|------|
| action_agent | 8120 | A2A Action Agent |
| action_registry | 8121 | REST API (옵션) |

---

## 참고 자료

### Computer Use (핵심!)
- [Computer Use Tool Docs](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use) - 공식 문서
- [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo) - 공식 데모
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - 에이전트 설계 원칙

### 논문
- [Production-Grade Agentic AI Workflows](https://arxiv.org/abs/2512.08769) - 9가지 원칙
- [AI Agents vs. Agentic AI Taxonomy](https://arxiv.org/html/2505.10468v1)

### 프레임워크
- [wshobson/agents](https://github.com/wshobson/agents) - 99 agents, 107 skills
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25) - MCP 프로토콜 (외부 도구용)

### 공식 문서
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

---

---

## Version History

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 0.5.0 | 2025-01-13 | **AutoGen Studio 연동** - ag_action 어댑터, Gallery 등록 |
| 0.4.1 | 2025-01-13 | ExecutionType export 수정, Python 3.8 호환성 |
| 0.4.0 | 2025-01-13 | JSON Schema 검증, Clean imports |
| 0.3.0 | 2025-01-13 | Resolution Scaling (XGA/WXGA) |
| 0.2.0 | 2025-01-12 | FSM 통합, Prompt Caching |
| 0.1.0 | 2025-01-12 | 초기 버전, Computer Use Agent |

---

## AutoGen Studio 연동

AG_action은 AutoGen Studio Gallery에 자동 등록됩니다.

### 등록되는 컴포넌트

| 컴포넌트 | 타입 | 설명 |
|---------|------|------|
| Execute Action Tool | Tool | Direct Action 실행 (빌드, 테스트, 배포) |
| List Actions Tool | Tool | 사용 가능한 Action 목록 조회 |
| Get Action Info Tool | Tool | Action 상세 정보 조회 |
| Action Agent | Agent | Direct Action 실행 전문가 에이전트 |
| Action Agent Team | Team | Action Agent 단독 팀 |

### 어댑터 모듈 구조

```
autogenstudio/
├── ag_action/              # ★ AG_action 어댑터 모듈
│   ├── __init__.py        # 경로 탐색 + AG_action import
│   └── tools.py           # FunctionTool 정의
└── gallery/
    └── builder.py         # Gallery 등록 (AG_ACTION_AVAILABLE 체크)
```

### 경로 탐색 우선순위

1. **환경변수**: `AG_ACTION_PATH` 설정 시 해당 경로 사용
2. **상위 디렉토리 탐색**: `__file__`에서 15단계까지 AG_action 폴더 탐색
3. **하드코딩 경로**: 개발용 fallback (`D:/Data/22_AG/autogen_a2a_kit`)

---

*Created: 2025-01-12*
*Updated: 2025-01-13 - v0.5.0 AutoGen Studio Gallery 연동 완료*
*Key Insight: Computer Use = Claude API 직접 호출 (MCP 불필요)*

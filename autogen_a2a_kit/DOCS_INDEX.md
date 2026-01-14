# DOCS_INDEX.md - 프로젝트 문서 색인

**AutoGen A2A Kit** 문서 전체 목차입니다.
AI 어시스턴트는 이 파일부터 읽으세요!

---

## 🚀 QUICK START (5분 안에 실행!)

### 1단계: 환경 설정
```powershell
cd D:\Data\22_AG\autogen_a2a_kit

# .env 파일 생성 (API 키 설정)
copy .env.example .env
# .env 파일 열어서 OPENAI_API_KEY 입력!
```

### 2단계: 의존성 설치
```powershell
pip install -r requirements.txt
```

### 3단계: A2A 에이전트 시작 (8개)
```powershell
# 모든 에이전트 일괄 시작
start_all_agents.bat
```

### 4단계: AutoGen Studio 시작
```powershell
# 새 터미널에서
start_studio.bat
```

### 5단계: 접속
- **Studio**: http://127.0.0.1:8081
- **A2A Registry**: http://127.0.0.1:8081/api/a2a/registry

### 포트 요약
| Agent | Port |
|-------|------|
| poetry_agent | 8003 |
| philosophy_agent | 8004 |
| history_agent | 8005 |
| calculator_agent | 8006 |
| math_agent | 8007 |
| graphics_agent | 8008 |
| gpu_agent | 8009 |
| **gui_test_agent** | **8120** |
| **Studio** | **8081** |

---

## FOR AI ASSISTANTS - 읽기 순서

```
1️⃣ 이 파일 (DOCS_INDEX.md) - 전체 구조 파악
2️⃣ .claude/CLAUDE.md - 프로젝트 컨텍스트
3️⃣ 작업 유형에 따라 해당 섹션으로 이동
```

---

## 📚 문서 카테고리

### 🚀 시작하기 (Quick Start)

| 파일 | 설명 | 읽는 시점 |
|------|------|----------|
| **`.claude/CLAUDE.md`** | 프로젝트 전체 컨텍스트, 폴더 구조, 핵심 개념 | 항상 먼저! |
| `README.md` | 프로젝트 소개 및 설치 가이드 | 처음 접할 때 |

---

### 🤖 CLI 에이전트 (Claude Code 기반)

> Claude Code CLI를 A2A로 래핑한 에이전트 관련

| 파일 | 설명 | 핵심 내용 |
|------|------|----------|
| **`AG_Cohub/CLI_AGENT_GUIDE.md`** | ⭐ CLI 에이전트 완전 가이드 | 패턴 호환성, 트러블슈팅, 테스트 결과 |
| `AG-cli/README.md` | AG-cli 프로젝트 개요 | 설치, 실행 방법 |
| `AG-cli/docs/AGENTS.md` | CLI 에이전트 상세 스펙 | 도구 정의, 설정 |
| `AG-cli/docs/ARCHITECTURE.md` | 시스템 아키텍처 | 전체 구조 다이어그램 |

**CLI 작업시 필수 읽기**: `CLI_AGENT_GUIDE.md` → `AGENTS.md`

---

### 🎭 패턴 시스템 (Multi-Agent Collaboration)

> 멀티 에이전트 협업 패턴 정의 및 구현

| 파일 | 설명 | 핵심 내용 |
|------|------|----------|
| **`AG_Cohub/README.md`** | CoHub 시스템 개요 | 패턴 개념, 사용법 |
| `AG_Cohub/patterns/README.md` | 패턴 JSON 정의 가이드 | CLI 호환성, 스키마 |
| `AG_Cohub/loader/README.md` | JSON → AutoGen 변환 | 로더 동작 원리 |
| `AG_Cohub/templates/README.md` | 에이전트 템플릿 | 기본 설정값 |

**패턴 추가시 필수 읽기**: `AG_Cohub/README.md` → `patterns/README.md`

---

### 🔗 A2A 에이전트 (Google ADK 기반)

> Python A2A 에이전트 예제

| 파일 | 설명 | 핵심 내용 |
|------|------|----------|
| **`a2a_demo/README.md`** | A2A 에이전트 예제 | Calculator, Poet, History |
| `a2a_demo/gui_test_agent/` | **GUI 테스트 에이전트** | PyAutoGUI 기반, 포트 8120 |
| `AG-cli/docs/A2A_INTEGRATION.md` | A2A 통합 가이드 | FunctionTool 호출 흐름 |

---

### 🖥️ AG-mcp (MCP 서버) - NEW!

> Claude Code용 MCP 서버 (API Key 불필요!)

| 파일 | 설명 | 핵심 내용 |
|------|------|----------|
| **`AG-mcp/README.md`** | ⭐ PyAutoGUI MCP 개요 | 설치, 사용법, 도구 목록 |
| `AG-mcp/pyautogui_mcp/server.py` | MCP 서버 본체 | 12개 도구 (스크린샷, 마우스, 키보드) |
| `AG-mcp/pyautogui_mcp/config.py` | 설정 파일 | AG_action 경로 설정 |
| `AG-mcp/setup_venv.bat` | 가상환경 설정 | 최초 1회 실행 |
| `AG-mcp/start_mcp.bat` | MCP 시작 스크립트 | Claude Code 연동용 |

**MCP 도구 12개**:
- `screenshot`, `screenshot_scaled` - 화면 캡처
- `mouse_click`, `mouse_move`, `mouse_drag`, `mouse_scroll` - 마우스
- `keyboard_type`, `keyboard_key`, `keyboard_hotkey` - 키보드
- `locate_image` - 이미지로 UI 요소 찾기
- `get_screen_size`, `get_pixel_color` - 화면 정보

**Claude Code 연동**:
```bash
claude mcp add pyautogui-mcp "D:\Data\22_AG\autogen_a2a_kit\AG-mcp\start_mcp.bat"
```

---

### ⚡ AG_action (모듈형 Action 시스템) - NEW!

> 빌드, 테스트, 배포 등 반복 작업 자동화

| 파일 | 설명 | 핵심 내용 |
|------|------|----------|
| **`AG_action/README.md`** | ⭐ Action 시스템 개요 | 아키텍처, 연구 기반 |
| `AG_action/docs/ACTION_SPEC.md` | Action YAML 스펙 | 3-Layer Progressive Disclosure |
| `AG_action/docs/STUDIO_INTEGRATION.md` | Studio 연동 가이드 | A2A 등록, 패턴 통합 |
| `AG_action/actions/*.yaml` | Action 정의 파일들 | build, test, lint, git |

**Action 작업시 필수 읽기**: `AG_action/README.md` → `ACTION_SPEC.md`

**연구 기반**:
- [arXiv 2512.08769](https://arxiv.org/abs/2512.08769) - Production-Grade Agentic AI
- [wshobson/agents](https://github.com/wshobson/agents) - 99 agents, 107 skills

---

### 🏗️ 아키텍처 (심화)

> 시스템 설계 및 유지보수

| 파일 | 설명 | 읽는 시점 |
|------|------|----------|
| `AG-cli/docs/ARCHITECTURE.md` | 전체 아키텍처 | 시스템 이해 필요시 |
| `AG-cli/docs/COLLABORATIVE_FLOW.md` | 협업 플로우 상세 | 메시지 흐름 분석시 |
| `AG-cli/docs/MAINTAINER_GUIDE.md` | 유지보수 가이드 | 코드 수정시 |

---

### 🔧 autogen_source (수정된 AutoGen Studio)

> **외부 소스 코드** - Microsoft AutoGen Studio를 포크하여 수정한 파일들

| 폴더 | 설명 | 수정 이유 |
|------|------|----------|
| `autogen_source/.../autogenstudio/` | 백엔드 Python | A2A 통합, Gallery 빌더 |
| `autogen_source/.../frontend/` | 프론트엔드 React | 패턴 UI, 에이전트 플로우 |

**주요 수정 파일**:
```
autogen_source/python/packages/autogen-studio/
├── autogenstudio/
│   ├── a2a/                    # A2A 레지스트리, 클라이언트
│   ├── gallery/builder.py      # 자동 Gallery 생성
│   └── teammanager/            # 팀 실행 로직
│
└── frontend/src/components/
    └── views/playground/chat/
        ├── agentflow/          # 패턴 시각화
        │   └── patterns/       # 패턴 JSON 로더
        └── team-runtime/       # 팀 팩토리
```

> ⚠️ autogen_source는 **외부 코드**입니다. 수정 시 원본과 충돌 주의!

---

## 🗂️ 전체 파일 목록 (알파벳순)

```
autogen_a2a_kit/
├── .claude/
│   └── CLAUDE.md                    # 🌟 프로젝트 컨텍스트
├── DOCS_INDEX.md                    # 📚 이 파일
├── README.md                        # 프로젝트 소개
│
├── AG_Cohub/
│   ├── README.md                    # CoHub 개요
│   ├── CLI_AGENT_GUIDE.md           # 🌟 CLI 에이전트 가이드
│   ├── patterns/
│   │   └── README.md                # 패턴 JSON 가이드
│   ├── loader/
│   │   └── README.md                # 로더 설명
│   └── templates/
│       └── README.md                # 템플릿 설명
│
├── AG-cli/
│   ├── README.md                    # AG-cli 개요
│   └── docs/
│       ├── AGENTS.md                # 에이전트 스펙
│       ├── ARCHITECTURE.md          # 아키텍처
│       ├── A2A_INTEGRATION.md       # A2A 통합
│       ├── COLLABORATIVE_FLOW.md    # 협업 플로우
│       └── MAINTAINER_GUIDE.md      # 유지보수
│
├── a2a_demo/
│   ├── README.md                    # A2A 예제
│   ├── gui_test_agent/              # 🖥️ GUI 테스트 에이전트 (포트 8120)
│   ├── calculator_agent/            # 계산기 (포트 8006)
│   ├── poetry_agent/                # 시/문학 (포트 8003)
│   ├── philosophy_agent/            # 철학 (포트 8004)
│   ├── history_agent/               # 역사 (포트 8005)
│   ├── math_agent/                  # 수학 (포트 8007)
│   ├── graphics_agent/              # 그래픽스 (포트 8008)
│   └── gpu_agent/                   # GPU (포트 8009)
│
├── AG-mcp/                          # 🖥️ MCP 서버 (NEW!)
│   ├── README.md                    # 🌟 PyAutoGUI MCP 개요
│   ├── pyautogui_mcp/
│   │   ├── server.py                # MCP 서버 (12개 도구)
│   │   ├── config.py                # 설정
│   │   └── requirements.txt         # 의존성
│   ├── setup_venv.bat               # 가상환경 설정
│   └── start_mcp.bat                # MCP 시작
│
├── AG_action/                       # ⚡ 모듈형 Action 시스템 (NEW!)
│   ├── README.md                    # 🌟 Action 시스템 개요
│   ├── docs/
│   │   ├── ACTION_SPEC.md           # Action YAML 스펙
│   │   └── STUDIO_INTEGRATION.md    # Studio 연동
│   ├── actions/                     # Action 정의 (YAML)
│   │   ├── build/                   # 빌드 Actions
│   │   ├── test/                    # 테스트 Actions
│   │   ├── lint/                    # 린트 Actions
│   │   └── git/                     # Git Actions
│   ├── registry/                    # Action Registry
│   └── agents/                      # A2A Action Agent
│
└── autogen_source/.../autogen-studio/
    ├── README.md                    # 원본 AutoGen Studio
    ├── autogenstudio/               # 백엔드 (수정됨)
    └── frontend/                    # 프론트엔드 (수정됨)
```

---

## 🔍 작업별 빠른 참조

| 작업 | 읽어야 할 문서 |
|------|---------------|
| **CLI 에이전트 추가** | CLAUDE.md → CLI_AGENT_GUIDE.md → AGENTS.md |
| **새 패턴 만들기** | CLAUDE.md → AG_Cohub/README.md → patterns/README.md |
| **A2A 에이전트 추가** | CLAUDE.md → a2a_demo/README.md → A2A_INTEGRATION.md |
| **버그 수정** | CLAUDE.md → ARCHITECTURE.md → 해당 코드 |
| **전체 이해** | CLAUDE.md → 이 파일 → 관심 섹션 순회 |
| **Frontend 수정** | CLAUDE.md → autogen_source 섹션 → frontend/ |
| **Backend 수정** | CLAUDE.md → autogen_source 섹션 → autogenstudio/ |
| **Action 추가** | AG_action/README.md → ACTION_SPEC.md → actions/ |
| **빌드/테스트 자동화** | AG_action/README.md → STUDIO_INTEGRATION.md |
| **GUI 테스트 에이전트** | AG-mcp/README.md → a2a_demo/gui_test_agent/ |
| **MCP 서버 추가** | AG-mcp/README.md → setup_venv.bat → start_mcp.bat |

---

## ⚠️ 중요 참고사항

### CLI 에이전트 패턴 호환성

| 패턴 | 호환 | 비고 |
|------|------|------|
| Sequential | ✅ | RoundRobinGroupChat |
| Selector | ✅ | SelectorGroupChat |
| Debate | ✅ | 균형 로직 포함 |
| Reflection | ✅ | RoundRobinGroupChat |
| **Hierarchical** | ❌ | Swarm - handoff 미지원 |
| **Pseudo-Hierarchical** | ✅ | 대안 패턴 |

> 상세: `AG_Cohub/CLI_AGENT_GUIDE.md` 참조

---

*Last Updated: 2026-01-13*
*Total Docs: 20+ files (AG_action + AG-mcp + autogen_source 수정 파일들)*

---

## 📊 A2A 에이전트 포트 요약

| Agent | Port | 설명 |
|-------|------|------|
| poetry_agent | 8003 | 시/문학 |
| philosophy_agent | 8004 | 철학 |
| history_agent | 8005 | 역사 |
| calculator_agent | 8006 | 계산 |
| math_agent | 8007 | 수학 |
| graphics_agent | 8008 | 컴퓨터 그래픽스 |
| gpu_agent | 8009 | GPU/병렬컴퓨팅 |
| cli_db_agent | 8110 | Claude CLI - DB |
| cli_backend_agent | 8111 | Claude CLI - Backend |
| **gui_test_agent** | **8120** | **GUI 자동화 (PyAutoGUI)** |

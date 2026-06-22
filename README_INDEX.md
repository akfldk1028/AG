# AG README INDEX

AG 프로젝트 문서 인덱스. 멀티에이전트 시스템 허브의 전체 구조와 문서를 안내합니다.

## 프로젝트 개요

AG는 18개 이상의 AI 에이전트 프로젝트와 AutoGen Studio A2A 통합을 포함하는 멀티에이전트 시스템 허브입니다.

```
AG/
├── agent/              # 18개+ 개별 에이전트 프로젝트
├── agent_core/         # 재사용 가능한 코어 라이브러리
├── autogen_a2a_kit/    # AutoGen + A2A 통합 시스템 + Claude SDK
│   └── AG_Cohub/       # 모델 팩토리 + SDK 패키지
├── Auto-Claude/        # 24/7 자율 코딩 (Electron + CLI)
└── templates/          # 빠른 시작 템플릿

JSON_MODULES/           # 62+ AutoGen 컴포넌트 JSON (별도 루트)
```

---

## 루트 레벨 문서

| 파일 | 설명 |
|------|------|
| [README.md](README.md) | 프로젝트 메인 README |
| [README_INDEX.md](README_INDEX.md) | 이 파일 - 문서 인덱스 |

---

## agent/ 문서

18개 이상의 AI 에이전트 프로젝트 모음.

### 메인 문서

| 경로 | 설명 |
|------|------|
| [agent/README_INDEX.md](agent/README_INDEX.md) | 에이전트 프로젝트 인덱스 (★ 핵심) |
| [agent/README_KO.md](agent/README_KO.md) | 전체 프로젝트 가이드 (한국어) |
| [agent/LANGGRAPH_USAGE_GUIDE.md](agent/LANGGRAPH_USAGE_GUIDE.md) | LangGraph 사용법 |
| [agent/SETUP_GUIDE.md](agent/SETUP_GUIDE.md) | 설정 가이드 |

### 프로젝트별 README

#### 입문 레벨
| 경로 | 프레임워크 | 설명 |
|------|-----------|------|
| [agent/my-first-agent/](agent/my-first-agent/) | OpenAI SDK | 기본 에이전트 학습 |
| [agent/hello-langgraph/](agent/hello-langgraph/) | LangGraph | 시 작성 봇 |

#### 중급 레벨
| 경로 | 프레임워크 | 설명 |
|------|-----------|------|
| [agent/chatgpt-clone/](agent/chatgpt-clone/) | OpenAI + Streamlit | ChatGPT 클론 |
| [agent/customer-support-agent/](agent/customer-support-agent/) | OpenAI + Streamlit | 고객 지원 멀티에이전트 |
| [agent/tutor-agent/](agent/tutor-agent/) | LangGraph | AI 튜터 시스템 |
| [agent/workflow-architectures/](agent/workflow-architectures/) | LangGraph | 워크플로우 패턴 |
| [agent/multi-agent-architectures/](agent/multi-agent-architectures/) | LangGraph | 멀티에이전트 패턴 |

#### 고급 레벨
| 경로 | 프레임워크 | 설명 |
|------|-----------|------|
| [agent/financial-analyst/](agent/financial-analyst/) | Google ADK | 금융 분석 |
| [agent/a2a/](agent/a2a/) | ADK + LangGraph | 에이전트 간 통신 |
| [agent/deep-research-clone/](agent/deep-research-clone/) | AutoGen | 심층 리서치 |
| [agent/law-domain-agents/](agent/law-domain-agents/) | LangGraph + A2A | 법률 검색 (★ 핵심) |

#### 콘텐츠 생성
| 경로 | 프레임워크 | 설명 |
|------|-----------|------|
| [agent/youtube-thumbnail-maker/](agent/youtube-thumbnail-maker/) | LangGraph | 썸네일 생성 |
| [agent/youtube-shorts-maker/](agent/youtube-shorts-maker/) | Google ADK | Shorts 제작 |
| [agent/content-pipeline-agent/](agent/content-pipeline-agent/) | CrewAI | 콘텐츠 자동화 |

#### 유틸리티
| 경로 | 프레임워크 | 설명 |
|------|-----------|------|
| [agent/email-refiner-agent/](agent/email-refiner-agent/) | Google ADK | 이메일 개선 |
| [agent/job-hunter-agent/](agent/job-hunter-agent/) | CrewAI | 구직 자동화 |
| [agent/news-reader-agent/](agent/news-reader-agent/) | CrewAI | 뉴스 수집 |
| [agent/deployment/](agent/deployment/) | OpenAI | 프로덕션 배포 |

### 쿡북 (Cookbook)

| 경로 | 설명 |
|------|------|
| [agent/cookbook/a2a_mcp/](agent/cookbook/a2a_mcp/) | A2A + MCP 연동 |
| [agent/cookbook/google-adk/](agent/cookbook/google-adk/) | Google ADK 레시피 |
| [agent/cookbook/langchain/](agent/cookbook/langchain/) | LangChain 레시피 |
| [agent/cookbook/prompting/](agent/cookbook/prompting/) | 프롬프팅 기법 |

---

## agent_core/ 문서

재사용 가능한 에이전트 코어 라이브러리.

| 경로 | 설명 |
|------|------|
| [agent_core/README.md](agent_core/README.md) | 코어 라이브러리 사용법 |

### 핵심 기능
- `create_agent()` - 에이전트 생성
- `run_a2a_server()` - A2A 서버 실행
- config.yaml 기반 설정

---

## autogen_a2a_kit/ 문서

AutoGen Studio와 A2A 프로토콜 통합 시스템.

### 메인 문서

| 경로 | 설명 |
|------|------|
| [autogen_a2a_kit/README.md](autogen_a2a_kit/README.md) | 통합 시스템 메인 가이드 (★ 핵심, 1500줄) |

### 서브 시스템

| 경로 | 설명 |
|------|------|
| [autogen_a2a_kit/AG-cli/README.md](autogen_a2a_kit/AG-cli/README.md) | Claude CLI 협업 시스템 |
| [autogen_a2a_kit/AG-mcp/README.md](autogen_a2a_kit/AG-mcp/README.md) | MCP 통합 |
| [autogen_a2a_kit/AG_Cohub/README.md](autogen_a2a_kit/AG_Cohub/README.md) | 협업 허브 |
| [autogen_a2a_kit/AG_action/README.md](autogen_a2a_kit/AG_action/README.md) | GitHub Actions |
| [autogen_a2a_kit/a2a_demo/README.md](autogen_a2a_kit/a2a_demo/README.md) | A2A 데모 에이전트 |
| [autogen_a2a_kit/patches/README.md](autogen_a2a_kit/patches/README.md) | AutoGen 패치 |

### AG_Cohub 하위 문서

| 경로 | 설명 |
|------|------|
| [autogen_a2a_kit/AG_Cohub/loader/README.md](autogen_a2a_kit/AG_Cohub/loader/README.md) | 패턴 로더 |
| [autogen_a2a_kit/AG_Cohub/patterns/README.md](autogen_a2a_kit/AG_Cohub/patterns/README.md) | 팀 협업 패턴 |
| [autogen_a2a_kit/AG_Cohub/templates/README.md](autogen_a2a_kit/AG_Cohub/templates/README.md) | 패턴 템플릿 |

### AutoGen Source 문서

| 경로 | 설명 |
|------|------|
| [autogen_a2a_kit/autogen_source/README.md](autogen_a2a_kit/autogen_source/README.md) | AutoGen 소스 |
| [autogen_a2a_kit/autogen_source/python/README.md](autogen_a2a_kit/autogen_source/python/README.md) | Python 패키지 |

---

## templates/ 문서

A2A 통합 빠른 시작 템플릿.

| 경로 | 설명 |
|------|------|
| [templates/QUICK_START.md](templates/QUICK_START.md) | A2A 빠른 시작 가이드 |
| [templates/a2a_integration_template.py](templates/a2a_integration_template.py) | 통합 템플릿 코드 |
| [templates/a2a_minimal.py](templates/a2a_minimal.py) | 최소 구현 예제 |

---

## 서비스 포트 맵

### A2A 에이전트 (autogen_a2a_kit/a2a_demo/)

| Port | Agent | 용도 |
|------|-------|------|
| 8003 | poetry_agent | 시/문학 |
| 8004 | philosophy_agent | 철학 |
| 8005 | history_agent | 역사 |
| 8006 | calculator_agent | 계산 |
| 8007 | math_agent | 수학 |
| 8008 | graphics_agent | 그래픽 |
| 8009 | gpu_agent | GPU 연산 |
| 8120 | gui_test_agent | GUI 자동화 |

### 핵심 서비스

| Port | Service | 용도 |
|------|---------|------|
| 8081 | AutoGen Studio | 멀티에이전트 UI |
| 8100 | Message Bus | AG-CLI 대화 라우팅 |
| 8101 | SharedMemory | AG-CLI 정보 공유 |

### agent/ 프로젝트

| Port | Project | 프레임워크 |
|------|---------|-----------|
| 8101 | hello-langgraph | LangGraph |
| 8102 | tutor-agent | LangGraph |
| 8103 | multi-agent-architectures | LangGraph |
| 8501 | chatgpt-clone | Streamlit |
| 8502 | customer-support-agent | Streamlit |
| 8010-8015 | law-domain-agents | LangGraph + A2A |

---

## JSON_MODULES/ 문서

62개+ AutoGen 컴포넌트 JSON 파일 (teams, agents, models, terminations).

| 경로 | 설명 |
|------|------|
| [../JSON_MODULES/README.md](../JSON_MODULES/README.md) | 모듈 구조 가이드 |
| [../JSON_MODULES/cohub_gallery.json](../JSON_MODULES/cohub_gallery.json) | 5개 Gallery 팀 (Sequential, Selector, Handoff, Debate, Reflection) |
| [../JSON_MODULES/validate_json.py](../JSON_MODULES/validate_json.py) | 62개 파일 전수 검증 |

### 컴포넌트 현황
- agents: 12개 (auto_claude 7 + pattern 5)
- models: 7개 (Claude 3 + OpenAI 2 + Mistral 1 + Azure 1)
- teams: 20개+
- patterns: 14개
- templates: 6개 (5 기본 + auto_claude_dev_team)

---

## Claude Agent SDK (AG_Cohub/sdk/)

모듈화된 SDK 패키지 (2026-02-06 리팩토링).

| 모듈 | 설명 |
|------|------|
| `sdk/auth.py` | OAuth 토큰 관리 |
| `sdk/config.py` | ToolProfile, AgentConfig, ROLE_PRESETS |
| `sdk/client.py` | ClaudeSDK 래퍼 (query + conversation) |
| `sdk/context.py` | ProjectContext + ContextManager |
| `sdk/hooks.py` | quality/logging/budget/security 훅 |
| `sdk/tools.py` | MCP 도구 스키마 |

### ToolProfile 시스템
| Profile | 도구 | 용도 |
|---------|------|------|
| TEXT_ONLY | `tools=[]` | 순수 텍스트 응답 |
| READER | Read, Glob, Grep, WebSearch | 읽기 전용 분석 |
| CODER | Read, Write, Edit, Bash, Glob, Grep | 코드 작성/실행 |
| FULL_AGENT | `tools=None` (모든 도구) | 완전 자율 에이전트 |

### Plan Mode (`permission_mode: "plan"`)
- Claude Code의 공식 plan mode 활용
- Read/Glob/Grep만 가능, Write/Edit/Bash 차단
- Planner 에이전트가 분석 후 구현 계획 생성
- Coder 에이전트가 계획을 실행

---

## 관련 프로젝트

| 프로젝트 | 위치 | 설명 |
|----------|------|------|
| Auto-Claude | [Auto-Claude/](Auto-Claude/) | 24/7 자율 코딩 (Electron + CLI) |

> AG-ACE-BRIDGE는 2026-02-06 삭제됨. 기능은 Auto-Claude에 통합.

---

## E2E 테스트 현황 (2026-02-07)

| 팀 | 패턴 | 결과 | Run# |
|----|------|------|------|
| Sequential | RoundRobinGroupChat | PASS | - |
| Selector | SelectorGroupChat | PASS | - |
| Handoff | Swarm | PASS | #177 |
| Debate | SelectorGroupChat | PASS | #178 |
| Reflection | RoundRobinGroupChat | PASS | #152 |
| **Tool Execution** | Auto-Claude Dev Team | PASS | #182 |

---

## 변경 이력

- 2026-02-07: Tool execution PASS, plan mode 추가, SDK 패키지 문서화
- 2026-02-06: AG-ACE-BRIDGE 삭제, Auto-Claude AG/로 이동, SDK 모듈화
- 2025-01-23: README.md, README_INDEX.md 생성
- 2025-01-21: agent/README_INDEX.md 생성

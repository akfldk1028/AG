# DOCS_INDEX.md - 프로젝트 문서 색인

**AutoGen A2A Kit** 문서 전체 목차입니다.
AI 어시스턴트는 이 파일부터 읽으세요!

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
| `AG-cli/docs/A2A_INTEGRATION.md` | A2A 통합 가이드 | FunctionTool 호출 흐름 |

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
│   └── README.md                    # A2A 예제
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

*Last Updated: 2025-01-11*
*Total Docs: 14 files (+ autogen_source 수정 파일들)*

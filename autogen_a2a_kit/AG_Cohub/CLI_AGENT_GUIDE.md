# CLI A2A 에이전트 가이드

> **이 문서는 CLI 에이전트 관련 모든 작업을 요약합니다.**
> 다음 AI가 빠르게 컨텍스트를 파악할 수 있도록 작성되었습니다.

---

## 1. 개요

### CLI A2A 에이전트란?

Claude Code CLI를 A2A(Agent-to-Agent) 프로토콜로 래핑한 에이전트입니다.
AutoGen Studio에서 다른 에이전트들과 협업할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI A2A Agent Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AutoGen Studio                                                 │
│       ↓ (A2A Protocol - JSON-RPC)                              │
│  Google ADK Agent (cli_agent.py)                               │
│       ↓ (FunctionTool)                                         │
│  execute_claude_cli()                                          │
│       ↓ (subprocess)                                           │
│  Claude Code CLI                                               │
│       ↓ (built-in tools)                                       │
│  [Read] [Write] [Edit] [Glob] [Grep] [Bash]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 현재 실행 중인 에이전트

| Agent | Port | 폴더 | 전문 분야 |
|-------|------|------|-----------|
| cli_db_agent | 8110 | db/ | 데이터베이스, 스키마 |
| cli_backend_agent | 8111 | backend/ | API, 백엔드 로직 |

---

## 2. 파일 구조

```
autogen_a2a_kit/
├── AG-cli/studio/
│   ├── cli_agent.py          # 메인 에이전트 (A2A 서버)
│   ├── config.py             # 설정
│   ├── tools/
│   │   ├── claude_cli.py     # Claude CLI 실행 도구
│   │   ├── file_ops.py       # 파일 작업 도구
│   │   └── shared_folder.py  # 공유 폴더 도구
│   ├── utils/
│   │   └── logging.py        # 로깅 시스템
│   ├── db/                   # cli_db_agent 작업 폴더
│   └── backend/              # cli_backend_agent 작업 폴더
│
├── AG_Cohub/
│   ├── patterns/
│   │   ├── 07_debate.json           # 수정됨: 균형 로직 추가
│   │   ├── 11_cli_collaboration.json # CLI 협업 패턴
│   │   └── 12_pseudo_hierarchical.json # 신규: 의사-계층 패턴
│   └── CLI_AGENT_GUIDE.md           # 이 문서
│
└── autogen_source/.../frontend/
    └── team-runtime/
        └── team-factory.ts          # 수정됨: debate 템플릿
```

---

## 3. 패턴 호환성 테스트 결과

### 테스트 환경
- 팀: default_team17_selector (teamId=21)
- 에이전트: cli_db_agent + cli_backend_agent
- AutoGen Studio: http://127.0.0.1:8081

### 호환성 매트릭스

| 패턴 | Provider | 결과 | 비고 |
|------|----------|------|------|
| Sequential | RoundRobinGroupChat | ✅ 성공 | 순차 실행 |
| Selector/Router | SelectorGroupChat | ✅ 성공 | 동적 라우팅 |
| Reflection | RoundRobinGroupChat | ✅ 성공 | 상호 검토 |
| Multi-Agent Debate | SelectorGroupChat | ✅ 성공 | 토론/비교 |
| Code Execution | SelectorGroupChat | ✅ 성공 | Read→Execute |
| **Hierarchical** | **Swarm** | ❌ **실패** | handoff 미지원 |
| Pseudo-Hierarchical | SelectorGroupChat | ✅ 성공 | 새로 구현 |

### Hierarchical 패턴 실패 원인

```
문제: CLI A2A 에이전트는 Google ADK 기반
      → FunctionTool만 지원
      → handoff/transfer_to_* 함수 없음
      → Swarm Provider와 호환 불가

해결: Pseudo-Hierarchical 패턴 구현
      → SelectorGroupChat 사용
      → selector_prompt가 암묵적 Manager 역할
```

---

## 4. 주요 구현 내용

### 4.1 Pseudo-Hierarchical 패턴 (12_pseudo_hierarchical.json)

CLI 에이전트와 호환되는 의사-계층 구조입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pseudo-Hierarchical Flow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  selector_prompt = 암묵적 PROJECT MANAGER                       │
│       │                                                         │
│       ├── Phase 1 (Analysis)                                    │
│       │   └── cli_db_agent: 요구사항 분석                       │
│       │       → [ANALYSIS REPORT] 출력                          │
│       │                                                         │
│       ├── Phase 2 (Implementation)                              │
│       │   └── cli_backend_agent: 구현                           │
│       │       → [IMPLEMENTATION REPORT] 출력                    │
│       │                                                         │
│       ├── Phase 3 (Verification)                                │
│       │   └── cli_db_agent: 검증                                │
│       │                                                         │
│       └── Phase 4 (Synthesis)                                   │
│           └── 최종 결과 정리                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**실제 Hierarchical vs Pseudo-Hierarchical:**

| 항목 | 실제 Hierarchical | Pseudo-Hierarchical |
|-----|------------------|---------------------|
| Provider | Swarm | SelectorGroupChat |
| 위임 방식 | transfer_to_* 함수 | selector_prompt 판단 |
| Manager | 전용 Agent | selector_prompt 내장 |
| CLI 호환 | ❌ | ✅ |

### 4.2 Debate 균형 로직 (07_debate.json 수정)

**문제:** LLM이 두 에이전트만 계속 선택 (A↔B, C 소외)

**해결:** selector_prompt에 발언 횟수 카운팅 로직 추가

```
=== STEP 1: COUNT SPEAKER TURNS ===
대화 기록에서 각 에이전트 발언 횟수 카운팅

=== STEP 2: BALANCE CHECK ===
최다 발언자 - 최소 발언자 >= 2 이면
→ 최소 발언자 강제 선택 (MANDATORY!)

=== STEP 3: SELECTION RULES ===
1. [MUST] 직전 발언자와 다른 사람 선택
2. [MUST] 발언 횟수 가장 적은 에이전트 우선
3. [MUST] 0회 발언 에이전트 있으면 즉시 선택
```

**예상 결과:**
```
이전: A → B → A → B → A → B (두 명만)
이후: A → B → C → A → B → C (균형 순환)
```

---

## 5. 실행 방법

### CLI 에이전트 시작

```powershell
# cli_db_agent (포트 8110)
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli\studio
python cli_agent.py --port 8110 --folder db

# cli_backend_agent (포트 8111) - 새 터미널
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli\studio
python cli_agent.py --port 8111 --folder backend
```

### AutoGen Studio 시작

```powershell
powershell.exe -Command "Start-Process cmd -ArgumentList '/k', 'D:\\Data\\22_AG\\autogen_a2a_kit\\start_studio.bat'"
```

### 상태 확인

```powershell
# 포트 확인
netstat -an | findstr "LISTENING" | findstr "811"

# 로그 확인 (CLI 에이전트)
GET http://localhost:8110/logs/latest
```

---

## 6. 트러블슈팅

### 6.1 "A2A 호출 실패: All connection attempts failed"

**원인:** CLI 에이전트 서버 미실행

**해결:**
```powershell
# 에이전트 실행 상태 확인
netstat -an | findstr "8110"
netstat -an | findstr "8111"

# 서버 시작
python cli_agent.py --port 8110 --folder db
```

### 6.2 Hierarchical 패턴 "Invalid" 에러

**원인:** CLI A2A 에이전트는 handoff 미지원

**해결:** Pseudo-Hierarchical 패턴 사용
```
패턴 선택 → "Pseudo-Hierarchical (CLI 호환)" 선택
```

### 6.3 Debate에서 두 명만 대화

**원인:** LLM이 selector_prompt 지시를 완벽히 따르지 않음

**해결:** 균형 로직이 포함된 새 selector_prompt 적용됨
- team-factory.ts의 debate 템플릿 수정 완료
- 07_debate.json의 selector_prompt 수정 완료

---

## 7. 관련 코드 위치

### Python (백엔드)

| 파일 | 역할 |
|------|------|
| `AG-cli/studio/cli_agent.py` | CLI A2A 에이전트 메인 |
| `AG-cli/studio/tools/claude_cli.py` | Claude CLI 실행 도구 |
| `autogenstudio/a2a/agent.py` | A2A Agent wrapper |
| `autogenstudio/a2a/registry.py` | 에이전트 레지스트리 |

### TypeScript (프론트엔드)

| 파일 | 역할 |
|------|------|
| `team-runtime/team-factory.ts` | 팀 생성, selector_prompt 생성 |
| `team-runtime/pattern-runtime.ts` | 패턴 적용 로직 |
| `agentflow/patterns/data/*.json` | 패턴 정의 파일 |

### JSON (패턴 정의)

| 파일 | 역할 |
|------|------|
| `07_debate.json` | Debate 패턴 (균형 로직 포함) |
| `11_cli_collaboration.json` | CLI 협업 기본 패턴 |
| `12_pseudo_hierarchical.json` | 의사-계층 패턴 (신규) |

---

## 8. 다음 단계 제안

### 즉시 가능

1. **Pseudo-Hierarchical 테스트**
   - AutoGen Studio에서 패턴 적용 후 테스트
   - 작업: "db 분석하고 backend에 API 만들어줘"

2. **Debate 균형 테스트**
   - 3개 이상 에이전트로 토론
   - 모든 에이전트 골고루 발언하는지 확인

### 추후 개선

1. **실제 Hierarchical 지원**
   - CLI A2A에 handoff 래퍼 추가
   - Google ADK → AutoGen 변환 레이어

2. **더 많은 CLI 에이전트**
   - cli_frontend_agent (포트 8112)
   - cli_test_agent (포트 8113)

3. **SharedMemory 통합**
   - 에이전트 간 컨텍스트 공유
   - API 스펙, 스키마 정보 공유

---

## 9. 빠른 참조

### 포트 맵

```
8081  - AutoGen Studio
8110  - cli_db_agent
8111  - cli_backend_agent
8112  - cli_frontend_agent (예약)
8113  - cli_test_agent (예약)
```

### 패턴 선택 가이드

```
순차 작업       → Sequential
전문가 라우팅   → Selector
코드 리뷰       → Reflection
찬반 토론       → Debate (균형 로직 포함)
코드 실행       → Code Execution
계층적 위임     → Pseudo-Hierarchical ✅ (CLI 호환)
                  (Hierarchical ❌ 사용 불가)
```

### CLI 도구 태그

로그에서 확인 가능한 도구 태그:
```
[TOOL] [READ]  - 파일 읽기
[TOOL] [WRITE] - 파일 생성
[TOOL] [EDIT]  - 파일 수정
[TOOL] [GLOB]  - 파일 검색
[TOOL] [GREP]  - 내용 검색
[TOOL] [BASH]  - 명령 실행
```

---

*최종 업데이트: 2025-01-11*
*작성: Claude Code CLI 테스트 세션*

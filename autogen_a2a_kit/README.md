# AutoGen + A2A Integration Kit

Microsoft AutoGen과 Google A2A(Agent-to-Agent) 프로토콜을 연동한 멀티 에이전트 개발 환경.

---

## FOR AI ASSISTANTS - 반드시 먼저 읽으세요!

> **CRITICAL**: 이 섹션을 완전히 이해한 후 작업하세요. 여기서 설명하는 `name`과 `description` 필드가 **전체 시스템의 핵심**입니다!

### 30초 핵심 이해

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        A2A → Pattern 통합의 핵심                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  A2A agent.py              AutoGen JSON 등록             team-factory.ts    │
│  ┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐│
│  │ name: "..."  │─────────│ config.name      │─────────│ selector_prompt: ││
│  │ description  │─────────│ config.description│─────────│ "- name: desc"   ││
│  │ (에이전트)   │         │ (JSON에 복사!)   │         │ (LLM이 선택!)    ││
│  └──────────────┘         └──────────────────┘         └──────────────────┘│
│                                                                             │
│  ★ name: Selector LLM이 "누구를 선택할지" 판단할 때 사용                     │
│  ★ description: Selector LLM이 "이 에이전트가 뭘 하는지" 파악할 때 사용      │
│                                                                             │
│  이 두 필드가 일치하지 않으면 → 패턴이 제대로 작동하지 않음!                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 이 프로젝트가 뭔가?

```
┌─────────────────────────────────────────────────────────────┐
│                    AutoGen Studio (UI)                       │
│                   http://localhost:8081                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│   │  Pattern    │     │    Team     │     │    A2A      │  │
│   │  System     │────▶│   Config    │◀────│   Agents    │  │
│   │ (협업방식)  │     │ (실행설정)  │     │ (외부연결)  │  │
│   └─────────────┘     └─────────────┘     └─────────────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│   AG_Cohub/           TeamConfig          a2a_demo/        │
│   patterns/           JSON 생성           port 8002-8010   │
└─────────────────────────────────────────────────────────────┘
```

### 핵심 두 시스템

| 시스템 | 역할 | 위치 | 핵심 파일 |
|--------|------|------|-----------|
| **A2A** | 외부 에이전트 서버 연결 | `a2a_demo/` | `agent.py` |
| **Pattern** | 팀 협업 방식 정의 | `AG_Cohub/` | `patterns/*.json` |

---

## 📚 AI/개발자 필독 - 파일 읽기 순서

> **STOP!** 새 에이전트를 JSON으로 추가하기 전에 아래 순서대로 파일을 반드시 읽어주세요.
> 각 파일의 핵심 포인트를 이해하지 않으면 통합에서 문제가 발생합니다.

### Phase 1: A2A 에이전트 이해 (★ 새 에이전트 추가 시 필수!)

```
1. a2a_demo/README.md                    ← [필독!] 에이전트 추가 완전 가이드
   - "FOR AI ASSISTANTS" 섹션 반드시 읽기
   - 핵심 필드 테이블 (name, description) 이해
   - JSON 등록 예제 복사해서 사용

2. a2a_demo/calculator_agent/agent.py    ← 기본 A2A 에이전트 예제
   - Agent() 생성자 패턴 확인
   - name과 description 필드 형식 확인

3. a2a_demo/history_agent/agent.py       ← 복잡한 도구를 가진 에이전트
   - 여러 FunctionTool 사용 방법
   - 상세한 description 작성 방법
```

**핵심**: A2A agent.py의 `name`과 `description`이 AutoGen JSON에 **그대로** 복사되어야 함!

### Phase 2: AutoGen 통합 이해

```
4. autogen_source/.../autogenstudio/a2a/agent.py    ← A2AAgent 클래스
   - A2AAgentConfig 스키마 확인
   - name, description, a2a_server_url 필드

5. autogen_source/.../teammanager/teammanager.py    ← 팀 실행 로직
   - provider 타입에 따른 팀 생성
```

**핵심**: A2AAgent가 외부 A2A 서버를 AutoGen 팀 참가자로 래핑

### Phase 3: 패턴 시스템 이해 (★ 협업 방식 수정 시 필수!)

```
6. AG_Cohub/README.md                               ← [필독!] 패턴 시스템 완전 가이드
   - "FOR AI ASSISTANTS" 섹션 반드시 읽기
   - Pattern → AutoGen Provider 매핑 테이블
   - A2A 에이전트와 패턴 통합 섹션

7. AG_Cohub/patterns/07_debate.json                 ← 토론 패턴 JSON 예제
   - autogen_implementation.provider 확인
   - selector_prompt 형식 확인

8. frontend/.../team-runtime/team-factory.ts        ← [핵심!] 패턴 적용 로직
   - generateDynamicSelectorPrompt() 함수
   - applyPatternToExistingTeam() 함수
   - AgentInfo 인터페이스 (name + description)
```

**핵심**: team-factory.ts가 에이전트 name/description을 사용해 동적으로 selector_prompt 생성!

### Phase 4: 전체 데이터 플로우 이해

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         전체 데이터 플로우                                │
└─────────────────────────────────────────────────────────────────────────┘

[Step 1] A2A 에이전트 Python 정의
         a2a_demo/*/agent.py
         ┌────────────────────────────┐
         │ Agent(                     │
         │   name="history_agent",    │ ←─── 이 값이!
         │   description="역사 전문가", │ ←─── 그대로 복사됨!
         │   ...                      │
         │ )                          │
         └────────────────────────────┘
                     ↓
[Step 2] A2A 서버 실행 (port 8003-8010)
         python a2a_demo/history_agent/agent.py
                     ↓
[Step 3] AutoGen Studio JSON 등록
         ┌────────────────────────────────────┐
         │ {                                  │
         │   "provider": "...A2AAgent",       │
         │   "config": {                      │
         │     "name": "history_agent",       │ ←─── agent.py와 동일!
         │     "description": "역사 전문가",   │ ←─── agent.py와 동일!
         │     "a2a_server_url": "http://..." │
         │   }                                │
         │ }                                  │
         └────────────────────────────────────┘
                     ↓
[Step 4] 패턴 선택 (예: "debate")
         ┌────────────────────────────┐
         │ SelectorGroupChat 적용     │
         └────────────────────────────┘
                     ↓
[Step 5] team-factory.ts 동적 프롬프트 생성
         ┌─────────────────────────────────────────┐
         │ selector_prompt:                        │
         │ "You are coordinating a multi-agent..." │
         │                                         │
         │ Available Agents:                       │
         │ - history_agent: 역사 전문가             │ ←─── name + description 사용!
         │ - philosophy_agent: 철학 인용 전문가     │
         │                                         │
         │ Return ONLY the agent name."            │
         └─────────────────────────────────────────┘
                     ↓
[Step 6] Selector LLM이 에이전트 선택
         "역사 질문이니까... history_agent 선택!"
                     ↓
[Step 7] A2A 에이전트 응답
         history_agent → "역사적으로 보면..."
```

### name/description 불일치 시 발생하는 문제

| 상황 | 증상 | 해결 |
|------|------|------|
| agent.py `name` ≠ JSON `name` | Selector가 에이전트 찾지 못함 | 값 일치시키기 |
| description이 빈 문자열 | Selector가 에이전트 역할 모름 | 상세 설명 추가 |
| description이 너무 짧음 | Selector가 잘못된 에이전트 선택 | 역할 명확히 기술 |

### 핵심 파일 퀵 레퍼런스

| 파일 | 용도 | 언제 읽나? |
|------|------|-----------|
| `a2a_demo/README.md` | 에이전트 추가 방법 | 새 에이전트 만들 때 |
| `a2a_demo/*/agent.py` | A2A 에이전트 예제 | 구현 참고할 때 |
| `autogenstudio/a2a/agent.py` | A2AAgent 클래스 | AutoGen 통합 이해 |
| `AG_Cohub/patterns/*.json` | 패턴 정의 | 협업 방식 이해/수정 |
| `team-factory.ts` | 패턴 적용 로직 | 패턴 동작 디버깅 |

---

## ⚠️ 필수! A2A 에이전트 서버 먼저 실행

> **CRITICAL**: AutoGen Studio에서 A2A 에이전트를 사용하려면 **반드시** A2A 서버들을 먼저 실행해야 합니다!
>
> 에러 메시지 `A2A 호출 실패: All connection attempts failed`가 나오면 → A2A 서버가 실행되지 않은 것!

### A2A 서버 시작 (반드시 먼저!)

**PowerShell에서 각 터미널에서 실행:**

```powershell
# 터미널 1: History Agent (포트 8003)
cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\history_agent
python agent.py

# 터미널 2: Philosophy Agent (포트 8004)
cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\philosophy_agent
python agent.py

# 터미널 3: Poetry Agent (포트 8005)
cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\poetry_agent
python agent.py

# 터미널 4: Calculator Agent (포트 8006)
cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\calculator_agent
python agent.py
```

**또는 한 줄로 여러 창 열기 (PowerShell):**

```powershell
# 모든 A2A 서버 새 창에서 시작
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\history_agent; python agent.py'
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\philosophy_agent; python agent.py'
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\poetry_agent; python agent.py'
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\calculator_agent; python agent.py'
```

### 서버 실행 확인

```powershell
# 포트 확인 - 8003, 8004, 8005, 8006이 LISTENING이면 성공
netstat -an | findstr ":8003 :8004 :8005 :8006"
```

예상 출력:
```
TCP    127.0.0.1:8003         0.0.0.0:0              LISTENING
TCP    127.0.0.1:8004         0.0.0.0:0              LISTENING
TCP    127.0.0.1:8005         0.0.0.0:0              LISTENING
TCP    127.0.0.1:8006         0.0.0.0:0              LISTENING
```

### 이제 AutoGen Studio 실행

```powershell
cd D:\Data\22_AG\autogen_a2a_kit
python start_server.py
# 또는: autogenstudio ui --port 8081
```

브라우저에서 http://127.0.0.1:8081 접속

---

## 즉시 실행 (복붙용)

### ⚠️ 필수: .env 파일 확인

```bash
# 프로젝트 루트에 .env 파일 필요
# 없으면 .env.example 복사 후 API 키 설정
copy .env.example .env
# 그리고 .env 파일 열어서 OPENAI_API_KEY 설정
```

### AutoGen Studio 실행 (Windows PowerShell)

```powershell
# .env 로드 후 실행 (권장)
$env:OPENAI_API_KEY = (Get-Content .env | Select-String 'OPENAI_API_KEY' | ForEach-Object { $_.Line.Split('=')[1] })
python -c "from autogenstudio.web.app import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8081)"
```

### AutoGen Studio 실행 (Windows CMD)

```cmd
# .env 파일의 API 키를 환경변수로 설정 후 실행
for /f "tokens=2 delims==" %a in ('findstr OPENAI_API_KEY .env') do set OPENAI_API_KEY=%a
python -c "from autogenstudio.web.app import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8081)"
```

### 포트 확인 (이미 실행 중인지)

```bash
netstat -ano | findstr :8081
```

### 전체 서비스 실행 (A2A + Studio)

```powershell
# Windows PowerShell (자동으로 .env 로드)
.\run_all.ps1

# Windows CMD
run_all.bat
```

### 전체 서비스 종료

```powershell
.\stop_all.ps1
# 또는
stop_all.bat
```

### 흔한 에러 해결

| 에러 | 원인 | 해결 |
|------|------|------|
| `OPENAI_API_KEY environment variable` | API 키 미설정 | `.env` 파일 확인, 환경변수 설정 |
| `Address already in use :8081` | 이미 실행 중 | `netstat -ano \| findstr :8081`로 PID 확인 후 종료 |
| `Module not found` | 패키지 미설치 | `pip install -e autogen_source/python/packages/autogen-studio` |

---

## 📊 패턴(Pattern) 파라미터 상세 설명

> **이 섹션은 각 패턴의 핵심 파라미터를 설명합니다.**

### 패턴 요약 테이블

| ID | 패턴명 | Provider | 핵심 파라미터 | 용도 |
|----|--------|----------|--------------|------|
| 01 | Sequential | RoundRobinGroupChat | - | 순차적 대화 |
| 02 | Concurrent | RoundRobinGroupChat | - | 병렬 처리 후 취합 |
| 03 | Selector | SelectorGroupChat | `model_client`, `selector_prompt`, `allow_repeated_speaker` | LLM이 다음 발언자 선택 |
| 04 | Group Chat | RoundRobinGroupChat | - | 라운드로빈 대화 |
| 05 | Handoff (Swarm) | Swarm | `handoffs` | 에이전트 간 핸드오프 |
| 06 | Magentic | MagenticOneGroupChat | `model_client` | 오케스트레이터 패턴 |
| 07 | Debate | SelectorGroupChat | `allow_repeated_speaker: false` | 토론/반박 |
| 08 | Reflection | SelectorGroupChat | - | 작업자+검토자 |
| 09 | Hierarchical | SelectorGroupChat | - | 계층적 위임 |
| 10 | Mixture of Agents | SelectorGroupChat | `model_client` | 다중 에이전트 앙상블 |
| 11 | Code Execution | RoundRobinGroupChat | `termination_condition` | 코드 작성+실행 |

---

### 03. Selector Pattern 파라미터

```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "config": {
    "model_client": { ... },           // ★ 필수: Selector LLM
    "selector_prompt": "...",          // ★ 핵심: 선택 기준 프롬프트
    "allow_repeated_speaker": true,    // 같은 에이전트 연속 선택 허용
    "participants": [ ... ]
  }
}
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `model_client` | object | Selector LLM (에이전트 선택용) |
| `selector_prompt` | string | LLM에게 전달되는 선택 기준 프롬프트 |
| `allow_repeated_speaker` | boolean | `true`: 같은 에이전트 연속 허용, `false`: 강제 로테이션 |

---

### 05. Swarm (Handoff) Pattern 파라미터

```json
{
  "provider": "autogen_agentchat.teams.Swarm",
  "config": {
    "participants": [
      {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "config": {
          "name": "triage_agent",
          "handoffs": ["specialist_a", "specialist_b"]  // ★ 핸드오프 대상
        }
      }
    ]
  }
}
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `handoffs` | string[] | 이 에이전트가 작업을 넘길 수 있는 대상 에이전트 이름 목록 |

---

### 06. Magentic One Pattern 파라미터

```json
{
  "provider": "autogen_agentchat.teams.MagenticOneGroupChat",
  "config": {
    "model_client": { ... },  // ★ 필수: Orchestrator LLM
    "participants": [ ... ]
  }
}
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `model_client` | object | Orchestrator LLM (작업 분배/통합) |

---

### 07. Debate Pattern 파라미터 (★ 중요!)

**핵심**: `allow_repeated_speaker: false`로 설정해야 에이전트 로테이션 강제!

> **🐛 Bug Fix (2025-01-10)**: `requiredConfig`가 top-level과 `autogen_implementation` 양쪽에서 읽히도록 수정됨.
> 이제 JSON 패턴 파일의 top-level `requiredConfig.allow_repeated_speaker: false`가 정상 적용됩니다.

```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "requiredConfig": {
    "allow_repeated_speaker": false,  // ★ top-level에서 설정 (권장)
    "max_turns": 10
  },
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "team_config": { ... }
  }
}
```

**수정된 파일:**
- `pattern-loader.ts`: top-level + autogen_implementation 양쪽에서 requiredConfig 읽기
- `selector-config.ts`: allow_repeated_speaker 기본값을 false로 설정
- `team-factory.ts`: selector_prompt 적용 로직 개선

| 설정 | 동작 |
|------|------|
| `allow_repeated_speaker: true` | 같은 에이전트 계속 선택 가능 → 한 명만 응답하는 문제 발생! |
| `allow_repeated_speaker: false` (기본값) | 반드시 다른 에이전트 선택 → 토론 로테이션 ✅ |

---

### 공통 파라미터

모든 패턴에 적용되는 공통 파라미터:

```json
{
  "config": {
    "participants": [ ... ],          // 참가 에이전트 목록
    "termination_condition": {        // 종료 조건
      "provider": "autogen_agentchat.conditions.TextMentionTermination",
      "config": { "text": "TERMINATE" }
    }
  }
}
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `participants` | array | 팀에 참여하는 에이전트 목록 |
| `termination_condition` | object | 대화 종료 조건 |

### 종료 조건 종류

| Provider | 설명 |
|----------|------|
| `TextMentionTermination` | 특정 텍스트("TERMINATE") 언급 시 종료 |
| `MaxMessageTermination` | 최대 메시지 수 도달 시 종료 |
| `OrTermination` | 여러 조건 중 하나라도 만족 시 종료 |

---

## A2A vs Pattern 비교

```
A2A (Agent-to-Agent):
├─ 무엇? 외부 에이전트 서버를 AutoGen에 연결
├─ 어디? a2a_demo/ 폴더
├─ 어떻게? Google A2A 프로토콜 (JSON-RPC)
└─ 예시: calculator_agent → http://localhost:8006

Pattern (협업 패턴):
├─ 무엇? 에이전트들이 협업하는 "방식"
├─ 어디? AG_Cohub/patterns/ 폴더
├─ 어떻게? JSON 정의 → TeamConfig 변환
└─ 예시: Debate → advocate↔critic 번갈아 발언
```

### 둘의 관계

```
Pattern은 "어떻게 협업할지" (Selector, Sequential, Swarm)
A2A는 "누구와 협업할지" (외부 에이전트 연결)

예: SelectorGroupChat(Pattern) + calculator_agent(A2A)
    = LLM이 계산 필요시 외부 계산기 에이전트 선택
```

---

## 프로젝트 구조 (핵심만)

```
autogen_a2a_kit/
├── AG_Cohub/                  ★ 패턴 시스템 (협업 방식)
│   ├── patterns/              패턴 JSON 정의
│   ├── templates/             TeamConfig 템플릿
│   └── loader/                JSON→TypeScript 변환
│
├── a2a_demo/                  ★ A2A 에이전트 서버들
│   ├── calculator_agent/      수학 계산 (port 8006)
│   ├── poetry_agent/          시 분석 (port 8003)
│   └── ...
│
├── autogen_source/            ★ AutoGen 소스 (editable)
│   └── python/packages/
│       └── autogen-studio/
│           ├── autogenstudio/
│           │   ├── a2a/       A2AAgent 클래스
│           │   └── web/       Studio 백엔드
│           └── frontend/      Studio UI (React)
│
├── run_all.ps1               전체 실행 스크립트
├── stop_all.ps1              전체 종료 스크립트
└── README.md                 이 파일
```

---

## 🚀 Quick Start (AI/CLI 실행용)

> **AI Agent나 CLI에서 순서대로 실행하세요. setup.bat 없이 수동 설치합니다.**

### Prerequisites
- Python 3.10+
- OpenAI API Key

### Step 1: Clone Repository
```bash
git clone https://github.com/akfldk1028/AG.git
cd AG/autogen_a2a_kit
```

### Step 2: Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade pip
```bash
pip install --upgrade pip
```

### Step 4: Install AutoGen packages (editable mode)
```bash
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"
pip install -e autogen_source/python/packages/autogen-studio
```

### Step 5: Install A2A dependencies
```bash
pip install google-adk httpx python-dotenv
```

### Step 6: Set API Key

**Windows:**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

### Step 7: Verify Installation
```bash
python -c "from autogen_agentchat.agents import AssistantAgent; print('OK: autogen-agentchat')"
python -c "from autogenstudio.a2a import A2AAgent; print('OK: A2AAgent')"
```

### Step 8: Run A2A Demo Server (Terminal 1)
```bash
python a2a_demo/remote_agent/agent.py
```

### Step 9: Run AutoGen Studio (Terminal 2)
```bash
autogenstudio ui --port 8081
```

### Step 10: Open Browser
```
http://localhost:8081
```

---

## 주요 기능

- AutoGen 소스를 editable mode로 설치하여 수정 즉시 반영
- A2A 프로토콜 서버 예제 포함 (소수 판별, 계산기)
- AutoGen Studio UI에서 A2A 에이전트 사용 가능
- 원클릭 설치 스크립트

## 요구사항

- Python 3.10 이상
- OpenAI API Key

## 설치

> **권장: 위의 [Quick Start](#-quick-start-aicli-실행용) 섹션을 따라하세요.**

### 자동 설치 (setup 스크립트)

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

setup 스크립트는 다음을 수행합니다:
1. Python 가상환경 생성 (venv/)
2. autogen-core, autogen-agentchat, autogen-ext, autogen-studio를 editable mode로 설치
3. A2A 관련 의존성 설치

> **Note**: `autogen_source/` 폴더는 이미 A2A 수정본이 포함되어 있습니다. Microsoft repo에서 별도로 클론하지 않습니다.

## 환경 변수 설정

### .env 파일 사용 (권장)

`.env` 파일을 생성하고 API 키를 설정하세요:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

### 환경 변수 직접 설정

```cmd
# Windows
set OPENAI_API_KEY=sk-your-api-key-here
set GEMINI_API_KEY=your-gemini-api-key-here

# Linux / Mac
export OPENAI_API_KEY=sk-your-api-key-here
export GEMINI_API_KEY=your-gemini-api-key-here
```

> **Note:** A2A 에이전트들은 Google ADK를 사용하며 GEMINI_API_KEY가 필요합니다.

## A2A 에이전트 상세 설명

### Poetry Agent (포트 8003)
- **역할**: 시 분석 및 해석
- **기술**: Google ADK + Gemini
- **기능**:
  - 시의 주제, 구조, 감정 분석
  - 시적 표현 해석
  - 문학적 기법 설명

### Philosophy Agent (포트 8004)
- **역할**: 철학적 지혜 제공
- **기술**: Google ADK + Gemini
- **기능**:
  - 철학적 질문 답변
  - 철학자 인용 및 설명
  - 윤리적 딜레마 분석

### History Agent (포트 8005)
- **역할**: 역사 스토리텔링
- **기술**: Google ADK + Gemini
- **기능**:
  - 역사적 사건 설명
  - 시대별 맥락 제공
  - 역사적 인물 소개

### Calculator Agent (포트 8006)
- **역할**: 수학 계산
- **기술**: Google ADK + Gemini
- **기능**:
  - 기본 사칙연산
  - 피보나치, 팩토리얼 계산
  - 수식 평가

---

## 🔧 CLI Agent (Claude Code 기반)

> **NEW!** Claude Code CLI를 활용한 코드 작성/수정 전문 에이전트

### CLI Agent 개요

CLI 에이전트는 Claude Code의 6가지 도구를 A2A 프로토콜로 래핑하여 AutoGen Studio에서 사용할 수 있게 합니다.

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Agent                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  A2A Protocol  ──▶  Google ADK  ──▶  Claude Code CLI   │
│  (port 8110)        (FunctionTool)   (6 tools)          │
│                                                         │
│  지원 도구:                                              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│  │Read │ │Write│ │Edit │ │Glob │ │Grep │ │Bash │       │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### CLI Agent 포트

| Agent | Port | 작업 폴더 | 역할 |
|-------|------|----------|------|
| cli_db_agent | 8110 | db/ | PostgreSQL 스키마, 마이그레이션, DB 관련 코드 |
| cli_backend_agent | 8111 | backend/ | FastAPI, API 엔드포인트, 서버 코드 |

### 지원하는 도구

| 도구 | 기능 | 로그 형식 |
|------|------|----------|
| **Read** | 파일 읽기 | `[TOOL] [READ] Reading: {path}` |
| **Write** | 파일 생성 | `[TOOL] [WRITE] Creating: {path}` |
| **Edit** | 파일 수정 | `[TOOL] [EDIT] Modifying: {path}` |
| **Glob** | 파일 검색 (패턴) | `[TOOL] [GLOB] Pattern: {pattern}` |
| **Grep** | 내용 검색 | `[TOOL] [GREP] Search: {term}` |
| **Bash** | 명령어 실행 | `[TOOL] [BASH] {command}` |

### CLI Agent 실행

```powershell
# 개별 실행
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli\studio
python cli_agent.py --port 8110 --folder db      # DB 에이전트
python cli_agent.py --port 8111 --folder backend # Backend 에이전트
```

### CLI Agent 로그 확인

```powershell
# 실시간 로그 확인
curl http://127.0.0.1:8110/logs

# 특정 작업 로그
curl http://127.0.0.1:8110/logs/{task_id}
```

### 로그 출력 예시

```
[14:44:39.918] [START] === Claude CLI Task Started ===
[14:44:39.918] [INFO] Task: db/hello.py 파일 생성
[14:44:45.411] [TOOL] [WRITE] Creating: D:\...\db\hello.py
[14:44:45.412] [CODE] [CONTENT]
print('Hello World!')
[14:44:46.271] [RESULT] [CREATED] D:\...\db\hello.py
[14:44:48.863] [OUT] [ASSISTANT] hello.py 파일을 생성했습니다.
[14:44:50.640] [INFO] [DONE] Status: success, Duration: 10970ms
[14:44:52.929] [END] === Task Completed Successfully ===
```

### AutoGen Studio에서 CLI Agent 사용

1. Team Builder에서 cli_db_agent 또는 cli_backend_agent 추가
2. Selector 패턴으로 작업 유형에 따라 자동 라우팅
3. 작업 완료 시 TASK_COMPLETE 반환

## 디렉토리 구조

```
autogen_a2a_kit/
├── a2a_demo/                      # A2A 서버 예제
│   ├── remote_agent/
│   │   └── agent.py               # 소수 판별 에이전트 (port 8002)
│   ├── poetry_agent/
│   │   └── agent.py               # 시 분석 에이전트 (port 8003)
│   ├── philosophy_agent/
│   │   └── agent.py               # 철학 지혜 에이전트 (port 8004)
│   ├── history_agent/
│   │   └── agent.py               # 역사 스토리텔러 에이전트 (port 8005)
│   ├── calculator_agent/
│   │   └── agent.py               # 계산기 에이전트 (port 8006)
│   └── root_agent/
│       └── agent.py               # 코디네이터 에이전트
├── autogen_source/                # AutoGen 소스 (editable mode)
│   └── python/packages/
│       ├── autogen-core/          # 코어 라이브러리
│       ├── autogen-agentchat/     # 에이전트 채팅
│       ├── autogen-ext/           # 확장 (OpenAI 등)
│       └── autogen-studio/        # Studio UI + A2A 통합
│           └── autogenstudio/
│               └── a2a/           # A2AAgent 클래스
├── run_all.ps1                    # PowerShell 전체 실행 스크립트
├── run_all.bat                    # CMD 전체 실행 스크립트
├── stop_all.ps1                   # PowerShell 전체 종료 스크립트
├── stop_all.bat                   # CMD 전체 종료 스크립트
├── setup.bat                      # Windows 설치 스크립트
├── setup.sh                       # Linux/Mac 설치 스크립트
├── requirements.txt               # Python 의존성
├── .env                           # 환경 변수 (API 키)
├── AI_HANDOFF.md                  # AI 전달 문서
└── README.md                      # 이 문서
```

## 실행 방법

### 1. A2A 서버 실행

**권장: 한 번에 모든 서비스 실행**
```powershell
.\run_all.ps1   # PowerShell
# 또는
run_all.bat     # CMD
```

**개별 실행 (각각 별도 터미널에서):**

```cmd
# Windows - 가상환경 활성화
cd autogen_a2a_kit
venv\Scripts\activate

# 각 에이전트 실행
python a2a_demo/poetry_agent/agent.py       # 포트 8003
python a2a_demo/philosophy_agent/agent.py   # 포트 8004
python a2a_demo/history_agent/agent.py      # 포트 8005
python a2a_demo/calculator_agent/agent.py   # 포트 8006
```

```bash
# Linux/Mac - 가상환경 활성화
cd autogen_a2a_kit
source venv/bin/activate

# 각 에이전트 실행
python a2a_demo/poetry_agent/agent.py       # 포트 8003
python a2a_demo/philosophy_agent/agent.py   # 포트 8004
python a2a_demo/history_agent/agent.py      # 포트 8005
python a2a_demo/calculator_agent/agent.py   # 포트 8006
```

### 2. AutoGen Studio 실행

```cmd
# Windows
cd autogen_a2a_kit
venv\Scripts\activate
autogenstudio ui --port 8081
```

```bash
# Linux/Mac
cd autogen_a2a_kit
source venv/bin/activate
autogenstudio ui --port 8081
```

브라우저에서 http://localhost:8081 접속

### 3. A2A 서버 직접 테스트

```cmd
# 소수 판별 테스트
curl -X POST http://localhost:8002 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"message/send\",\"id\":\"1\",\"params\":{\"message\":{\"messageId\":\"1\",\"role\":\"user\",\"parts\":[{\"kind\":\"text\",\"text\":\"Is 17 a prime number?\"}]}}}"
```

```cmd
# 계산기 테스트
curl -X POST http://localhost:8006 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"message/send\",\"id\":\"1\",\"params\":{\"message\":{\"messageId\":\"1\",\"role\":\"user\",\"parts\":[{\"kind\":\"text\",\"text\":\"Calculate fibonacci(10)\"}]}}}"
```

## 포트 구성

| Port | Service | 설명 |
|------|---------|------|
| 8081 | AutoGen Studio | 웹 UI (에이전트 관리/실행) |
| 8002 | prime_checker_agent | A2A 소수 판별 서버 |
| 8003 | poetry_agent | A2A 시 분석 에이전트 |
| 8004 | philosophy_agent | A2A 철학 지혜 에이전트 |
| 8005 | history_agent | A2A 역사 스토리텔러 에이전트 |
| 8006 | calculator_agent | A2A 계산기 에이전트 |
| 8007 | math_agent | A2A 수학 전문가 에이전트 |
| 8008 | graphics_agent | A2A 컴퓨터 그래픽스 에이전트 |
| 8009 | gpu_agent | A2A GPU/병렬컴퓨팅 에이전트 |
| 8110 | cli_db_agent | CLI 에이전트 (db/ 폴더) - Claude Code 기반 |
| 8111 | cli_backend_agent | CLI 에이전트 (backend/ 폴더) - Claude Code 기반 |

## 한 번에 모든 서비스 실행

### Windows PowerShell
```powershell
.\run_all.ps1
```

### Windows CMD
```cmd
run_all.bat
```

### 모든 서비스 종료
```powershell
.\stop_all.ps1
# 또는
stop_all.bat
```

## AutoGen Studio에서 A2A 에이전트 사용

### A2AAgent 설정 형식

AutoGen Studio 팀 구성에서 A2A 에이전트를 추가할 때 사용하는 JSON 형식:

```json
{
    "provider": "autogenstudio.a2a.A2AAgent",
    "component_type": "agent",
    "version": 1,
    "label": "Calculator Agent",
    "config": {
        "name": "calculator_agent",
        "a2a_server_url": "http://localhost:8006",
        "description": "Math calculator specialist",
        "timeout": 60,
        "skills": []
    }
}
```

### SelectorGroupChat 팀 구성 예시

여러 A2A 에이전트를 포함한 팀:

```json
{
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team",
    "label": "Dual A2A Team",
    "config": {
        "participants": [
            {
                "provider": "autogen_agentchat.agents.AssistantAgent",
                "config": {
                    "name": "assistant_agent",
                    "model_client": {
                        "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                        "config": {"model": "gpt-4o-mini"}
                    },
                    "system_message": "General assistant. Delegate prime questions to prime_checker_agent, math to calculator_agent. Say TERMINATE when done."
                }
            },
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "prime_checker_agent",
                    "a2a_server_url": "http://localhost:8002",
                    "description": "Prime number specialist"
                }
            },
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "calculator_agent",
                    "a2a_server_url": "http://localhost:8006",
                    "description": "Math calculator specialist"
                }
            }
        ],
        "model_client": {
            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
            "config": {"model": "gpt-4o-mini"}
        },
        "selector_prompt": "Select agent:\n- prime_checker_agent: prime numbers, factorization\n- calculator_agent: calculations, fibonacci, factorial\n- assistant_agent: general\n\nConversation: {history}\nRoles: {roles}\nReturn ONLY agent name.",
        "termination_condition": {
            "provider": "autogen_agentchat.conditions.MaxMessageTermination",
            "config": {"max_messages": 10}
        }
    }
}
```

### API로 팀 생성하기

```python
import requests
import json

team_config = {
    "user_id": "guestuser@gmail.com",
    "team": {
        "provider": "autogen_agentchat.teams.SelectorGroupChat",
        "component_type": "team",
        "version": 1,
        "label": "Dual A2A Team",
        "config": {
            "participants": [
                {
                    "provider": "autogen_agentchat.agents.AssistantAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "assistant_agent",
                        "model_client": {
                            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                            "component_type": "model",
                            "version": 1,
                            "config": {"model": "gpt-4o-mini"}
                        },
                        "system_message": "General assistant. Say TERMINATE when done."
                    }
                },
                {
                    "provider": "autogenstudio.a2a.A2AAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "prime_checker_agent",
                        "a2a_server_url": "http://localhost:8002",
                        "description": "Prime number specialist",
                        "timeout": 60,
                        "skills": []
                    }
                },
                {
                    "provider": "autogenstudio.a2a.A2AAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "calculator_agent",
                        "a2a_server_url": "http://localhost:8006",
                        "description": "Math calculator specialist",
                        "timeout": 60,
                        "skills": []
                    }
                }
            ],
            "model_client": {
                "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                "component_type": "model",
                "version": 1,
                "config": {"model": "gpt-4o-mini"}
            },
            "termination_condition": {
                "provider": "autogen_agentchat.conditions.MaxMessageTermination",
                "component_type": "termination",
                "version": 1,
                "config": {"max_messages": 10}
            },
            "selector_prompt": "Select agent based on query type. Return ONLY agent name."
        }
    }
}

response = requests.post(
    "http://127.0.0.1:8081/api/teams/",
    json=team_config
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

## A2A 프로토콜 상세

### 요청 형식

```json
{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "unique-request-id",
    "params": {
        "message": {
            "messageId": "unique-message-id",
            "role": "user",
            "parts": [{"kind": "text", "text": "질문 내용"}]
        }
    }
}
```

### 응답 형식

```json
{
    "jsonrpc": "2.0",
    "id": "unique-request-id",
    "result": {
        "artifacts": [{
            "parts": [{"kind": "text", "text": "응답 내용"}]
        }]
    }
}
```

### Agent Card 확인

```bash
curl http://localhost:8002/.well-known/agent.json
```

응답:

```json
{
    "name": "prime_checker_agent",
    "description": "소수를 판별하고 소인수분해를 수행하는 에이전트",
    "skills": [
        {"name": "is_prime", "description": "숫자가 소수인지 확인"},
        {"name": "get_prime_factors", "description": "소인수분해 수행"}
    ]
}
```

## AutoGen 소스 수정

editable mode로 설치되어 있어 소스 수정 시 즉시 반영됩니다.

```
autogen_source/python/packages/
├── autogen-core/src/autogen_core/          # 코어 기능
├── autogen-agentchat/src/autogen_agentchat/  # 에이전트 채팅
├── autogen-ext/src/autogen_ext/            # 확장 모듈
└── autogen-studio/autogenstudio/           # Studio UI
    └── a2a/                                # A2A 통합
        ├── __init__.py
        ├── agent.py                        # A2AAgent 클래스
        └── registry.py                     # A2ARegistry
```

수정 후 재설치 불필요. 파일 저장만 하면 됩니다.

## 새로운 A2A 에이전트 추가하기 (★ AI/개발자 필독!)

> **이 섹션을 따라하면 5분 안에 새 에이전트를 추가할 수 있습니다.**
>
> **✅ Gallery 자동 등록!** `builder.py`가 `a2a_demo/` 폴더를 자동 스캔합니다.
> agent.py 파일만 추가하면 Gallery에 자동으로 등록됩니다!

### 체크리스트 (2단계로 끝!)

```
[ ] 1. a2a_demo/{agent_name}/ 폴더 생성 + agent.py 작성
[ ] 2. 서버 실행 및 테스트
```

> **참고**: Gallery 자동 등록은 `autogenstudio/gallery/builder.py`의
> `create_cohub_gallery()` 함수가 `a2a_demo/*/agent.py`를 스캔하여
> name, description, port를 정규식으로 추출합니다.

### Step 1: 포트 번호 결정

현재 사용 중인 포트:
- 8003-8009: 기존 에이전트
- **다음 가용 포트: 8010**

### Step 2: 에이전트 템플릿 복사

`a2a_demo/{your_agent_name}/agent.py` 생성:

```python
# {Agent Name} Agent - A2A Protocol
# {에이전트 설명}

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm  # ★ 필수!

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found")


# ★ 도구 함수 정의 (docstring 필수!)
def your_tool_function(param1: str, param2: int = 10) -> dict:
    """도구 함수 설명 (한 줄).

    Args:
        param1: 첫 번째 매개변수 설명
        param2: 두 번째 매개변수 설명 (기본값: 10)

    Returns:
        결과 딕셔너리
    """
    # 로직 구현
    return {"result": f"처리됨: {param1}", "value": param2}


# ★ 에이전트 정의
your_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),  # ★ LiteLlm 래퍼 필수!
    name="your_agent_name",  # ★ 이 이름이 AutoGen에서 사용됨
    description="에이전트가 하는 일을 명확하게 기술. Selector LLM이 이걸 보고 선택함!",
    instruction="""당신은 {역할} 전문가 에이전트입니다.

주요 기능:
1. 기능 1 설명
2. 기능 2 설명

토론 시 역할:
- 어떤 관점에서 분석하는지
- 어떤 전문성을 제공하는지

한국어로 응답해주세요.""",
    tools=[
        FunctionTool(your_tool_function),
        # FunctionTool(another_function),
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    PORT = 8010  # ★ 사용할 포트 번호

    print("=" * 50)
    print(f"Your Agent Name - A2A Server")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Agent Card: http://localhost:{PORT}/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(your_agent, port=PORT, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=PORT)
```

### Step 3: CLAUDE.md 업데이트

`.claude/CLAUDE.md` 파일의 에이전트 테이블에 추가:

```markdown
| your_agent | 8010 | a2a_demo/your_agent/agent.py | 전문 분야 |
```

### Step 4: run_all.ps1 업데이트

`run_all.ps1`의 `$agents` 배열에 추가:

```powershell
$agents = @(
    # ... 기존 에이전트들 ...
    @{Name="your_agent"; Port=8010}
)
```

### Step 5: 서버 실행 및 테스트

```powershell
# 서버 시작
cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\your_agent
python agent.py

# 다른 터미널에서 테스트
curl http://localhost:8010/.well-known/agent-card.json
```

### ★ 핵심 규칙

| 규칙 | 설명 |
|------|------|
| `LiteLlm(model="openai/gpt-4o-mini")` | OpenAI 모델은 반드시 LiteLlm 래퍼 사용 |
| `name` 일관성 | agent.py의 name = AutoGen JSON의 name |
| `description` 중요 | Selector LLM이 이걸 보고 에이전트 선택 |
| docstring 필수 | 도구 함수에 docstring 없으면 작동 안 함 |

### 기존 에이전트 참고

| 에이전트 | 참고 포인트 |
|----------|-------------|
| `calculator_agent` | 기본 도구 함수 구조 |
| `math_agent` | 수학 함수 (이차방정식, 피보나치) |
| `graphics_agent` | 복잡한 도구 (색공간 변환, 렌더링 파이프라인) |
| `gpu_agent` | 기술 도메인 전문 에이전트 |

## 프론트엔드 개발 (UI 수정 시)

> **중요**: 프론트엔드는 **Gatsby**로 빌드됩니다. Windows에서는 기본 `npm run build`가 작동하지 않으므로 아래 Windows 전용 명령어를 사용하세요.

### 1. 프론트엔드 소스 위치

```
autogen_source/python/packages/autogen-studio/frontend/
├── src/
│   ├── components/   # React 컴포넌트
│   ├── pages/        # 페이지 라우트
│   └── ...
├── package.json
└── gatsby-config.ts  # Gatsby 설정
```

### 2. 의존성 설치 (최초 1회)

```bash
cd autogen_source/python/packages/autogen-studio/frontend
npm install --legacy-peer-deps
```

### 3. 개발 모드 실행 (실시간 미리보기)

```bash
npm run develop
```

브라우저에서 `http://localhost:8000` 접속 (Gatsby 개발 서버)

### 4. 프로덕션 빌드 (★ Windows 전용 명령어)

> **WARNING**: `npm run build`는 Linux 명령어(`rm -rf`, `rsync`)를 사용하므로 Windows에서 실패합니다!

**Windows PowerShell (권장):**
```powershell
cd autogen_source/python/packages/autogen-studio/frontend

# Step 1: Gatsby 캐시 정리
npx gatsby clean

# Step 2: Gatsby 빌드
npx gatsby build --prefix-paths

# Step 3: 빌드 결과를 web/ui로 복사
Remove-Item -Recurse -Force ..\autogenstudio\web\ui\* -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force public\* ..\autogenstudio\web\ui\
```

**Windows 한 줄 명령어 (복붙용):**
```powershell
cd "D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio\frontend"; npx gatsby clean; npx gatsby build --prefix-paths; Remove-Item -Recurse -Force ..\autogenstudio\web\ui\* -ErrorAction SilentlyContinue; Copy-Item -Recurse -Force public\* ..\autogenstudio\web\ui\
```

**Linux/Mac:**
```bash
npm run build
# 위 명령어가 자동으로 public/ → web/ui/ 복사
```

### 5. 빌드 후 서버 재시작

```bash
# 기존 서버 종료 후
autogenstudio ui --port 8081

# 또는 start_server.py 사용
python start_server.py
```

### 6. 빌드 결과 Git 커밋

UI 빌드 파일은 **반드시 커밋**해야 합니다 (Windows에서 빌드 불가한 환경 대응):

```bash
git add autogen_source/python/packages/autogen-studio/autogenstudio/web/ui/
git commit -m "build: Update frontend UI"
git push
```

### 흔한 빌드 에러

| 에러 | 원인 | 해결 |
|------|------|------|
| `rm: command not found` | Linux 명령어 | Windows용 명령어 사용 (위 참조) |
| `rsync: command not found` | Linux 명령어 | `Copy-Item` 사용 |
| `PREFIX_PATH_VALUE is not recognized` | 환경변수 문법 | PowerShell용 명령어 사용 |
| `gatsby: command not found` | PATH 문제 | `npx gatsby` 사용 |

> **Note:** `autogenstudio/web/ui/` 폴더는 이미 빌드된 파일이 포함되어 있습니다. 프론트엔드를 수정하지 않는 사용자는 빌드 없이 바로 사용 가능합니다.

---

## 문제 해결

### Windows 한글 깨짐

```cmd
chcp 65001
```

### A2A 서버 연결 실패

1. 서버가 실행 중인지 확인:
```cmd
curl http://localhost:8002/.well-known/agent.json
```

2. 포트가 사용 중인지 확인:
```cmd
netstat -ano | findstr :8002
```

3. 프로세스 종료 (필요시):
```cmd
taskkill /PID <프로세스ID> /F
```

### API 키 오류

환경 변수가 설정되어 있는지 확인:

```cmd
# Windows
echo %OPENAI_API_KEY%

# Linux/Mac
echo $OPENAI_API_KEY
```

### AutoGen Studio 팀 업데이트 불가 (PUT 405 오류)

AutoGen Studio의 PUT API가 405를 반환하는 경우 SQLite 직접 수정:

```python
import sqlite3
import os
import json

db_path = os.path.expanduser("~/.autogenstudio/autogen04202.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 팀 조회
cursor.execute("SELECT id, component FROM teams WHERE id = ?", (team_id,))
row = cursor.fetchone()
if row:
    component = json.loads(row[1])
    # component 수정
    component["config"]["participants"].append(new_agent)
    # 저장
    cursor.execute("UPDATE teams SET component = ? WHERE id = ?",
                   (json.dumps(component), team_id))
    conn.commit()

conn.close()
```

### venv 활성화 오류

```cmd
# Windows PowerShell 실행 정책 문제
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 이후 다시 시도
venv\Scripts\activate
```

## 기술 스택

| Component | Technology | Version |
|-----------|------------|---------|
| Multi-Agent Framework | Microsoft AutoGen | 0.7.x |
| A2A Server | Google ADK | 0.2.0+ |
| LLM | OpenAI GPT-4o-mini | - |
| Language | Python | 3.10+ |
| Web UI | AutoGen Studio | 0.4.x |

## 전체 실행 순서 요약

> **상세한 단계별 설치는 맨 위 [Quick Start](#-quick-start-aicli-실행용) 참조**

```bash
# 1. 저장소 클론
git clone https://github.com/akfldk1028/AG.git
cd AG/autogen_a2a_kit

# 2. 가상환경 + 설치
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install --upgrade pip
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"
pip install -e autogen_source/python/packages/autogen-studio
pip install google-adk httpx python-dotenv

# 3. 환경 변수
set OPENAI_API_KEY=sk-your-key  # Windows
# export OPENAI_API_KEY=sk-your-key  # Linux/Mac

# 4. 설치 확인
python -c "from autogenstudio.a2a import A2AAgent; print('OK')"

# 5. A2A 서버 실행 (터미널 1)
python a2a_demo/remote_agent/agent.py

# 6. AutoGen Studio 실행 (터미널 2)
autogenstudio ui --port 8081

# 7. 브라우저 접속
http://localhost:8081
```

## Changelog

### 2025-01-11
- ✨ **CLI Agent**: Claude Code 기반 CLI 에이전트 추가
  - 6개 도구 지원: Read, Write, Edit, Glob, Grep, Bash
  - 모듈화 구조: config.py, tools/, utils/
  - Stream-JSON 파싱으로 실시간 로그 캡처
  - AutoGen Studio 패턴과 완벽 통합
  - 포트: 8110 (db), 8111 (backend)

### 2025-01-10
- 🐛 **Bug Fix**: `allow_repeated_speaker` 버그 수정
  - `pattern-loader.ts`: top-level과 autogen_implementation 양쪽에서 requiredConfig 읽기
  - `selector-config.ts`: 기본값을 false로 설정 (AutoGen 기본 동작과 일치)
  - `team-factory.ts`: selector_prompt 적용 로직 개선
- ✨ **New Patterns**: 10_mixture_of_agents.json, 11_code_execution.json 추가
- ✅ **Tested Patterns**:
  - Multi-Agent Debate: 4개 A2A 에이전트 토론 성공
  - Reflection Pattern: 44,405 tokens | 20 messages
  - Selector/Router Orchestration: 27,491 tokens | 15 messages

## 라이선스

MIT License

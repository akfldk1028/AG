# A2A Demo Agents

A2A (Agent-to-Agent) 프로토콜 기반 데모 에이전트 컬렉션.
이 에이전트들은 AutoGen Studio 팀에 직접 참여할 수 있습니다.

---

## FOR AI ASSISTANTS - 필수 이해사항

> **📖 전체 문서 색인**: [`../DOCS_INDEX.md`](../DOCS_INDEX.md) - 모든 문서 목록 및 읽기 순서
>
> **이 섹션을 먼저 읽고 전체 구조를 파악하세요.**

### 핵심 개념 한눈에 보기

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2A → AutoGen 통합 플로우                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. A2A Agent 정의 (Python)                                     │
│     ├─ name: "history_agent"         ← selector가 이 이름 사용   │
│     ├─ description: "역사 전문가..."   ← selector가 이 설명 참조  │
│     ├─ instruction: "시스템 프롬프트"                             │
│     └─ tools: [FunctionTool(...)]                               │
│                           │                                     │
│                           ▼                                     │
│  2. A2A 서버로 노출 (port 8005)                                  │
│     to_a2a(agent, port=8005)                                    │
│                           │                                     │
│                           ▼                                     │
│  3. AutoGen Studio에 JSON 등록                                   │
│     {                                                           │
│       "provider": "autogenstudio.a2a.A2AAgent",                 │
│       "config": {                                               │
│         "name": "history_agent",        ← 반드시 일치!           │
│         "description": "역사 전문가...", ← 반드시 일치!           │
│         "a2a_server_url": "http://localhost:8005"               │
│       }                                                         │
│     }                                                           │
│                           │                                     │
│                           ▼                                     │
│  4. 팀에 추가 → 패턴 적용                                         │
│     team-factory.ts가 동적 selector_prompt 생성                  │
│     "Available Agents:                                          │
│      - history_agent: 역사 전문가..."                            │
│                           │                                     │
│                           ▼                                     │
│  5. Selector LLM이 에이전트 선택                                  │
│     "다음 발언자: history_agent" → A2A 호출                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 핵심 필드 (반드시 이해!)

| 필드 | 위치 | 역할 | 중요도 |
|------|------|------|--------|
| `name` | Agent() + A2AAgent | Selector가 에이전트 선택할 때 사용 | **필수** |
| `description` | Agent() + A2AAgent | Selector가 "누가 이 질문에 답할 수 있나?" 판단 | **필수** |
| `instruction` | Agent() | 에이전트의 행동 방식 정의 | 권장 |
| `tools` | Agent() | 에이전트가 사용 가능한 도구들 | 선택 |

> **중요**: `name`과 `description`은 A2A Agent 파일과 AutoGen 등록 JSON에서 **반드시 일치**해야 합니다!

---

## AI/개발자를 위한 읽기 순서

새 에이전트를 추가하거나 시스템을 이해하려면 다음 순서로 읽어주세요:

```
Phase 1: A2A 에이전트 구조 이해
1. 이 README.md (전체 구조)
2. calculator_agent/agent.py (기본 예제 - 단순한 도구)
3. history_agent/agent.py (복잡한 예제 - 여러 도구)

Phase 2: AutoGen 통합 이해
4. ../autogen_source/.../autogenstudio/a2a/agent.py (A2AAgent 클래스)
   → A2A 서버를 AutoGen BaseChatAgent로 래핑

Phase 3: 패턴 시스템 이해
5. ../autogen_source/.../team-runtime/team-factory.ts
   → generateDynamicSelectorPrompt() 함수가 핵심
   → 에이전트 name + description으로 selector_prompt 생성
```

---

## 디렉토리 구조

```
a2a_demo/
├── README.md              # 이 파일
├── calculator_agent/      # 수학 계산 에이전트 (포트 8006)
│   └── agent.py
├── history_agent/         # 역사 이야기 에이전트 (포트 8005)
│   └── agent.py
├── philosophy_agent/      # 철학 인용 에이전트 (포트 8004)
│   └── agent.py
├── poetry_agent/          # 시 분석 에이전트 (포트 8003)
│   └── agent.py
├── math_agent/            # 수학 전문 에이전트 (포트 8007)
│   └── agent.py
├── graphics_agent/        # 컴퓨터 그래픽스 에이전트 (포트 8008)
│   └── agent.py
├── gpu_agent/             # GPU/병렬컴퓨팅 에이전트 (포트 8009)
│   └── agent.py
├── root_agent/            # 루트/오케스트레이터 에이전트
│   └── agent.py
├── remote_agent/          # 원격 에이전트 예제 (포트 8002)
│   └── agent.py
└── start_server.bat       # 일괄 실행 스크립트
```

### 🔧 CLI 에이전트 (Claude Code 기반)

> **별도 폴더**: `AG-cli/studio/`에 위치

| 에이전트 | 포트 | 작업 폴더 | 도구 |
|---------|------|----------|------|
| cli_db_agent | 8110 | db/ | Read, Write, Edit, Glob, Grep, Bash |
| cli_backend_agent | 8111 | backend/ | Read, Write, Edit, Glob, Grep, Bash |

> **CLI 에이전트 상세**: `AG_Cohub/CLI_AGENT_GUIDE.md` 참조

## 에이전트 상세

| 에이전트 | 포트 | 설명 | 주요 도구 |
|---------|------|-----|----------|
| remote_agent | 8002 | 소수 판별 | is_prime, get_prime_factors |
| poetry_agent | 8003 | 시 분석 | analyze_poem, find_literary_devices |
| philosophy_agent | 8004 | 철학 인용 | get_philosopher_quote, compare_schools |
| history_agent | 8005 | 역사 이야기 | get_historical_event, compare_eras |
| calculator_agent | 8006 | 수학 계산 | calculate, fibonacci, factorial |

---

## 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 루트에서
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 설정
```

### 2. 개별 에이전트 실행

```bash
cd a2a_demo/calculator_agent
python agent.py
# → http://localhost:8006 에서 실행
```

### 3. 모든 에이전트 실행

```powershell
# Windows PowerShell (프로젝트 루트에서)
.\run_all.ps1

# 중지
.\stop_all.ps1
```

---

## 새 에이전트 추가 방법 (JSON 기반)

개발자나 AI가 새 에이전트를 추가하려면 아래 3단계를 따르세요.

### Step 1: 에이전트 Python 파일 생성

```python
# a2a_demo/weather_agent/agent.py

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# ===== 환경변수 로드 =====
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found")

# ===== 도구 정의 =====
def get_weather(city: str) -> dict:
    """도시의 날씨 정보를 가져옵니다.

    Args:
        city: 도시 이름

    Returns:
        날씨 정보 딕셔너리
    """
    # 실제로는 API 호출
    return {
        "city": city,
        "temperature": "22°C",
        "condition": "맑음",
        "humidity": "45%"
    }

def get_forecast(city: str, days: int = 3) -> dict:
    """도시의 일기예보를 가져옵니다.

    Args:
        city: 도시 이름
        days: 예보 일수 (기본 3일)

    Returns:
        일기예보 딕셔너리
    """
    return {
        "city": city,
        "forecast": [
            {"day": 1, "condition": "맑음", "temp": "23°C"},
            {"day": 2, "condition": "구름", "temp": "21°C"},
            {"day": 3, "condition": "비", "temp": "18°C"},
        ][:days]
    }

# ===== 에이전트 생성 =====
# 중요: name과 description은 AutoGen 등록 시 동일하게 사용!
weather_agent = Agent(
    model="openai/gpt-4o-mini",

    # ★ 핵심 필드 1: name
    # - Selector LLM이 이 이름으로 에이전트 선택
    # - AutoGen JSON 등록 시 동일하게 사용
    name="weather_agent",

    # ★ 핵심 필드 2: description
    # - Selector LLM이 이 설명을 보고 "이 에이전트가 적합한가?" 판단
    # - 구체적이고 명확하게 작성할수록 좋음
    description="날씨 정보와 일기예보를 제공하는 기상 전문 에이전트입니다. 현재 날씨, 기온, 습도, 향후 일기예보를 알려줍니다.",

    # instruction: 에이전트의 행동 방식
    instruction="""당신은 날씨 정보 전문 에이전트입니다.

주요 기능:
1. 현재 날씨 조회 (get_weather)
2. 일기예보 조회 (get_forecast)

응답 시:
- 정확한 정보 제공
- 날씨에 맞는 활동 추천
- 한국어로 친절하게 응답""",

    # tools: 에이전트가 사용할 도구들
    tools=[
        FunctionTool(get_weather),
        FunctionTool(get_forecast)
    ]
)

# ===== A2A 서버로 노출 =====
if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    PORT = 8011  # 사용하지 않는 포트 선택 (8011-8099 권장)

    print("=" * 50)
    print(f"Weather Agent - A2A Server")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Agent Card: http://localhost:{PORT}/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(weather_agent, port=PORT, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=PORT)
```

### Step 2: AutoGen Studio에 JSON으로 등록

**방법 A: UI에서 직접 등록**

AutoGen Studio UI (http://localhost:8081) 에서:
1. Build → Agents → New Agent
2. Provider: `autogenstudio.a2a.A2AAgent`
3. 아래 설정 입력

**방법 B: API로 등록**

```python
import requests

agent_config = {
    "user_id": "guestuser@gmail.com",
    "agent": {
        "provider": "autogenstudio.a2a.A2AAgent",
        "component_type": "agent",
        "version": 1,
        "label": "Weather Agent",
        "description": "날씨 정보와 일기예보를 제공하는 기상 전문 에이전트",
        "config": {
            # ★ name: A2A agent.py의 name과 동일해야 함!
            "name": "weather_agent",

            # ★ a2a_server_url: 에이전트 서버 주소
            "a2a_server_url": "http://localhost:8011",

            # ★ description: A2A agent.py의 description과 동일 권장
            "description": "날씨 정보와 일기예보를 제공하는 기상 전문 에이전트입니다.",

            "timeout": 60,
            "skills": []
        }
    }
}

response = requests.post(
    "http://127.0.0.1:8081/api/agents/",
    json=agent_config
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

**등록 JSON 전체 예시**

```json
{
    "provider": "autogenstudio.a2a.A2AAgent",
    "component_type": "agent",
    "version": 1,
    "label": "Weather Agent",
    "description": "날씨 정보와 일기예보를 제공하는 기상 전문 에이전트",
    "config": {
        "name": "weather_agent",
        "a2a_server_url": "http://localhost:8011",
        "description": "날씨 정보와 일기예보를 제공하는 기상 전문 에이전트입니다. 현재 날씨, 기온, 습도, 향후 일기예보를 알려줍니다.",
        "timeout": 60,
        "skills": []
    }
}
```

### Step 3: 팀에 추가하고 패턴 적용

Build → Teams에서:
1. 기존 팀에 에이전트 추가 또는 새 팀 생성
2. 패턴 선택 (예: debate, selector, sequential)
3. `team-factory.ts`가 자동으로 동적 `selector_prompt` 생성

---

## 패턴과 함께 사용

### Multi-Agent Debate 예제

A2A 에이전트들이 토론 패턴에 참여:

```
User: "인공지능의 미래에 대해 토론해주세요"

→ history_agent: 역사적 기술 발전 관점에서 분석
   "역사적으로 보면, 증기기관, 전기, 인터넷 등 모든 혁신은..."

→ philosophy_agent: 윤리적, 철학적 관점 제시
   "플라톤의 '동굴의 비유'를 빌리면, AI는..."

→ poetry_agent: 인문학적 상상력으로 미래 비전 제시
   "윌리엄 블레이크가 말했듯이 '한 알의 모래에서 세계를'..."

→ history_agent: 반론
   "하지만 역사적으로 기술 낙관론은 종종 부작용을..."

→ ... (계속 토론)
```

### 동작 원리 (상세)

```
1. 사용자가 패턴 선택 (예: debate)
   └─ UI에서 "Multi-Agent Debate" 클릭

2. team-factory.ts의 applyPatternToExistingTeam() 호출
   ├─ 기존 에이전트들 보존 (A2A 에이전트 포함)
   ├─ 패턴 구조 적용 (SelectorGroupChat)
   └─ 동적 selector_prompt 생성

3. generateDynamicSelectorPrompt() 함수
   입력: patternId="debate", agents=[
     {name: "history_agent", description: "역사 전문가..."},
     {name: "philosophy_agent", description: "철학 인용..."},
     {name: "poetry_agent", description: "시 분석..."}
   ]

   출력:
   "You are coordinating a multi-agent debate.

   Available Agents:
   - history_agent: 역사 전문가...
   - philosophy_agent: 철학 인용...
   - poetry_agent: 시 분석...

   Based on the conversation history, select the next speaker.
   Return ONLY the agent name."

4. Selector LLM이 다음 발언자 선택
   └─ "history_agent" → A2AAgent.on_messages() 호출

5. A2AAgent가 외부 A2A 서버 호출
   └─ POST http://localhost:8005 (JSON-RPC)

6. 응답을 팀에 반환 → 다음 턴 진행
```

---

## 포트 할당 규칙

| 범위 | 용도 |
|-----|-----|
| 8081 | AutoGen Studio |
| 8002-8010 | A2A 데모 에이전트 (이 폴더) |
| 8011-8099 | 사용자 정의 에이전트 |

---

## JSON 스키마 참조

### A2AAgent 설정 스키마

```typescript
interface A2AAgentConfig {
    name: string;              // 필수: 에이전트 이름 (selector가 사용)
    a2a_server_url: string;    // 필수: A2A 서버 URL
    description: string;       // 권장: 에이전트 설명 (selector가 참조)
    timeout: number;           // 선택: 요청 타임아웃 (기본 60초)
    skills: Array<object>;     // 선택: 스킬 목록
}
```

### 팀에 A2A 에이전트 포함 예시

```json
{
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team",
    "config": {
        "participants": [
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "history_agent",
                    "a2a_server_url": "http://localhost:8005",
                    "description": "역사 전문가"
                }
            },
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "philosophy_agent",
                    "a2a_server_url": "http://localhost:8004",
                    "description": "철학 인용 전문가"
                }
            }
        ],
        "model_client": {
            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
            "config": {"model": "gpt-4o-mini"}
        },
        "termination_condition": {
            "provider": "autogen_agentchat.conditions.TextMentionTermination",
            "config": {"text": "TERMINATE"}
        }
    }
}
```

---

## 문제 해결

### "OPENAI_API_KEY not found"
```bash
# .env 파일 확인
cat ../.env | grep OPENAI_API_KEY

# Windows
type ..\.env | findstr OPENAI_API_KEY
```

### 포트 충돌
```powershell
# Windows - 사용 중인 포트 확인
Get-NetTCPConnection -LocalPort 8005

# 프로세스 종료
Stop-Process -Id <PID> -Force
```

### A2A 연결 실패
```bash
# 에이전트 상태 확인
curl http://localhost:8005/.well-known/agent-card.json

# 직접 호출 테스트
curl -X POST http://localhost:8005 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","id":"1","params":{"message":{"messageId":"1","role":"user","parts":[{"type":"text","text":"테스트"}]}}}'
```

### Selector가 에이전트를 선택하지 않음
- `name`과 `description`이 A2A agent.py와 AutoGen JSON에서 일치하는지 확인
- `description`이 충분히 구체적인지 확인
- 브라우저 콘솔에서 `selector_prompt` 확인

---

## 체크리스트: 새 에이전트 추가 시

```
□ a2a_demo/{agent_name}/agent.py 생성
□ Agent()에 name, description, instruction, tools 정의
□ 포트 번호 선택 (8011-8099 권장)
□ python agent.py로 서버 실행 확인
□ curl로 agent-card.json 접근 확인
□ AutoGen Studio에 A2AAgent로 등록
  □ name이 agent.py와 동일
  □ description이 agent.py와 동일
  □ a2a_server_url이 정확한 포트
□ 팀에 추가하고 테스트
```

---

## 참조

- [A2A Protocol Spec](https://github.com/google/a2a)
- [Google ADK](https://github.com/google/adk-python)
- [AutoGen](https://github.com/microsoft/autogen)

---

## 🔗 관련 문서

| 문서 | 내용 |
|------|------|
| **AG_Cohub/CLI_AGENT_GUIDE.md** | CLI 에이전트 완전 가이드 (패턴 호환성) |
| **AG-cli/README.md** | Multi-Claude 자동 코딩 시스템 |
| **AG_Cohub/README.md** | 패턴 시스템 개요 |

---

*Last Updated: 2025-01-11*

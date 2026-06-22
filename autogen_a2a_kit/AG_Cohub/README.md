# AG_Cohub - Multi-Agent Collaboration Patterns

AI 에이전트 오케스트레이션을 위한 멀티 에이전트 협업 패턴 종합 컬렉션입니다.

---

## FOR AI ASSISTANTS - START HERE

> **📖 전체 문서 색인**: [`../DOCS_INDEX.md`](../DOCS_INDEX.md) - 모든 문서 목록 및 읽기 순서
>
> **이 섹션을 먼저 읽으세요!** AI가 이 프로젝트를 빠르게 이해하도록 설계되었습니다.

### 🚨 CLI 에이전트 작업 시 필독!

**CLI A2A 에이전트** (Claude Code 기반) 관련 작업이면 **먼저** 이 문서를 읽으세요:
- 📖 **`AG_Cohub/CLI_AGENT_GUIDE.md`** - CLI 에이전트 완전 가이드
  - 패턴 호환성 테스트 결과
  - Hierarchical 패턴 실패 원인 (handoff 미지원)
  - Pseudo-Hierarchical 패턴 구현
  - Debate 균형 로직 설명

### 다음에 읽어야 할 파일들 (순서대로)

```
Phase 0: CLI 에이전트 (선택적)
0. AG_Cohub/CLI_AGENT_GUIDE.md - CLI 에이전트 전용 가이드 ⭐

Phase 1: 패턴 시스템 이해
1. 이 파일 (AG_Cohub/README.md) - 전체 개요
2. AG_Cohub/patterns/README.md - 패턴 JSON 포맷 이해
3. AG_Cohub/loader/README.md - 로더 시스템 이해
4. AG_Cohub/templates/README.md - 팀 템플릿 이해

Phase 2: Frontend 코드 분석
5. frontend/.../agentflow/patterns/pattern-loader.ts - 패턴 로딩
6. frontend/.../team-runtime/team-factory.ts - 팀 설정 적용 (A2A 통합 핵심!)
7. frontend/.../chat/chat.tsx - WebSocket으로 백엔드 전송

Phase 3: A2A 통합 이해 (중요!)
8. ../a2a_demo/README.md - A2A 에이전트 추가 방법
9. ../autogen_source/.../autogenstudio/a2a/agent.py - A2AAgent 클래스
```

### 프로젝트 핵심 이해 (30초)

```
AG_Cohub/
├── patterns/           ← JSON 패턴 정의 (소스 오브 트루스!)
│   ├── 01_sequential.json
│   ├── 07_debate.json
│   └── ...
├── loader/             ← TypeScript 로더 (JSON → PatternDefinition)
├── templates/          ← TeamConfig JSON 템플릿
└── README.md           ← 이 파일
```

### 패턴이 실제로 어떻게 작동하는가

```
[패턴 JSON] → [pattern-loader.ts] → [PatternDefinition]
                                           ↓
[사용자가 패턴 선택] → [team-factory.ts] → [effectiveTeamConfig]
                                                  ↓
                                     [WebSocket으로 백엔드 전송]
                                                  ↓
                            [AutoGen이 provider에 따라 팀 실행]
```

### 핵심 매핑 (Pattern → AutoGen Provider → 동작)

| Pattern ID | AutoGen Provider | 실제 동작 |
|------------|------------------|----------|
| sequential, reflection | `RoundRobinGroupChat` | A→B→C→A→B→C (고정 순서) |
| selector, debate, group_chat | `SelectorGroupChat` | **LLM이 다음 화자 선택** |
| handoff | `Swarm` | **에이전트가 HandoffMessage로 결정** |
| magentic | `MagenticOneGroupChat` | 오케스트레이터가 동적 계획 |

**중요**: `SelectorGroupChat`은 `selector_prompt`를 사용해 LLM이 다음 화자를 선택합니다!

---

## 데이터 흐름 상세

### 1. 패턴 정의 (patterns/*.json)

```json
{
  "id": "debate",
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "team_config": {
      "selector_prompt": "토론 규칙: advocate와 critic이 번갈아 발언..."
    }
  }
}
```

### 2. Frontend 로딩 (pattern-loader.ts)

```typescript
// patterns/*.json에서 selector_prompt 추출
function getPrompts(json): { selector?: string } {
  const selectorPrompt = json.autogen_implementation.team_config?.selector_prompt;
  return selectorPrompt ? { selector: selectorPrompt } : undefined;
}
```

### 3. 팀 설정 적용 (team-factory.ts:231-238)

```typescript
// SelectorGroupChat이면 selector_prompt 추가
if (pattern.autogenProvider === "SelectorGroupChat") {
  config.selector_prompt = pattern.prompts?.selector || "";
}
```

### 4. 백엔드 전송 (chat.tsx:589)

```typescript
socket.send(JSON.stringify({
  type: "start",
  team_config: effectiveTeamConfig,  // selector_prompt 포함!
}));
```

---

## 패턴별 실제 동작

### Sequential (RoundRobinGroupChat)

```
에이전트 순서: [A, B, C]
실행: A → B → C → A → B → C → ...
선택 로직: current_index = (current_index + 1) % len(agents)
```

### Debate (SelectorGroupChat + selector_prompt)

```
에이전트: [advocate, critic, judge]
selector_prompt: "토론 규칙: advocate와 critic이 번갈아..."

1. advocate: "이 기술의 장점은..."
2. [LLM이 selector_prompt 읽고 판단] → critic 선택
3. critic: "하지만 리스크가..."
4. [LLM 판단] → advocate 선택
5. ... (토론 반복)
6. [LLM이 "충분한 토론" 판단] → judge 선택
7. judge: "최종 결론은... TERMINATE"
```

### Handoff (Swarm)

```
에이전트: [triage, sales, support]
handoffs 설정: triage.handoffs = ["sales", "support"]

1. triage: "이건 판매 문의입니다" + HandoffMessage(target="sales")
2. [Swarm이 HandoffMessage 감지] → sales 활성화
3. sales: "판매 관련 답변..."
```

---

## 새 패턴 추가 방법

### Step 1: patterns/ 폴더에 JSON 생성

`patterns/10_my_pattern.json`:

```json
{
  "id": "my_pattern",
  "name": { "en": "My Pattern", "ko": "내 패턴" },
  "description": { "en": "Description", "ko": "설명" },
  "diagram": "A → B → C",
  "complexity": "medium",
  "when_to_use": ["Use case 1"],
  "when_to_avoid": ["Avoid case 1"],
  "pros": ["Pro 1"],
  "cons": ["Con 1"],
  "example_use_cases": [{ "name": "Example" }],
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "team_config": {
      "participants": [
        {
          "provider": "autogen_agentchat.agents.AssistantAgent",
          "component_type": "agent",
          "config": {
            "name": "Agent_A",
            "description": "First agent",
            "system_message": "You are Agent A."
          }
        }
      ],
      "selector_prompt": "다음 에이전트를 선택하세요..."
    }
  },
  "references": [{ "title": "Reference", "url": "https://..." }]
}
```

### Step 2: Frontend data 폴더에 복사

```bash
cp patterns/10_my_pattern.json \
   AG-Frontend/src/.../agentflow/patterns/data/
```

### Step 3: pattern-loader.ts에 import 추가

```typescript
import myPattern from "./data/10_my_pattern.json";

const PATTERN_JSON_FILES = [
  // ... existing
  myPattern as CoHubPatternJSON,
];
```

### Step 4: 빌드 및 테스트

```bash
cd AG-Frontend && npm run build
```

---

## 파일별 역할

| 파일 | 역할 |
|------|------|
| `patterns/*.json` | 패턴 정의 (소스 오브 트루스) |
| `loader/index.ts` | 로더 진입점 |
| `loader/types.ts` | TypeScript 타입 정의 |
| `loader/converter.ts` | JSON → PatternDefinition 변환 |
| `loader/providers.json` | Provider 기본 설정 (색상, 아이콘 등) |
| `templates/*.json` | 실행 가능한 팀 설정 템플릿 |

---

## Frontend 통합 경로

```
AG_Cohub/patterns/*.json
        ↓ (복사)
autogen-studio/frontend/src/components/views/playground/chat/agentflow/patterns/data/*.json
        ↓ (import)
pattern-loader.ts
        ↓ (변환)
PATTERN_LIBRARY: PatternDefinition[]
        ↓ (사용)
team-factory.ts → effectiveTeamConfig
        ↓ (전송)
chat.tsx → WebSocket → Backend
```

---

## 디버깅 팁

### selector_prompt가 적용되는지 확인

```typescript
// chat.tsx에서 console.log 추가
console.log('effectiveTeamConfig:', effectiveTeamConfig);
console.log('selector_prompt:', effectiveTeamConfig?.config?.selector_prompt);
```

### 백엔드에서 어떤 provider가 사용되는지 확인

```python
# teammanager.py에서 로깅
print(f"Team provider: {team_config['provider']}")
print(f"Selector prompt: {team_config['config'].get('selector_prompt')}")
```

---

## 관련 문서

- **AutoGen 공식 문서**
  - [SelectorGroupChat](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html)
  - [Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html)
  - [MagenticOne](https://microsoft.github.io/autogen/stable/user-guide/extensions-user-guide/magentic-one.html)

- **연구 논문**
  - [Multi-Agent Collaboration Mechanisms Survey](https://arxiv.org/abs/2501.06322)
  - [MetaGPT](https://arxiv.org/abs/2308.00352)
  - [Magentic-One](https://arxiv.org/abs/2411.04468)

---

## A2A 에이전트와 패턴 통합

> **중요**: 패턴은 에이전트 협업 **방식**을 정의하고, A2A는 **외부 에이전트**를 연결합니다. 둘은 함께 작동합니다!

### 패턴 + A2A의 관계

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pattern + A2A 협업                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pattern (협업 방식)          A2A (외부 에이전트)                  │
│  ├─ SelectorGroupChat        ├─ history_agent (port 8005)       │
│  ├─ RoundRobinGroupChat      ├─ philosophy_agent (port 8004)    │
│  └─ Swarm                    └─ poetry_agent (port 8003)        │
│           │                              │                       │
│           └──────────┬───────────────────┘                       │
│                      ▼                                           │
│           team-factory.ts                                        │
│           ├─ 기존 A2A 에이전트 보존                               │
│           ├─ 패턴 구조 적용                                       │
│           └─ 동적 selector_prompt 생성                           │
│                      │                                           │
│                      ▼                                           │
│           "Available Agents:                                     │
│            - history_agent: 역사 전문가...                        │
│            - philosophy_agent: 철학 인용..."                      │
│                      │                                           │
│                      ▼                                           │
│           Selector LLM이 에이전트 선택                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 핵심: team-factory.ts의 동적 프롬프트 생성

```typescript
// team-factory.ts의 핵심 로직

// 1. AgentInfo 인터페이스 - A2A 에이전트의 name과 description
interface AgentInfo {
  name: string;        // "history_agent"
  description: string; // "역사 전문가..."
}

// 2. 동적 selector_prompt 생성
const generateDynamicSelectorPrompt = (patternId, agents: AgentInfo[]) => {
  const agentList = agents.map(a =>
    `- ${a.name}: ${a.description}`
  ).join("\n");

  return `You are coordinating a multi-agent debate.

Available Agents:
${agentList}

Based on the conversation, select the next speaker.
Return ONLY the agent name.`;
};

// 3. 패턴 적용 시 기존 A2A 에이전트 보존
export const applyPatternToExistingTeam = (existingTeam, patternId) => {
  // ★ 기존 에이전트가 있으면 항상 보존!
  if (existingParticipantCount > 0) {
    // A2A 에이전트 유지, 패턴 구조만 적용
    const existingAgents = existingParticipants.map(p => ({
      name: p.config?.name,
      description: p.config?.description
    }));

    // 동적 selector_prompt 생성
    config.selector_prompt = generateDynamicSelectorPrompt(patternId, existingAgents);
  }
};
```

### Debate 패턴 + A2A 에이전트 예시

```
팀 구성:
├─ history_agent (A2A, port 8005) - "역사 전문가"
├─ philosophy_agent (A2A, port 8004) - "철학 인용 전문가"
└─ poetry_agent (A2A, port 8003) - "시 분석 전문가"

패턴 선택: "debate" (SelectorGroupChat)

team-factory.ts가 생성한 selector_prompt:
"You are coordinating a multi-agent debate.

Available Agents:
- history_agent: 역사 전문가...
- philosophy_agent: 철학 인용 전문가...
- poetry_agent: 시 분석 전문가...

Debate Rules:
1. Each agent takes turns presenting their unique perspective
2. Agents should respond to and challenge each other's arguments
..."

실행 결과:
User: "인공지능의 미래에 대해 토론해주세요"

→ Selector LLM 판단: "역사적 관점부터 시작" → history_agent
→ history_agent: "역사적으로 보면 기술 혁신은..."

→ Selector LLM 판단: "철학적 관점 필요" → philosophy_agent
→ philosophy_agent: "플라톤의 동굴 비유를 빌리면..."

→ Selector LLM 판단: "인문학적 관점" → poetry_agent
→ poetry_agent: "윌리엄 블레이크의 시에서..."
```

### 패턴별 A2A 호환성

| 패턴 | A2A 호환 | 설명 |
|------|----------|------|
| **debate** | ✅ 완벽 | Selector가 description 기반으로 전문가 선택 |
| **selector** | ✅ 완벽 | 동일 - 질문에 맞는 에이전트 선택 |
| **sequential** | ✅ 가능 | 순서대로 발언 (A→B→C) |
| **reflection** | ✅ 가능 | producer-reviewer 구조 |
| **handoff** | ⚠️ 제한적 | A2A는 HandoffMessage 생성 불가 |

### A2A 에이전트 추가 후 패턴 테스트

1. A2A 에이전트 서버 실행:
   ```bash
   python a2a_demo/history_agent/agent.py   # port 8005
   python a2a_demo/philosophy_agent/agent.py # port 8004
   ```

2. AutoGen Studio에서 A2A 에이전트 등록

3. 팀 생성 후 "debate" 패턴 선택

4. team-factory.ts가 자동으로:
   - 기존 A2A 에이전트 보존
   - 동적 selector_prompt 생성

5. 테스트 메시지 전송하여 토론 확인

---

## Claude Max OAuth 모델 (API 키 없이 Claude 사용)

> **핵심**: Claude Max 구독자는 API 키 없이 `claude` CLI를 통해 AutoGen Studio에서 Claude 모델 사용 가능.

### 구조 (2026-02-06 SDK 리팩토링)

```
AG_Cohub/
├── model_factory.py                   ← Slim AutoGen ChatCompletionClient (SDK에 위임)
│   ├── ClaudeCLIChatCompletionClient  ← AutoGen 호환 래퍼
│   │   ├── create()    → ClaudeSDK.query() (SDK 우선, subprocess 폴백)
│   │   └── agent_config: dict 수용   ← JSON 팀 설정에서 프로필 전달
│   └── get_model_client()             ← 팩토리
│
├── sdk/                               ← 모듈화된 SDK 패키지 (7개 모듈)
│   ├── auth.py      OAuth 토큰 관리 (~/.claude/.credentials.json)
│   ├── config.py    ToolProfile, AgentConfig, PermissionMode, ROLE_PRESETS
│   ├── client.py    ClaudeSDK 래퍼 (query + conversation)
│   │                [TOOL EXECUTED: Write] 마커 + ToolResultBlock 처리
│   ├── context.py   ProjectContext + ContextManager (cwd, SharedMemory 8101)
│   ├── hooks.py     quality/logging/budget/security 훅
│   └── tools.py     MCP 도구 스키마 (shared_memory, project, autogen)
│
├── patterns/        패턴 JSON 정의
├── templates/       팀 설정 템플릿
└── loader/          TypeScript 로더
```

### ToolProfile 시스템 (sdk/config.py)

| Profile | 도구 | JSON 설정 |
|---------|------|-----------|
| TEXT_ONLY | `tools=[]` | `"profile": "text_only"` |
| READER | Read, Glob, Grep, WebSearch | `"profile": "reader"` |
| CODER | Read, Write, Edit, Bash, Glob, Grep | `"profile": "coder"` |
| FULL_AGENT | `tools=None` (전체) | `"profile": "full_agent"` |

### Plan Mode

`"permission_mode": "plan"` - Claude Code의 공식 plan mode.
Read/Glob/Grep만 가능, Write/Edit/Bash 차단.

```json
"agent_config": {"profile": "reader", "permission_mode": "plan", "cwd": "D:\\AC247"}
```

### [TOOL EXECUTED] 마커 (sdk/client.py)

SDK가 도구를 실행하면 응답에 마커를 삽입하여 다른 에이전트가 도구 사용 여부를 판별:

```
[TOOL EXECUTED: Write] -> D:\AC247\calc.py
[TOOL EXECUTED: Bash] $ python D:\AC247\calc.py
[TOOL RESULT]: Tests passed (5/5)
```

### Gallery에 등록된 Claude 모델 (3개)

| 모델 | label | model ID |
|------|-------|----------|
| Sonnet 4.5 | Claude Sonnet 4.5 (Max OAuth) | `claude-sonnet-4-5-20250929` |
| Opus 4.5 | Claude Opus 4.5 (Max OAuth) | `claude-opus-4-5-20251101` |
| Haiku 4.5 | Claude Haiku 4.5 (Max OAuth) | `claude-haiku-4-5-20251001` |

**전용 Gallery**: `Claude Max Models (OAuth)` (Gallery ID: **11**, `claude_max_models`)
- Default Gallery(ID 9/10)는 건드리지 않음
- Claude 전용 Gallery를 별도로 생성하여 관리

### Gallery 재생성 방법 (DB 초기화 등으로 사라졌을 때)

```python
import urllib.request, json, sqlite3

# 1. 전용 Gallery 생성 (POST)
gallery_config = {
    'config': {
        'id': 'claude_max_models',
        'name': 'Claude Max Models (OAuth)',
        'metadata': {
            'author': 'AG_Cohub',
            'description': 'Claude Max 구독의 OAuth로 API 키 없이 사용하는 Claude 모델들',
            'version': '1.0.0'
        },
        'components': [
            {
                'provider': 'AG_Cohub.model_factory.ClaudeCLIChatCompletionClient',
                'component_type': 'model', 'version': 1, 'component_version': 1,
                'label': 'Claude Sonnet 4.5 (Max OAuth)',
                'description': 'Claude Sonnet 4.5 - Max 구독 OAuth, API 키 불필요. 범용 코딩/분석.',
                'config': {'model': 'claude-sonnet-4-5-20250929'}
            },
            {
                'provider': 'AG_Cohub.model_factory.ClaudeCLIChatCompletionClient',
                'component_type': 'model', 'version': 1, 'component_version': 1,
                'label': 'Claude Opus 4.5 (Max OAuth)',
                'description': 'Claude Opus 4.5 - Max 구독 OAuth, API 키 불필요. 고급 추론/분석.',
                'config': {'model': 'claude-opus-4-5-20251101'}
            },
            {
                'provider': 'AG_Cohub.model_factory.ClaudeCLIChatCompletionClient',
                'component_type': 'model', 'version': 1, 'component_version': 1,
                'label': 'Claude Haiku 4.5 (Max OAuth)',
                'description': 'Claude Haiku 4.5 - Max 구독 OAuth, API 키 불필요. 빠른 응답.',
                'config': {'model': 'claude-haiku-4-5-20251001'}
            }
        ]
    }
}
data = json.dumps(gallery_config).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8081/api/gallery/?user_id=guestuser@gmail.com',
    data=data, headers={'Content-Type': 'application/json'}
)
resp = json.loads(urllib.request.urlopen(req).read())
new_id = resp['data']['id']
print(f'Gallery created: ID {new_id}')

# 2. user_id 수정 (API가 user_id를 NULL로 생성하는 경우)
db_path = r'C:\Users\SOGANG1\.autogenstudio\autogen04203.db'
conn = sqlite3.connect(db_path)
conn.execute(f"UPDATE gallery SET user_id = 'guestuser@gmail.com' WHERE id = {new_id} AND user_id IS NULL")
conn.commit()
conn.close()
print(f'Gallery {new_id} user_id fixed')

# 3. 확인
resp = urllib.request.urlopen('http://127.0.0.1:8081/api/gallery/?user_id=guestuser@gmail.com')
galleries = json.loads(resp.read())['data']
for g in galleries:
    print(f"  Gallery {g['id']}: {g['config']['name']}")
```

**왜 전용 Gallery인가?**
- Default Gallery를 수정하면 AutoGen Studio 업데이트 시 충돌 가능
- Claude 모델만 별도 관리하면 추가/삭제가 깔끔
- Gallery ID가 변경되어도 `claude_max_models`라는 config ID로 식별 가능

### Import 경로 설정

AG_Cohub 모듈이 AutoGen Studio에서 import 가능해야 함:

1. **`.pth` 파일** (자동 import 경로):
   ```
   C:\Users\SOGANG1\AppData\Roaming\Python\Python313\site-packages\ag_cohub.pth
   내용: D:\Data\25_ACE\AG\autogen_a2a_kit
   ```

2. **`start_autogen.py`에서도 경로 추가**:
   ```python
   sys.path.insert(0, r"D:\Data\25_ACE\AG\autogen_a2a_kit")
   ```

### 서버 실행 (start_autogen.py)

```powershell
python D:\Data\25_ACE\AG\start_autogen.py
# → http://127.0.0.1:8081
```

**주의**: `autogenstudio` CLI 명령어는 설치되어 있지 않음. 반드시 `start_autogen.py`로 실행.

### 프론트엔드 빌드 & 배포

> **커스텀 프론트엔드**: `AG-frontend/` (Vite + React 19)을 사용합니다. `cd AG-frontend && npm run dev`
> 아래는 AutoGen Studio **내장 UI (upstream 원본)** 빌드 참고용입니다.

UI가 깨질 때 (webpack JS 404 에러) 다음 순서로 수행:

```powershell
# 1. 빌드
cd D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio\frontend
npm install --legacy-peer-deps
npx gatsby clean
npx gatsby build --prefix-paths

# 2. 실제 UI 경로에 복사 (★ 중요: 22_AG 경로!)
#    autogenstudio 패키지가 D:\Data\22_AG\...에서 import되므로 거기에 복사해야 함
Copy-Item -Path "public\*" `
  -Destination "D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio\autogenstudio\web\ui\" `
  -Recurse -Force

# 3. 서버 재시작
python D:\Data\25_ACE\AG\start_autogen.py

# 4. 브라우저에서 Ctrl+Shift+R (강제 새로고침, 캐시 무시)
```

**★ UI 복사 경로 주의**:
- `autogenstudio` 패키지는 `D:\Data\22_AG\...`에서 로드됨 (Python import 경로)
- `25_ACE`가 아닌 `22_AG` 경로의 `web/ui/`에 복사해야 함
- 틀린 경로에 복사하면 webpack JS 404 에러 발생

### 동작 확인 (WebSocket 테스트)

```python
import asyncio, json, urllib.request, websockets

with open(r'D:\Data\25_ACE\AG\team27_config.json') as f:
    team_config = json.load(f)

async def test():
    # Run 생성
    data = json.dumps({'session_id': 125, 'user_id': 'guestuser@gmail.com', 'task': 'test'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8081/api/runs/?user_id=guestuser@gmail.com',
        data=data, headers={'Content-Type': 'application/json'})
    run_id = json.loads(urllib.request.urlopen(req).read())['data']['run_id']

    # WebSocket 실행
    uri = f'ws://127.0.0.1:8081/api/ws/runs/{run_id}?user_id=guestuser@gmail.com'
    async with websockets.connect(uri, ping_interval=30, ping_timeout=120) as ws:
        await ws.recv()  # connected
        await ws.send(json.dumps({'type': 'start', 'task': 'What is 2+3?', 'team_config': team_config}))
        while True:
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=120))
            print(f"[{resp.get('type')}] {str(resp)[:200]}")
            if resp.get('type') in ('result', 'error'):
                break

asyncio.run(test())
```

**참고**: Claude CLI 응답에 ~60초 소요. WebSocket 타임아웃을 120초 이상으로 설정할 것.

### 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| webpack JS 404 에러 | 프론트엔드 빌드 해시 불일치 | upstream UI rebuild → `22_AG` 경로에 복사 → Ctrl+Shift+R, 또는 `AG-frontend/` 사용 권장 |
| Sessions 0, "Create a team" | JS 로드 실패로 API 호출 안 됨 | 위와 동일 (데이터는 안 사라짐) |
| Run이 CREATED에 머무름 | REST API만으로는 실행 안 됨 | WebSocket으로 `type: start` + `team_config` 전송 필요 |
| Claude CLI 응답 없음 | `claude` CLI 미설치 또는 미로그인 | `claude /login` 실행 |
| `ModuleNotFoundError: AG_Cohub` | import 경로 미설정 | `.pth` 파일 확인 또는 `sys.path.insert` |
| OAuth token not found | 크리덴셜 파일 없음 | `claude /login` 후 `~/.claude/.credentials.json` 확인 |

### E2E 테스트 결과 (2026-02-07)

| 팀 | Run# | 결과 | 비고 |
|----|------|------|------|
| Reflection | #152 | PASS | critic APPROVED |
| Code Generation | #155 | PASS | 7984 chars |
| Handoff | #177 | PASS | triage->refund->triage->support |
| Debate | #178 | PASS | advocate->critic->judge(TERMINATE) |
| Tool Execution | #182 | PASS | fibonacci.py 생성, D:\AC247 |

---

*Last Updated: 2026-02-07*
*SDK Package + Tool Execution + Plan Mode: 2026-02-07*
*Claude Max OAuth Model Factory Added: 2026-01-29*
*CLI Agent Guide Added: 2025-01-11*

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
   frontend/src/.../agentflow/patterns/data/
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
cd frontend && npm run build
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

*Last Updated: 2025-01-11*
*CLI Agent Guide Added: 2025-01-11*

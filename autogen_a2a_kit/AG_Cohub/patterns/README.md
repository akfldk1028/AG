# AG_Cohub/patterns - Pattern JSON Definitions

멀티 에이전트 협업 패턴의 JSON 정의 파일들입니다.

---

## FOR AI ASSISTANTS

### 다음에 읽어야 할 파일들

```
이 폴더 내:
1. 07_debate.json - SelectorGroupChat + selector_prompt 예시
2. 01_sequential.json - RoundRobinGroupChat 예시
3. 05_handoff.json - Swarm + handoffs 예시

상위 폴더:
4. AG_Cohub/loader/README.md - JSON이 어떻게 변환되는지

Frontend:
5. frontend/.../agentflow/patterns/data/ - 실제 사용되는 복사본
6. frontend/.../agentflow/patterns/pattern-loader.ts - JSON import 위치
```

### 핵심 이해 (30초)

```
패턴 JSON의 핵심 차이점:

RoundRobinGroupChat (순차):
  - A → B → C → A → B → C (고정 순서)
  - selector_prompt 없음

SelectorGroupChat (동적):
  - LLM이 매 턴 다음 화자 선택
  - selector_prompt 필수! ← 이게 핵심!

Swarm (핸드오프):
  - 에이전트가 HandoffMessage로 결정
  - handoffs 배열 필요
```

### selector_prompt가 왜 중요한가?

```json
// 07_debate.json에서
"autogen_implementation": {
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "team_config": {
    "selector_prompt": "토론 규칙: advocate와 critic이 번갈아 발언..."
  }
}
```

이 `selector_prompt`가 LLM에게 "누가 다음에 말해야 하는지" 알려줍니다.
없으면 LLM이 임의로 선택 → 토론이 아니라 무작위 대화가 됨!

---

## 파일 목록

| 파일 | 패턴 | Provider | 핵심 설정 |
|------|------|----------|----------|
| `01_sequential.json` | Sequential | RoundRobinGroupChat | 없음 (고정 순서) |
| `02_concurrent.json` | Concurrent | Custom | asyncio 병렬 |
| `03_selector.json` | Selector | SelectorGroupChat | selector_prompt |
| `04_group_chat.json` | Group Chat | SelectorGroupChat | selector_prompt |
| `05_handoff.json` | Handoff | Swarm | handoffs |
| `06_magentic.json` | Magentic-One | MagenticOneGroupChat | 오케스트레이터 |
| `07_debate.json` | Debate | SelectorGroupChat | selector_prompt |
| `08_reflection.json` | Reflection | RoundRobinGroupChat | 없음 |
| `09_hierarchical.json` | Hierarchical | Nested Teams | 중첩 팀 |

---

## JSON 스키마

### 필수 필드

```json
{
  "id": "pattern_name",
  "name": { "en": "English Name", "ko": "한국어 이름" },
  "description": { "en": "Description", "ko": "설명" },
  "diagram": "A → B → C",
  "complexity": "low | medium | high | very-high",
  "when_to_use": ["사용 사례 1"],
  "when_to_avoid": ["피해야 할 상황"],
  "pros": ["장점"],
  "cons": ["단점"],
  "example_use_cases": [{ "name": "예시" }],
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.XXX",
    "team_config": { "participants": [...] }
  },
  "references": [{ "title": "제목", "url": "https://..." }]
}
```

### autogen_implementation (Provider별)

#### RoundRobinGroupChat (순차 패턴)

```json
"autogen_implementation": {
  "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
  "team_config": {
    "participants": [
      {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent",
        "config": {
          "name": "agent_a",
          "description": "First agent",
          "system_message": "You are agent A."
        }
      }
    ]
  }
}
```

#### SelectorGroupChat (동적 선택)

```json
"autogen_implementation": {
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "team_config": {
    "participants": [...],
    "selector_prompt": "다음 에이전트를 선택하세요. 규칙: ..."  // 핵심!
  }
}
```

#### Swarm (핸드오프)

```json
"autogen_implementation": {
  "provider": "autogen_agentchat.teams.Swarm",
  "team_config": {
    "participants": [
      {
        "config": {
          "name": "triage",
          "handoffs": ["sales", "support"]  // 핸드오프 대상!
        }
      }
    ]
  }
}
```

### visual_override (선택적)

```json
"visual_override": {
  "layout": "chain | hub-spoke | mesh | tree | fork-join | ring",
  "category": "sequential | dynamic | parallel | hierarchical",
  "icon": "ArrowRight | GitBranch | Share2 | RefreshCw | GitMerge | Network",
  "primaryColor": "#3b82f6",
  "secondaryColor": "#93c5fd",
  "edgeStyle": "solid | dashed | animated",
  "bidirectional": true | false,
  "showCrossConnections": true | false,
  "centerNodeType": "selector | supervisor | aggregator | triage"
}
```

---

## 새 패턴 추가 (Step by Step)

### Step 1: JSON 파일 생성

`patterns/10_my_pattern.json`:

```json
{
  "id": "my_pattern",
  "name": { "en": "My Pattern", "ko": "내 패턴" },
  "description": { "en": "Description", "ko": "설명" },
  "diagram": "A → B → C",
  "complexity": "medium",
  "when_to_use": ["Use case"],
  "when_to_avoid": ["Avoid case"],
  "pros": ["Pro"],
  "cons": ["Con"],
  "example_use_cases": [{ "name": "Example" }],
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "team_config": {
      "participants": [
        {
          "provider": "autogen_agentchat.agents.AssistantAgent",
          "component_type": "agent",
          "config": {
            "name": "agent_a",
            "description": "Agent A",
            "system_message": "You are agent A."
          }
        }
      ],
      "selector_prompt": "다음 에이전트를 선택하세요..."
    }
  },
  "references": []
}
```

### Step 2: Frontend data 폴더에 복사

```bash
# Windows
copy patterns\10_my_pattern.json ^
     ..\autogen_source\python\packages\autogen-studio\frontend\src\components\views\playground\chat\agentflow\patterns\data\
```

### Step 3: pattern-loader.ts에 import 추가

```typescript
// pattern-loader.ts
import myPattern from "./data/10_my_pattern.json";

const PATTERN_JSON_FILES: CoHubPatternJSON[] = [
  // ... existing
  myPattern as CoHubPatternJSON,
];
```

### Step 4: 빌드

```bash
cd frontend && npm run build
```

---

## Provider 선택 가이드

```
어떤 Provider를 써야 할까?

고정된 순서로 실행?
├─ Yes → RoundRobinGroupChat
└─ No: LLM이 다음 화자 결정?
        ├─ Yes → SelectorGroupChat (+ selector_prompt 필수!)
        └─ No: 에이전트가 다음 화자 결정?
                ├─ Yes → Swarm (+ handoffs 필수!)
                └─ No: 복잡한 작업 계획?
                        ├─ Yes → MagenticOneGroupChat
                        └─ No → RoundRobinGroupChat
```

---

## 파일 네이밍 규칙

- `01_sequential.json` - 번호 + 언더스코어 + 이름
- `_template.json` - 언더스코어로 시작하면 무시됨

---

## 연결 경로

```
AG_Cohub/patterns/*.json (소스 오브 트루스)
        ↓ 복사
frontend/.../agentflow/patterns/data/*.json
        ↓ import in pattern-loader.ts
PATTERN_LIBRARY: PatternDefinition[]
        ↓
team-factory.ts → effectiveTeamConfig
        ↓
chat.tsx → WebSocket → Backend
```

---

*Last Updated: 2025-01-09*

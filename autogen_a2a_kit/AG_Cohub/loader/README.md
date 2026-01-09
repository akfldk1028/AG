# AG_Cohub/loader - Pattern Loading System

JSON 패턴 파일을 TypeScript PatternDefinition으로 변환하는 로더 시스템입니다.

---

## FOR AI ASSISTANTS

### 다음에 읽어야 할 파일들

```
이 폴더 내:
1. types.ts - 타입 정의 (CoHubPatternJSON, PatternDefinition)
2. providers.json - Provider 기본 설정 (색상, 아이콘)
3. converter.ts - JSON → PatternDefinition 변환 로직
4. index.ts - 진입점 및 API

Frontend 연결:
5. frontend/.../agentflow/patterns/pattern-loader.ts - 실제 사용처
```

### 이 폴더의 역할

```
patterns/*.json
      ↓ (이 loader가 변환)
PatternDefinition (UI용)
TeamConfig (런타임용)
```

---

## 파일 구조

```
loader/
├── index.ts        ← 진입점 (createPatternLibrary, loadAllPatterns)
├── types.ts        ← 타입 정의
├── providers.json  ← Provider 기본 설정 (색상, 아이콘 등)
├── providers.ts    ← providers.json 로더
├── converter.ts    ← JSON → PatternDefinition/TeamConfig 변환
└── README.md       ← 이 파일
```

---

## 핵심 타입 (types.ts)

### CoHubPatternJSON (입력: patterns/*.json)

```typescript
interface CoHubPatternJSON {
  id: string;
  name: { en: string; ko: string };
  description: { en: string; ko: string };
  autogen_implementation: {
    provider: string;  // "autogen_agentchat.teams.SelectorGroupChat"
    team_config?: {
      participants: [...];
      selector_prompt?: string;  // 핵심!
    };
  };
  visual_override?: { layout, icon, primaryColor, ... };
}
```

### PatternDefinition (출력: UI용)

```typescript
interface PatternDefinition {
  id: string;
  name: string;
  category: "sequential" | "dynamic" | "parallel" | "hierarchical";
  visual: { layout, icon, primaryColor, secondaryColor, ... };
  autogenProvider: string;        // "SelectorGroupChat"
  autogenProviderFull: string;    // "autogen_agentchat.teams.SelectorGroupChat"
  prompts?: { selector?: string }; // selector_prompt!
}
```

### Component<TeamConfig> (출력: 런타임용)

```typescript
interface Component<TeamConfig> {
  provider: string;
  component_type: "team";
  config: {
    participants: [...];
    selector_prompt?: string;
    model_client?: {...};
    termination_condition?: {...};
  };
}
```

---

## 핵심 함수 (index.ts)

### createPatternLibrary (Frontend용)

```typescript
// Vite glob import 사용
const modules = import.meta.glob('../patterns/*.json', { eager: true });
const library = createPatternLibrary(modules);

library.PATTERN_LIBRARY      // PatternDefinition[]
library.PATTERN_TEMPLATES    // Record<string, Component<TeamConfig>>
library.getPatternById(id)   // PatternDefinition | undefined
library.getTemplateById(id)  // Component<TeamConfig> | undefined
```

### loadAllPatterns (Backend/Node.js용)

```typescript
const library = await loadAllPatterns('./patterns');
// 동일한 출력
```

---

## 변환 로직 (converter.ts)

### convertToPatternDefinition

```typescript
function convertToPatternDefinition(json: CoHubPatternJSON): PatternDefinition {
  const provider = getProvider(json.autogen_implementation.provider);

  return {
    id: json.id,
    name: json.name.en,
    category: json.visual_override?.category || provider.category,
    visual: {
      layout: json.visual_override?.layout || provider.layout,
      icon: json.visual_override?.icon || provider.icon,
      primaryColor: json.visual_override?.primaryColor || provider.colors.primary,
      // ...
    },
    autogenProvider: extractProviderShort(json.autogen_implementation.provider),
    autogenProviderFull: json.autogen_implementation.provider,
    prompts: getPrompts(json),  // selector_prompt 추출!
  };
}
```

### getPrompts (핵심!)

```typescript
function getPrompts(json: CoHubPatternJSON): { selector?: string } | undefined {
  const selectorPrompt = json.autogen_implementation.team_config?.selector_prompt;
  return selectorPrompt ? { selector: selectorPrompt } : undefined;
}
```

---

## Provider 설정 (providers.json)

```json
{
  "RoundRobinGroupChat": {
    "full": "autogen_agentchat.teams.RoundRobinGroupChat",
    "category": "sequential",
    "layout": "chain",
    "icon": "ArrowRight",
    "colors": { "primary": "#3b82f6", "secondary": "#93c5fd" },
    "communicationStyle": "turn-based",
    "requiresModelClient": false
  },
  "SelectorGroupChat": {
    "full": "autogen_agentchat.teams.SelectorGroupChat",
    "category": "dynamic",
    "layout": "hub-spoke",
    "icon": "GitBranch",
    "colors": { "primary": "#8b5cf6", "secondary": "#c4b5fd" },
    "communicationStyle": "request-response",
    "requiresModelClient": true
  },
  "Swarm": {
    "full": "autogen_agentchat.teams.Swarm",
    "category": "dynamic",
    "layout": "mesh",
    "icon": "Share2",
    "colors": { "primary": "#10b981", "secondary": "#6ee7b7" },
    "communicationStyle": "event-driven",
    "requiresModelClient": false
  }
}
```

---

## 사용 예시

### Frontend (Vite + React)

```typescript
// 1. Glob import
const modules = import.meta.glob('../AG_Cohub/patterns/*.json', { eager: true });

// 2. 라이브러리 생성
import { createPatternLibrary } from '../AG_Cohub/loader';
const { PATTERN_LIBRARY, getPatternById } = createPatternLibrary(modules);

// 3. 패턴 사용
const debatePattern = getPatternById('debate');
console.log(debatePattern?.prompts?.selector);
// → "토론 규칙: advocate와 critic이 번갈아..."
```

### Backend (Node.js)

```typescript
import { loadAllPatterns } from './AG_Cohub/loader';

const library = await loadAllPatterns('./AG_Cohub/patterns');
const template = library.getTemplateById('debate');
console.log(template?.config?.selector_prompt);
```

---

## 주의사항

1. **visual_override 우선순위**: JSON의 `visual_override`가 providers.json 기본값보다 우선
2. **selector_prompt**: SelectorGroupChat 패턴은 반드시 `selector_prompt` 필요
3. **파일 네이밍**: `_`로 시작하는 파일은 스킵됨

---

*Last Updated: 2025-01-09*

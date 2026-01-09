# Team Runtime - Pattern Application System

패턴을 팀 설정에 적용하는 런타임 시스템입니다.

---

## FOR AI ASSISTANTS

### 이 폴더의 역할

```
PatternDefinition (UI 선택)
        ↓
team-factory.ts (applyPatternToExistingTeam)
        ↓
effectiveTeamConfig (selector_prompt 포함!)
        ↓
chat.tsx → WebSocket → Backend
```

### 다음에 읽어야 할 파일들

```
이 폴더 내 (핵심 순서):
1. team-factory.ts - applyPatternToExistingTeam() ← 핵심!
2. pattern-runtime.ts - applyPatternComplete()
3. selector-config.ts - SelectorGroupChat 설정

상위/관련:
4. ../agentflow/patterns/pattern-loader.ts - 패턴 로딩
5. ../chat.tsx - WebSocket 전송
6. AG_Cohub/patterns/README.md - 패턴 정의
```

### 핵심 함수: applyPatternToExistingTeam (team-factory.ts)

```typescript
// line 225-238
if (pattern.autogenProvider === "SelectorGroupChat") {
  // 팀 레벨 model_client 추가
  config.model_client = { ... };

  // selector_prompt 추가 ← 이게 핵심!
  if (!config.selector_prompt) {
    config.selector_prompt = pattern.prompts?.selector || "";
  }
}
```

---

## 파일 구조

```
team-runtime/
├── index.ts           ← export 진입점
├── team-factory.ts    ← 핵심: createOrModifyTeam, applyPatternToExistingTeam
├── pattern-runtime.ts ← applyPatternComplete
├── selector-config.ts ← SelectorGroupChat 설정 유틸
├── swarm-config.ts    ← Swarm 설정 유틸
├── roundrobin-config.ts ← RoundRobin 설정 유틸
└── README.md          ← 이 파일
```

---

## 핵심 함수들

### 1. applyPatternComplete (pattern-runtime.ts)

```typescript
export const applyPatternComplete = (
  teamConfig: Component<TeamConfig> | null,
  patternId: string,
): TeamFactoryResult => {
  return createOrModifyTeam(teamConfig, patternId);
};
```

### 2. createOrModifyTeam (team-factory.ts)

```typescript
export const createOrModifyTeam = (
  existingTeam: Component<TeamConfig> | null,
  patternId: string,
): TeamFactoryResult => {
  if (!existingTeam) {
    return createNewTeamFromPattern(patternId);
  }
  return applyPatternToExistingTeam(existingTeam, patternId);
};
```

### 3. applyPatternToExistingTeam (team-factory.ts)

**가장 중요한 함수!** 기존 팀에 패턴 적용:

```typescript
export const applyPatternToExistingTeam = (
  existingTeam: Component<TeamConfig>,
  patternId: string,
): TeamFactoryResult => {
  const pattern = getPatternById(patternId);
  const teamConfig = JSON.parse(JSON.stringify(existingTeam));

  // Provider 변경
  teamConfig.provider = pattern.autogenProviderFull;

  // SelectorGroupChat이면 추가 설정
  if (pattern.autogenProvider === "SelectorGroupChat") {
    config.model_client = { ... };
    config.selector_prompt = pattern.prompts?.selector || "";
  }

  return { teamConfig, pattern };
};
```

---

## 데이터 흐름

```
1. 사용자가 패턴 선택 (UI)
        ↓
2. chat.tsx의 effectiveTeamConfig useMemo
        ↓
3. applyPatternComplete(teamConfig, selectedPatternId)
        ↓
4. createOrModifyTeam → applyPatternToExistingTeam
        ↓
5. selector_prompt 등 추가
        ↓
6. effectiveTeamConfig 반환
        ↓
7. WebSocket으로 백엔드 전송 (chat.tsx:589)
```

---

## Provider별 설정

### SelectorGroupChat

```typescript
// team-factory.ts:225-238
if (pattern.autogenProvider === "SelectorGroupChat") {
  config.model_client = modelClient;  // 팀 레벨 필수!
  config.selector_prompt = pattern.prompts?.selector;
  config.allow_repeated_speaker = true;
}
```

### Swarm

```typescript
// swarm-config.ts
// handoffs는 에이전트 레벨에서 설정됨
config.participants.forEach(p => {
  if (pattern needs handoffs) {
    p.config.handoffs = [...];
  }
});
```

### RoundRobinGroupChat

```typescript
// 특별한 설정 불필요
// 고정 순서로 실행됨
```

---

## 디버깅

### selector_prompt 확인

```typescript
// chat.tsx에서
const effectiveTeamConfig = React.useMemo(() => {
  const result = applyPatternComplete(teamConfig, selectedPatternId);
  console.log('selector_prompt:', result.teamConfig?.config?.selector_prompt);
  return result.teamConfig;
}, [teamConfig, selectedPatternId]);
```

### WebSocket 메시지 확인

```typescript
// chat.tsx:589
console.log('Sending to backend:', {
  type: "start",
  team_config: effectiveTeamConfig
});
```

---

*Last Updated: 2025-01-09*

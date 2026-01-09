# Frontend Pattern Data

AG_Cohub/patterns/*.json의 복사본입니다.
**이 폴더의 JSON 파일을 직접 수정하지 마세요!**

---

## FOR AI ASSISTANTS

### 소스 오브 트루스

```
AG_Cohub/patterns/*.json ← 여기가 원본!
        ↓ 복사
이 폴더 (data/*.json)
```

### 수정 시

1. `AG_Cohub/patterns/` 폴더의 JSON 수정
2. 이 폴더에 복사
3. `pattern-loader.ts`에 import 추가 (새 파일인 경우)
4. Frontend 빌드

### 다음에 읽어야 할 파일들

```
1. ../pattern-loader.ts - JSON을 import하고 변환
2. ../pattern-schema.ts - PATTERN_LIBRARY export
3. ../../team-runtime/team-factory.ts - 팀 설정 적용
4. AG_Cohub/patterns/README.md - 패턴 정의 상세
```

---

## 파일 목록

| 파일 | 원본 |
|------|------|
| `01_sequential.json` | AG_Cohub/patterns/01_sequential.json |
| `02_concurrent.json` | AG_Cohub/patterns/02_concurrent.json |
| `03_selector.json` | AG_Cohub/patterns/03_selector.json |
| `04_group_chat.json` | AG_Cohub/patterns/04_group_chat.json |
| `05_handoff.json` | AG_Cohub/patterns/05_handoff.json |
| `06_magentic.json` | AG_Cohub/patterns/06_magentic.json |
| `07_debate.json` | AG_Cohub/patterns/07_debate.json |
| `08_reflection.json` | AG_Cohub/patterns/08_reflection.json |
| `09_hierarchical.json` | AG_Cohub/patterns/09_hierarchical.json |
| `providers.json` | Provider 기본 설정 (색상, 아이콘) |

---

## providers.json

패턴별 기본 시각화 설정:

```json
{
  "RoundRobinGroupChat": {
    "full": "autogen_agentchat.teams.RoundRobinGroupChat",
    "category": "sequential",
    "layout": "chain",
    "icon": "ArrowRight",
    "colors": { "primary": "#3b82f6", "secondary": "#93c5fd" }
  },
  "SelectorGroupChat": {
    "category": "dynamic",
    "layout": "hub-spoke",
    "requiresModelClient": true
  }
}
```

---

## 핵심: selector_prompt

`07_debate.json`:

```json
{
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "team_config": {
      "selector_prompt": "토론 규칙: advocate와 critic이 번갈아..."
    }
  }
}
```

이 `selector_prompt`가 LLM에게 다음 화자를 알려줍니다!

---

*이 폴더는 AG_Cohub/patterns/의 복사본입니다. 수정은 원본에서 하세요.*

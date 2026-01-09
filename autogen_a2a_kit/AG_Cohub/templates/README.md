# AG_Cohub/templates - Team Configuration Templates

실행 가능한 TeamConfig 템플릿 파일들입니다.

---

## FOR AI ASSISTANTS

### 이 폴더의 역할

```
patterns/*.json (패턴 정의)
        ↓
templates/*.json (실행 가능한 팀 설정)
        ↓
AutoGen에서 직접 사용 가능
```

### 다음에 읽어야 할 파일들

```
이 폴더 내:
1. debate_team.json - SelectorGroupChat 팀 템플릿
2. handoff_team.json - Swarm 팀 템플릿

상위 폴더:
3. AG_Cohub/patterns/README.md - 패턴 정의 이해
4. AG_Cohub/loader/README.md - 템플릿이 어떻게 생성되는지
```

### patterns vs templates 차이

```
patterns/*.json:
  - 패턴의 "정의" (메타데이터, 설명, 다이어그램)
  - UI에서 패턴 선택/표시용
  - autogen_implementation.team_config에 기본 에이전트 포함

templates/*.json:
  - 실제 "실행 가능한" 팀 설정
  - AutoGen에서 직접 로드 가능
  - Component<TeamConfig> 형식
```

---

## 파일 목록

| 파일 | Provider | 설명 |
|------|----------|------|
| `sequential_team.json` | RoundRobinGroupChat | 순차 실행 팀 |
| `selector_team.json` | SelectorGroupChat | LLM 선택 팀 |
| `debate_team.json` | SelectorGroupChat | 토론 팀 |
| `handoff_team.json` | Swarm | 핸드오프 팀 |
| `reflection_team.json` | RoundRobinGroupChat | 반성 패턴 팀 |

---

## 템플릿 구조

### 기본 구조

```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "component_type": "team",
  "version": 1,
  "description": "팀 설명",
  "label": "Team Name (Template)",
  "config": {
    "participants": [...],
    "selector_prompt": "...",  // SelectorGroupChat만
    "model_client": {...},     // 선택적
    "termination_condition": {...}  // 선택적
  }
}
```

### SelectorGroupChat 템플릿 예시

```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "component_type": "team",
  "config": {
    "participants": [
      {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent",
        "config": {
          "name": "advocate",
          "description": "지지자",
          "system_message": "당신은 제안의 지지자입니다...",
          "model_client": {
            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
            "component_type": "model",
            "config": { "model": "gpt-4o-mini" }
          }
        }
      }
    ],
    "selector_prompt": "토론 규칙에 따라 다음 발언자 선택...",
    "model_client": {
      "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
      "component_type": "model",
      "config": { "model": "gpt-4o-mini" }
    }
  }
}
```

### Swarm 템플릿 예시

```json
{
  "provider": "autogen_agentchat.teams.Swarm",
  "component_type": "team",
  "config": {
    "participants": [
      {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent",
        "config": {
          "name": "triage",
          "description": "분류 에이전트",
          "system_message": "사용자 요청을 분류하세요...",
          "handoffs": ["sales", "support"],  // 핸드오프 대상!
          "model_client": {...}
        }
      },
      {
        "config": {
          "name": "sales",
          "handoffs": ["triage"]  // 다시 triage로 돌아갈 수 있음
        }
      }
    ]
  }
}
```

---

## 사용 방법

### 1. Python에서 직접 로드

```python
import json

with open('templates/debate_team.json') as f:
    team_config = json.load(f)

# AutoGen에서 사용
from autogen_agentchat.teams import SelectorGroupChat
team = SelectorGroupChat.from_config(team_config)
```

### 2. cohub_loader.py로 완전한 템플릿 생성

```bash
python cohub_loader.py
# patterns/*.json에서 templates/*.json 생성
```

### 3. AutoGen Studio Gallery에 Import

```bash
# Gallery JSON 생성
python cohub_gallery_builder.py

# AutoGen Studio UI에서 Import
```

---

## 주의사항

### 1. model_client 필요

대부분의 에이전트에 `model_client` 설정 필요:

```json
"model_client": {
  "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
  "component_type": "model",
  "config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7
  }
}
```

### 2. SelectorGroupChat은 팀 레벨 model_client 필요

```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "config": {
    "participants": [...],
    "model_client": {...},  // 팀 레벨 (화자 선택용)
    "selector_prompt": "..."
  }
}
```

### 3. Swarm은 handoffs 배열 필요

```json
{
  "config": {
    "name": "triage",
    "handoffs": ["sales", "support"]
  }
}
```

---

## 템플릿 vs 런타임 생성

| 방식 | 장점 | 단점 |
|------|------|------|
| 템플릿 사용 | 빠름, 미리 정의됨 | 유연성 낮음 |
| 런타임 생성 | 동적, 유연함 | 코드 필요 |

Frontend에서는 `pattern-loader.ts`의 `buildTeamTemplate()`로 런타임에 생성합니다.

---

## 관련 파일

- `AG_Cohub/cohub_loader.py` - 템플릿 생성 스크립트
- `AG_Cohub/cohub_gallery_builder.py` - Gallery JSON 생성
- `AG_Cohub/loader/converter.ts` - TypeScript에서 템플릿 생성

---

*Last Updated: 2025-01-09*

# AutoGen + A2A Developer Kit

Microsoft AutoGen + Google A2A 통합 개발 키트
**AutoGen 소스 수정 가능** (editable mode)

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd autogen_a2a_kit

# 2. Setup (Windows)
setup.bat

# 2. Setup (Linux/Mac)
chmod +x setup.sh && ./setup.sh

# 3. Set API Key
set OPENAI_API_KEY=sk-...   # Windows
export OPENAI_API_KEY=sk-... # Linux

# 4. Run
python example.py
```

## 구조

```
autogen_a2a_kit/
├── a2a_client.py         # A2A 클라이언트
├── agents.py             # AutoGen 래퍼
├── example.py            # 사용 예제
├── a2a_demo/             # A2A 서버 예제
├── setup.bat             # Windows 설치 (AutoGen 소스 포함)
├── setup.sh              # Linux/Mac 설치
└── requirements.txt      # 의존성

setup 후 생성:
├── venv/                 # 가상환경
└── autogen_source/       # AutoGen 소스 (수정 가능!)
```

## 사용법

```python
from a2a_client import create_a2a_tool, call_a2a
from agents import run_task, multi_agent_task
import asyncio

# A2A 도구 생성
tool = create_a2a_tool("http://localhost:8001/")

# 단일 에이전트
result = asyncio.run(run_task("Check if 97 is prime", tools=[tool]))

# 멀티 에이전트
agents = [
    {"name": "coordinator", "system_message": "Coordinate..."},
    {"name": "expert", "tools": [tool], "system_message": "Use tools..."}
]
result = asyncio.run(multi_agent_task("Your task", agents))
```

## 주요 함수

| 함수 | 설명 |
|------|------|
| `call_a2a(query, url)` | A2A 서버 직접 호출 |
| `create_a2a_tool(url)` | AutoGen용 A2A 도구 |
| `check_server(url)` | 서버 상태 확인 |
| `run_task(task, tools)` | 단일 에이전트 실행 |
| `multi_agent_task(task, agents)` | 멀티 에이전트 실행 |

## A2A 서버 실행

```bash
# 터미널 1: A2A 서버
python a2a_demo/remote_agent/agent.py

# 터미널 2: 테스트
python example.py
```

## AutoGen 소스 수정

setup 후 `autogen_source/` 폴더가 생성됩니다:
```
autogen_source/python/packages/
├── autogen-core/         # 코어
├── autogen-agentchat/    # 에이전트
└── autogen-ext/          # 확장
```

**editable mode**로 설치되어 소스 수정 → 즉시 반영

## AutoGen Studio + A2A 다중 에이전트 협업

AutoGen Studio UI에서 A2A 서버와 연동하여 다중 에이전트 협업을 구현할 수 있습니다.

### 1. 서버 실행

```bash
# 터미널 1: A2A Prime Checker 서버 (포트 8002)
python a2a_demo/remote_agent/agent.py

# 터미널 2: AutoGen Studio (포트 8081)
autogenstudio ui --port 8081
```

### 2. Agent Card로 에이전트 정보 확인

```bash
# A2A 서버의 Agent Card 확인
curl http://localhost:8002/.well-known/agent.json
```

응답 예시:
```json
{
  "name": "prime_checker_agent",
  "description": "소수를 판별하고 소인수분해를 수행하는 수학 전문 에이전트",
  "skills": [
    {"name": "is_prime", "description": "숫자가 소수인지 확인"},
    {"name": "get_prime_factors", "description": "소인수분해 수행"}
  ]
}
```

### 3. AutoGen Studio에서 A2A 도구 추가

**Tools → Create** 에서 FunctionTool 생성:

```python
def call_a2a_prime_checker(query: str) -> str:
    """A2A 프로토콜로 소수 판별 에이전트 호출"""
    import requests, json, uuid

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": query}]
            }
        }
    }

    response = requests.post(
        "http://localhost:8002/",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )

    result = response.json()
    if "result" in result and "artifacts" in result["result"]:
        for artifact in result["result"]["artifacts"]:
            for part in artifact.get("parts", []):
                if "text" in part:
                    return part["text"]
    return str(result)
```

> ⚠️ **중요**: FunctionTool 설정에 반드시 `has_cancellation_support: false` 추가!

### 4. 다중 에이전트 팀 구성

**Teams → Create → SelectorGroupChat** 에서:

1. **math_agent**: A2A 도구 사용, 수학 계산 담당
2. **critic_agent**: 응답 검토 및 피드백 제공

→ 상세 가이드: [docs/A2A_AGENT_GUIDE.md](docs/A2A_AGENT_GUIDE.md)

## 필요사항

- Python 3.10+
- Git
- OpenAI API Key

## 상세 문서

- [AI_HANDOFF.md](AI_HANDOFF.md) - 프로젝트 핸드오프 문서
- [docs/A2A_AGENT_GUIDE.md](docs/A2A_AGENT_GUIDE.md) - A2A 에이전트 추가 가이드

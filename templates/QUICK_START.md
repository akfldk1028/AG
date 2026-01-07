# A2A Multi-Agent Integration - Quick Start Guide

## 1. 필요 패키지 설치

```bash
pip install autogen-agentchat autogen-ext[openai] requests google-adk
```

## 2. 프로젝트 구조

```
my_project/
├── agents/
│   └── remote_agent.py     # Google ADK A2A 서버
├── tools/
│   └── a2a_client.py       # A2A 클라이언트 도구
├── main.py                 # AutoGen 멀티에이전트
└── config.py               # 설정
```

## 3. A2A 서버 시작 (Google ADK)

```python
# agents/remote_agent.py
from google.adk.agents import Agent

agent = Agent(
    model="gemini-2.0-flash",
    name="my_agent",
    instruction="Your agent instructions"
)

# 실행: adk api_server agents.remote_agent:agent --port 8001
```

## 4. A2A 클라이언트 도구

```python
# tools/a2a_client.py
import requests, uuid

def call_a2a_agent(query: str, url: str = "http://localhost:8001/") -> str:
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": str(uuid.uuid4()),
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": query}]
            }
        }
    }

    response = requests.post(url, json=payload, timeout=30)
    result = response.json()

    for artifact in result.get("result", {}).get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part.get("text")
    return str(result)
```

## 5. AutoGen 멀티에이전트

```python
# main.py
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tools.a2a_client import call_a2a_agent

model = OpenAIChatCompletionClient(model="gpt-4o-mini")

agent_with_a2a = AssistantAgent(
    name="A2A_Agent",
    model_client=model,
    tools=[call_a2a_agent],
    system_message="Use call_a2a_agent for external agent communication."
)

team = SelectorGroupChat(participants=[agent_with_a2a], model_client=model)
result = await team.run(task="Your task")
```

## 6. 실행

```bash
# Terminal 1: A2A 서버 시작
adk api_server agents.remote_agent:agent --port 8001

# Terminal 2: AutoGen 실행
python main.py
```

## 7. A2A 서버 상태 확인

```bash
curl http://localhost:8001/.well-known/agent.json
```

## 핵심 포인트

| Component | Role |
|-----------|------|
| Google ADK | A2A 서버 (원격 에이전트) |
| AutoGen | 멀티에이전트 오케스트레이션 |
| A2A Protocol | JSONRPC 기반 에이전트 통신 |
| FunctionTool | AutoGen에서 A2A 호출 |

## 문제 해결

1. **연결 실패**: A2A 서버가 실행 중인지 확인
2. **한글 깨짐**: Windows에서 `chcp 65001` 실행
3. **도구 호출 안됨**: system_message에 도구 사용 지시 추가

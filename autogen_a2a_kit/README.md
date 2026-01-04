# AutoGen + A2A Integration Kit

어떤 프로젝트에든 복사해서 바로 사용 가능한 패키지

## 설치 (1줄)

```bash
pip install autogen-agentchat autogen-ext[openai] requests
```

## 사용법

### 1. 폴더 복사
```
your_project/
├── autogen_a2a_kit/    ← 이 폴더 복사
│   ├── __init__.py
│   ├── a2a_client.py
│   ├── agents.py
│   └── example.py
└── your_code.py
```

### 2. 환경변수 설정
```bash
# Windows
set OPENAI_API_KEY=your-key

# Linux/Mac
export OPENAI_API_KEY=your-key
```

### 3. 코드에서 사용

```python
from autogen_a2a_kit import create_a2a_tool, run_task

# A2A 도구 생성
tool = create_a2a_tool("http://localhost:8001/")

# 작업 실행
import asyncio
result = asyncio.run(run_task("Check if 97 is prime", tools=[tool]))
print(result)
```

## 주요 함수

| 함수 | 설명 |
|------|------|
| `call_a2a(query, url)` | A2A 서버 직접 호출 |
| `create_a2a_tool(url)` | AutoGen용 A2A 도구 생성 |
| `check_server(url)` | 서버 상태 확인 |
| `quick_agent(name, tools)` | 에이전트 빠른 생성 |
| `run_task(task, tools)` | 단일 에이전트 실행 |
| `multi_agent_task(task, agents_config)` | 멀티 에이전트 실행 |

## 예제

```python
# 멀티 에이전트
from autogen_a2a_kit import create_a2a_tool, multi_agent_task

agents = [
    {"name": "coordinator", "system_message": "Coordinate tasks..."},
    {"name": "expert", "tools": [create_a2a_tool()], "system_message": "Use tools..."}
]

result = asyncio.run(multi_agent_task("Your task", agents))
```

## 필요한 것

- Python 3.10+
- OpenAI API Key
- (선택) A2A 서버 (localhost:8001)

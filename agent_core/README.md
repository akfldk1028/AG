# Agent Core

재사용 가능한 에이전트 코어 라이브러리

## 설치

```bash
# Editable 모드로 설치 (코드 수정 즉시 반영)
pip install -e D:\Data\22_AG\agent_core
```

## 사용법

### 1. 설정 파일 (config.yaml)

```yaml
name: my_agent
model: openai/gpt-4o-mini
description: 나의 에이전트
instruction: 친절하게 답변해주세요.
port: 8001
host: 127.0.0.1
```

### 2. 도구 정의 (tools.py)

```python
def my_tool(param: str) -> dict:
    """도구 설명"""
    return {"result": param}
```

### 3. 메인 코드 (main.py)

```python
from agent_core import create_agent, run_a2a_server
from tools import my_tool

agent = create_agent("config.yaml", tools=[my_tool])
run_a2a_server(agent)
```

## 수정하기

`pip install -e`로 설치했으므로 `D:\Data\22_AG\agent_core\src\agent_core\` 폴더의 코드를 직접 수정하면 즉시 반영됩니다!

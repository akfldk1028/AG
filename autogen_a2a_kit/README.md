# AutoGen + A2A Integration Kit

Microsoft AutoGen과 Google A2A(Agent-to-Agent) 프로토콜을 연동한 멀티 에이전트 개발 환경.

---

## 🚀 Quick Start (AI/CLI 실행용)

> **AI Agent나 CLI에서 순서대로 실행하세요. setup.bat 없이 수동 설치합니다.**

### Prerequisites
- Python 3.10+
- OpenAI API Key

### Step 1: Clone Repository
```bash
git clone https://github.com/akfldk1028/AG.git
cd AG/autogen_a2a_kit
```

### Step 2: Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade pip
```bash
pip install --upgrade pip
```

### Step 4: Install AutoGen packages (editable mode)
```bash
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"
pip install -e autogen_source/python/packages/autogen-studio
```

### Step 5: Install A2A dependencies
```bash
pip install google-adk httpx python-dotenv
```

### Step 6: Set API Key

**Windows:**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

### Step 7: Verify Installation
```bash
python -c "from autogen_agentchat.agents import AssistantAgent; print('OK: autogen-agentchat')"
python -c "from autogenstudio.a2a import A2AAgent; print('OK: A2AAgent')"
```

### Step 8: Run A2A Demo Server (Terminal 1)
```bash
python a2a_demo/remote_agent/agent.py
```

### Step 9: Run AutoGen Studio (Terminal 2)
```bash
autogenstudio ui --port 8081
```

### Step 10: Open Browser
```
http://localhost:8081
```

---

## 주요 기능

- AutoGen 소스를 editable mode로 설치하여 수정 즉시 반영
- A2A 프로토콜 서버 예제 포함 (소수 판별, 계산기)
- AutoGen Studio UI에서 A2A 에이전트 사용 가능
- 원클릭 설치 스크립트

## 요구사항

- Python 3.10 이상
- OpenAI API Key

## 설치

> **권장: 위의 [Quick Start](#-quick-start-aicli-실행용) 섹션을 따라하세요.**

### 자동 설치 (setup 스크립트)

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

setup 스크립트는 다음을 수행합니다:
1. Python 가상환경 생성 (venv/)
2. autogen-core, autogen-agentchat, autogen-ext, autogen-studio를 editable mode로 설치
3. A2A 관련 의존성 설치

> **Note**: `autogen_source/` 폴더는 이미 A2A 수정본이 포함되어 있습니다. Microsoft repo에서 별도로 클론하지 않습니다.

## 환경 변수 설정

```cmd
# Windows
set OPENAI_API_KEY=sk-your-api-key-here

# Linux / Mac
export OPENAI_API_KEY=sk-your-api-key-here
```

## 디렉토리 구조

```
autogen_a2a_kit/
├── a2a_demo/                      # A2A 서버 예제
│   ├── remote_agent/
│   │   └── agent.py               # 소수 판별 에이전트 (port 8002)
│   ├── calculator_agent/
│   │   └── agent.py               # 계산기 에이전트 (port 8003)
│   └── root_agent/
│       └── agent.py               # 코디네이터 에이전트
├── autogen_source/                # AutoGen 소스 (editable mode)
│   └── python/packages/
│       ├── autogen-core/          # 코어 라이브러리
│       ├── autogen-agentchat/     # 에이전트 채팅
│       ├── autogen-ext/           # 확장 (OpenAI 등)
│       └── autogen-studio/        # Studio UI + A2A 통합
│           └── autogenstudio/
│               └── a2a/           # A2AAgent 클래스
├── setup.bat                      # Windows 설치 스크립트
├── setup.sh                       # Linux/Mac 설치 스크립트
├── requirements.txt               # Python 의존성
├── AI_HANDOFF.md                  # AI 전달 문서
└── README.md                      # 이 문서
```

## 실행 방법

### 1. A2A 서버 실행

터미널 2개를 열고 각각 실행:

```cmd
# 터미널 1: 소수 판별 에이전트 (port 8002)
cd autogen_a2a_kit
venv\Scripts\activate
python a2a_demo/remote_agent/agent.py
```

```cmd
# 터미널 2: 계산기 에이전트 (port 8003)
cd autogen_a2a_kit
venv\Scripts\activate
python a2a_demo/calculator_agent/agent.py
```

Linux/Mac의 경우:

```bash
# 터미널 1
cd autogen_a2a_kit
source venv/bin/activate
python a2a_demo/remote_agent/agent.py
```

```bash
# 터미널 2
cd autogen_a2a_kit
source venv/bin/activate
python a2a_demo/calculator_agent/agent.py
```

### 2. AutoGen Studio 실행

```cmd
# Windows
cd autogen_a2a_kit
venv\Scripts\activate
autogenstudio ui --port 8081
```

```bash
# Linux/Mac
cd autogen_a2a_kit
source venv/bin/activate
autogenstudio ui --port 8081
```

브라우저에서 http://localhost:8081 접속

### 3. A2A 서버 직접 테스트

```cmd
# 소수 판별 테스트
curl -X POST http://localhost:8002 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"message/send\",\"id\":\"1\",\"params\":{\"message\":{\"messageId\":\"1\",\"role\":\"user\",\"parts\":[{\"kind\":\"text\",\"text\":\"Is 17 a prime number?\"}]}}}"
```

```cmd
# 계산기 테스트
curl -X POST http://localhost:8003 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"message/send\",\"id\":\"1\",\"params\":{\"message\":{\"messageId\":\"1\",\"role\":\"user\",\"parts\":[{\"kind\":\"text\",\"text\":\"Calculate fibonacci(10)\"}]}}}"
```

## 포트 구성

| Port | Service | 설명 |
|------|---------|------|
| 8002 | prime_checker_agent | A2A 소수 판별 서버 |
| 8003 | calculator_agent | A2A 계산기 서버 |
| 8081 | AutoGen Studio | 웹 UI |

## AutoGen Studio에서 A2A 에이전트 사용

### A2AAgent 설정 형식

AutoGen Studio 팀 구성에서 A2A 에이전트를 추가할 때 사용하는 JSON 형식:

```json
{
    "provider": "autogenstudio.a2a.A2AAgent",
    "component_type": "agent",
    "version": 1,
    "label": "Calculator Agent",
    "config": {
        "name": "calculator_agent",
        "a2a_server_url": "http://localhost:8003",
        "description": "Math calculator specialist",
        "timeout": 60,
        "skills": []
    }
}
```

### SelectorGroupChat 팀 구성 예시

여러 A2A 에이전트를 포함한 팀:

```json
{
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team",
    "label": "Dual A2A Team",
    "config": {
        "participants": [
            {
                "provider": "autogen_agentchat.agents.AssistantAgent",
                "config": {
                    "name": "assistant_agent",
                    "model_client": {
                        "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                        "config": {"model": "gpt-4o-mini"}
                    },
                    "system_message": "General assistant. Delegate prime questions to prime_checker_agent, math to calculator_agent. Say TERMINATE when done."
                }
            },
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "prime_checker_agent",
                    "a2a_server_url": "http://localhost:8002",
                    "description": "Prime number specialist"
                }
            },
            {
                "provider": "autogenstudio.a2a.A2AAgent",
                "config": {
                    "name": "calculator_agent",
                    "a2a_server_url": "http://localhost:8003",
                    "description": "Math calculator specialist"
                }
            }
        ],
        "model_client": {
            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
            "config": {"model": "gpt-4o-mini"}
        },
        "selector_prompt": "Select agent:\n- prime_checker_agent: prime numbers, factorization\n- calculator_agent: calculations, fibonacci, factorial\n- assistant_agent: general\n\nConversation: {history}\nRoles: {roles}\nReturn ONLY agent name.",
        "termination_condition": {
            "provider": "autogen_agentchat.conditions.MaxMessageTermination",
            "config": {"max_messages": 10}
        }
    }
}
```

### API로 팀 생성하기

```python
import requests
import json

team_config = {
    "user_id": "guestuser@gmail.com",
    "team": {
        "provider": "autogen_agentchat.teams.SelectorGroupChat",
        "component_type": "team",
        "version": 1,
        "label": "Dual A2A Team",
        "config": {
            "participants": [
                {
                    "provider": "autogen_agentchat.agents.AssistantAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "assistant_agent",
                        "model_client": {
                            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                            "component_type": "model",
                            "version": 1,
                            "config": {"model": "gpt-4o-mini"}
                        },
                        "system_message": "General assistant. Say TERMINATE when done."
                    }
                },
                {
                    "provider": "autogenstudio.a2a.A2AAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "prime_checker_agent",
                        "a2a_server_url": "http://localhost:8002",
                        "description": "Prime number specialist",
                        "timeout": 60,
                        "skills": []
                    }
                },
                {
                    "provider": "autogenstudio.a2a.A2AAgent",
                    "component_type": "agent",
                    "version": 1,
                    "config": {
                        "name": "calculator_agent",
                        "a2a_server_url": "http://localhost:8003",
                        "description": "Math calculator specialist",
                        "timeout": 60,
                        "skills": []
                    }
                }
            ],
            "model_client": {
                "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
                "component_type": "model",
                "version": 1,
                "config": {"model": "gpt-4o-mini"}
            },
            "termination_condition": {
                "provider": "autogen_agentchat.conditions.MaxMessageTermination",
                "component_type": "termination",
                "version": 1,
                "config": {"max_messages": 10}
            },
            "selector_prompt": "Select agent based on query type. Return ONLY agent name."
        }
    }
}

response = requests.post(
    "http://127.0.0.1:8081/api/teams/",
    json=team_config
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

## A2A 프로토콜 상세

### 요청 형식

```json
{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "unique-request-id",
    "params": {
        "message": {
            "messageId": "unique-message-id",
            "role": "user",
            "parts": [{"kind": "text", "text": "질문 내용"}]
        }
    }
}
```

### 응답 형식

```json
{
    "jsonrpc": "2.0",
    "id": "unique-request-id",
    "result": {
        "artifacts": [{
            "parts": [{"kind": "text", "text": "응답 내용"}]
        }]
    }
}
```

### Agent Card 확인

```bash
curl http://localhost:8002/.well-known/agent.json
```

응답:

```json
{
    "name": "prime_checker_agent",
    "description": "소수를 판별하고 소인수분해를 수행하는 에이전트",
    "skills": [
        {"name": "is_prime", "description": "숫자가 소수인지 확인"},
        {"name": "get_prime_factors", "description": "소인수분해 수행"}
    ]
}
```

## AutoGen 소스 수정

editable mode로 설치되어 있어 소스 수정 시 즉시 반영됩니다.

```
autogen_source/python/packages/
├── autogen-core/src/autogen_core/          # 코어 기능
├── autogen-agentchat/src/autogen_agentchat/  # 에이전트 채팅
├── autogen-ext/src/autogen_ext/            # 확장 모듈
└── autogen-studio/autogenstudio/           # Studio UI
    └── a2a/                                # A2A 통합
        ├── __init__.py
        ├── agent.py                        # A2AAgent 클래스
        └── registry.py                     # A2ARegistry
```

수정 후 재설치 불필요. 파일 저장만 하면 됩니다.

## 새로운 A2A 에이전트 추가하기

### 1. 에이전트 서버 생성

`a2a_demo/your_agent/agent.py` 파일 생성:

```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.servers import A2AServer

def your_function(query: str) -> str:
    """함수 설명"""
    # 로직 구현
    return result

agent = Agent(
    name="your_agent",
    model="gpt-4o-mini",
    description="Your agent description",
    instruction="Your agent instructions",
    tools=[your_function]
)

runner = Runner(agent=agent, app_name="your_agent")
server = A2AServer(runner=runner, host="0.0.0.0", port=8004)

if __name__ == "__main__":
    server.start()
```

### 2. 서버 실행

```bash
python a2a_demo/your_agent/agent.py
```

### 3. AutoGen Studio에 등록

AutoGen Studio UI에서 팀 생성 시 A2AAgent로 추가:

```json
{
    "provider": "autogenstudio.a2a.A2AAgent",
    "component_type": "agent",
    "version": 1,
    "config": {
        "name": "your_agent",
        "a2a_server_url": "http://localhost:8004",
        "description": "Your agent description",
        "timeout": 60,
        "skills": []
    }
}
```

## 프론트엔드 개발 (UI 수정 시)

프론트엔드 UI를 수정하고 싶다면 아래 절차를 따르세요.

### 1. 프론트엔드 소스 위치

```
autogen_source/python/packages/autogen-studio/frontend/
├── src/
│   ├── components/   # React 컴포넌트
│   ├── pages/        # 페이지 라우트
│   └── ...
├── package.json
└── gatsby-config.ts
```

### 2. 개발 모드 실행

```bash
cd autogen_source/python/packages/autogen-studio/frontend
npm install --legacy-peer-deps
npm run develop
```

브라우저에서 `http://localhost:8000` 접속 (Gatsby 개발 서버)

### 3. 수정 후 빌드 및 적용

**Windows:**
```cmd
.\node_modules\.bin\gatsby.cmd clean && .\node_modules\.bin\gatsby.cmd build --prefix-paths
xcopy /E /I /Y public ..\autogenstudio\web\ui
```

**Linux/Mac:**
```bash
npm run build
cp -r public/* ../autogenstudio/web/ui/
```

### 4. AutoGen Studio 재시작

```bash
autogenstudio ui --port 8081
```

> **Note:** `autogenstudio/web/ui/` 폴더는 이미 빌드된 파일이 포함되어 있습니다. 프론트엔드를 수정하지 않는 사용자는 빌드 없이 바로 사용 가능합니다.

---

## 문제 해결

### Windows 한글 깨짐

```cmd
chcp 65001
```

### A2A 서버 연결 실패

1. 서버가 실행 중인지 확인:
```cmd
curl http://localhost:8002/.well-known/agent.json
```

2. 포트가 사용 중인지 확인:
```cmd
netstat -ano | findstr :8002
```

3. 프로세스 종료 (필요시):
```cmd
taskkill /PID <프로세스ID> /F
```

### API 키 오류

환경 변수가 설정되어 있는지 확인:

```cmd
# Windows
echo %OPENAI_API_KEY%

# Linux/Mac
echo $OPENAI_API_KEY
```

### AutoGen Studio 팀 업데이트 불가 (PUT 405 오류)

AutoGen Studio의 PUT API가 405를 반환하는 경우 SQLite 직접 수정:

```python
import sqlite3
import os
import json

db_path = os.path.expanduser("~/.autogenstudio/autogen04202.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 팀 조회
cursor.execute("SELECT id, component FROM teams WHERE id = ?", (team_id,))
row = cursor.fetchone()
if row:
    component = json.loads(row[1])
    # component 수정
    component["config"]["participants"].append(new_agent)
    # 저장
    cursor.execute("UPDATE teams SET component = ? WHERE id = ?",
                   (json.dumps(component), team_id))
    conn.commit()

conn.close()
```

### venv 활성화 오류

```cmd
# Windows PowerShell 실행 정책 문제
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 이후 다시 시도
venv\Scripts\activate
```

## 기술 스택

| Component | Technology | Version |
|-----------|------------|---------|
| Multi-Agent Framework | Microsoft AutoGen | 0.7.x |
| A2A Server | Google ADK | 0.2.0+ |
| LLM | OpenAI GPT-4o-mini | - |
| Language | Python | 3.10+ |
| Web UI | AutoGen Studio | 0.4.x |

## 전체 실행 순서 요약

> **상세한 단계별 설치는 맨 위 [Quick Start](#-quick-start-aicli-실행용) 참조**

```bash
# 1. 저장소 클론
git clone https://github.com/akfldk1028/AG.git
cd AG/autogen_a2a_kit

# 2. 가상환경 + 설치
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install --upgrade pip
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"
pip install -e autogen_source/python/packages/autogen-studio
pip install google-adk httpx python-dotenv

# 3. 환경 변수
set OPENAI_API_KEY=sk-your-key  # Windows
# export OPENAI_API_KEY=sk-your-key  # Linux/Mac

# 4. 설치 확인
python -c "from autogenstudio.a2a import A2AAgent; print('OK')"

# 5. A2A 서버 실행 (터미널 1)
python a2a_demo/remote_agent/agent.py

# 6. AutoGen Studio 실행 (터미널 2)
autogenstudio ui --port 8081

# 7. 브라우저 접속
http://localhost:8081
```

## 라이선스

MIT License

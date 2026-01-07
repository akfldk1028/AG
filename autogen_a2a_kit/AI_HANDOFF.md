# AI Handoff Document - AutoGen + A2A Kit

> 이 문서는 AI가 프로젝트를 이해하고 셋업할 수 있도록 작성됨

## 프로젝트 개요

**목적**: Microsoft AutoGen과 Google A2A 프로토콜 연동 + AutoGen 소스 수정 가능한 개발 환경

**특징**:
- AutoGen 소스를 editable mode로 설치 → 수정 즉시 반영
- A2A 서버 예제 포함
- 원클릭 설치

## Quick Start (AI도 이것만 실행)

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

# 4. Test
python example.py
```

## 디렉토리 구조

```
autogen_a2a_kit/              ← 이 폴더가 Git 저장소
├── __init__.py               # 패키지 init
├── a2a_client.py             # A2A 클라이언트 핵심 코드
├── agents.py                 # AutoGen 에이전트 헬퍼
├── example.py                # 사용 예제
├── requirements.txt          # pip 의존성
├── setup.bat                 # Windows 원클릭 설치
├── setup.sh                  # Linux/Mac 원클릭 설치
├── .gitignore                # Git 제외 목록
├── README.md                 # 메인 설명서
├── AI_HANDOFF.md             # 이 문서
└── a2a_demo/                 # A2A 서버 예제
    ├── remote_agent/
    │   └── agent.py          # 소수 판별 A2A 서버 (port 8002)
    ├── calculator_agent/
    │   └── agent.py          # 계산기 A2A 서버 (port 8003)
    ├── root_agent/
    │   └── agent.py          # 코디네이터 에이전트
    └── start_server.bat      # 서버 시작 스크립트

setup.bat 실행 후 생성되는 폴더:
├── venv/                     # Python 가상환경
└── autogen_source/           # Microsoft AutoGen 소스 (editable)
```

## 기술 스택

| Component | Technology | Version |
|-----------|------------|---------|
| Multi-Agent Framework | Microsoft AutoGen | v0.4.2+ |
| A2A Server | Google ADK | v0.2.0+ |
| LLM | OpenAI GPT-4o-mini | - |
| Language | Python | 3.10+ |

## 주요 함수 API

### a2a_client.py
```python
call_a2a(query: str, url: str) -> str
# A2A 서버 직접 호출

create_a2a_tool(url: str, name: str) -> Callable
# AutoGen용 도구 함수 생성

check_server(url: str) -> dict
# 서버 상태 확인 {"available": bool, "name": str}
```

### agents.py
```python
quick_agent(name, tools, system_message, model) -> AssistantAgent
# 에이전트 빠른 생성

run_task(task, tools) -> str
# 단일 에이전트로 작업 실행

multi_agent_task(task, agents_config) -> dict
# 멀티 에이전트 협업 실행
```

## A2A 프로토콜

### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "unique-id",
  "params": {
    "message": {
      "messageId": "unique-id",
      "role": "user",
      "parts": [{"kind": "text", "text": "질문"}]
    }
  }
}
```

### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": {
    "artifacts": [{
      "parts": [{"kind": "text", "text": "응답"}]
    }]
  }
}
```

## AutoGen 소스 수정하기

setup.bat 실행 후:
```
autogen_source/python/packages/
├── autogen-core/         # 코어 라이브러리
├── autogen-agentchat/    # 에이전트 채팅
└── autogen-ext/          # 확장 (OpenAI 등)
```

editable mode로 설치되어 있으므로:
1. 파일 수정
2. 저장
3. 바로 반영됨 (재설치 불필요)

## 포트 사용

| Port | Service |
|------|---------|
| 8002 | prime_checker_agent (A2A 소수 판별) |
| 8003 | calculator_agent (A2A 계산기) |
| 8081 | AutoGen Studio UI |

## 실행 명령어

```bash
# A2A 서버 시작
python a2a_demo/remote_agent/agent.py

# 예제 실행
python example.py

# 대화형 모드
python a2a_demo/root_agent/agent.py --interactive
```

## AutoGen Studio A2A 통합

### A2AAgent 클래스
AutoGen Studio에서 A2A 프로토콜 에이전트 사용:

```python
# Provider: autogenstudio.a2a.A2AAgent
# 경로: autogen_source/python/packages/autogen-studio/autogenstudio/a2a/

# 팀 config 내 A2A 에이전트 정의
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

### SelectorGroupChat 라우팅
```python
# selector_prompt로 질문 유형에 따라 에이전트 선택
selector_prompt = """Select the appropriate agent:
- prime_checker_agent: For prime number checking, factorization
- calculator_agent: For calculations, fibonacci, factorial
- assistant_agent: For general questions

Conversation: {history}
Roles: {roles}
Return ONLY the agent name."""
```

### 팀 업데이트 방법
PUT API는 405 반환 → SQLite 직접 수정 필요:
```python
import sqlite3
db_path = "~/.autogenstudio/autogen04202.db"
conn = sqlite3.connect(db_path)
# component JSON 파싱 후 participants 수정
```

## 알려진 이슈

1. **Windows 한글 깨짐**: `chcp 65001` 실행
2. **A2A 연결 실패**: 서버 실행 상태 확인 필요
3. **API 키 오류**: 환경변수 확인
4. **팀 PUT API 405**: SQLite 직접 수정으로 우회

## 다음 AI에게

1. **Clone 후**: `setup.bat` 또는 `setup.sh` 실행
2. **환경변수**: `OPENAI_API_KEY` 설정
3. **테스트**: `python example.py`
4. **AutoGen 수정**: `autogen_source/python/packages/` 폴더
5. **AutoGen Studio**: `autogenstudio ui --port 8081`로 실행
6. **A2A 서버 시작**:
   - `python a2a_demo/remote_agent/agent.py` (port 8002)
   - `python a2a_demo/calculator_agent/agent.py` (port 8003)
7. **듀얼 에이전트 테스트**: AutoGen Studio UI에서 "Dual A2A Team" 선택

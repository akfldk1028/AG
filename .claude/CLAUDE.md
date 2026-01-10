# AutoGen A2A Kit - Claude Code 지침서

## 1. A2A 에이전트 서버 - 반드시 먼저 실행!

A2A 에이전트를 사용하려면 **반드시** 서버를 먼저 실행해야 합니다.
에러 메시지 `A2A 호출 실패: All connection attempts failed` → A2A 서버 미실행!

### 에이전트 포트 정보
| Agent | Port | 경로 |
|-------|------|------|
| poetry_agent | 8003 | a2a_demo/poetry_agent/agent.py |
| philosophy_agent | 8004 | a2a_demo/philosophy_agent/agent.py |
| history_agent | 8005 | a2a_demo/history_agent/agent.py |
| calculator_agent | 8006 | a2a_demo/calculator_agent/agent.py |

### 서버 시작 명령 (PowerShell)
```powershell
# 각 창에서 실행
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\poetry_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\philosophy_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\history_agent; python agent.py'"
powershell.exe -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\Data\22_AG\autogen_a2a_kit\a2a_demo\calculator_agent; python agent.py'"
```

## 2. Google ADK 모델명 형식

**중요**: Google ADK는 `openai/gpt-4o-mini` 형식을 **지원하지 않음**!

```python
# 틀린 예
model="openai/gpt-4o-mini"  # X - Model not found 에러

# 맞는 예
model="gpt-4o-mini"  # O - 정상 작동
```

## 3. Frontend 빌드 (Windows)

```powershell
cd D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio\frontend

# 1. Clean
npx gatsby clean

# 2. Build
npx gatsby build --prefix-paths

# 3. Copy to web/ui
Copy-Item -Path "public\*" -Destination "..\autogenstudio\web\ui\" -Recurse -Force
```

## 4. 환경변수 (.env)

프로젝트 루트에 `.env` 파일 필요:
```
OPENAI_API_KEY=sk-xxx
```

위치: `D:\Data\22_AG\autogen_a2a_kit\.env`

## 5. Debate 패턴 - allow_repeated_speaker

Multi-agent debate에서 한 에이전트만 계속 선택되는 문제:
- `07_debate.json`의 `requiredConfig.allow_repeated_speaker: false` 설정
- `team-factory.ts`의 selector prompt에서 강하게 rotation 강조

## 6. AutoGen Studio 실행

```bash
cd D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8083
```

## 7. 파일 위치

- 패턴 JSON: `frontend/src/components/views/playground/chat/agentflow/patterns/data/`
- 팀 팩토리: `frontend/src/components/views/playground/chat/team-runtime/team-factory.ts`
- 패턴 로더: `frontend/src/components/views/playground/chat/agentflow/patterns/pattern-loader.ts`
- A2A 에이전트: `a2a_demo/*/agent.py`
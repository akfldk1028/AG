# AG-mcp: PyAutoGUI MCP Server

GUI 자동화를 위한 MCP (Model Context Protocol) 서버.
**API Key 없이** 마우스, 키보드, 스크린샷 제어 가능!

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│              Claude Code / Claude Desktop            │
├─────────────────────────────────────────────────────┤
│                   MCP Protocol                       │
├─────────────────────────────────────────────────────┤
│             PyAutoGUI MCP Server                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Mouse   │  │ Keyboard │  │     Screen       │  │
│  │  Tools   │  │  Tools   │  │     Tools        │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
├───────┴─────────────┴─────────────────┴─────────────┤
│              AG_action/primitives                    │
│        (MouseActions, KeyboardActions, ScreenActions)│
├─────────────────────────────────────────────────────┤
│                    PyAutoGUI                         │
└─────────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │   Desktop (Unity,   │
              │   Flutter, Games)   │
              └─────────────────────┘
```

## 설치

### 1. 가상환경 설정 (최초 1회)

```powershell
cd D:\Data\22_AG\autogen_a2a_kit\AG-mcp
.\setup_venv.bat
```

### 2. Claude Code에 MCP 추가

```bash
claude mcp add pyautogui-mcp "D:\Data\22_AG\autogen_a2a_kit\AG-mcp\start_mcp.bat"
```

또는 설정 파일 직접 수정:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "pyautogui-mcp": {
      "command": "D:\\Data\\22_AG\\autogen_a2a_kit\\AG-mcp\\start_mcp.bat"
    }
  }
}
```

## 사용 가능한 도구 (12개)

### 스크린 도구
| 도구 | 설명 |
|------|------|
| `screenshot` | 스크린샷 촬영 (전체/영역) |
| `screenshot_scaled` | 스케일된 스크린샷 (XGA/WXGA) |
| `get_screen_size` | 화면 크기 조회 |
| `locate_image` | 이미지로 UI 요소 찾기 |
| `get_pixel_color` | 특정 좌표 색상 |

### 마우스 도구
| 도구 | 설명 |
|------|------|
| `mouse_click` | 클릭 (좌/우/중간, 단일/더블/트리플) |
| `mouse_move` | 마우스 이동 |
| `mouse_drag` | 드래그 |
| `mouse_scroll` | 스크롤 |

### 키보드 도구
| 도구 | 설명 |
|------|------|
| `keyboard_type` | 텍스트 입력 |
| `keyboard_key` | 특수키/조합키 (ctrl+c 등) |
| `keyboard_hotkey` | 조합키 |

## 사용 예시

### 스크린샷 촬영
```
"screenshot 도구로 현재 화면 캡처해줘"
```

### 마우스 클릭
```
"(500, 300) 위치에 더블클릭해줘"
→ mouse_click(x=500, y=300, clicks=2)
```

### 이미지로 버튼 찾기
```
"play_button.png 이미지와 같은 버튼을 찾아서 클릭해줘"
→ locate_image("play_button.png") → mouse_click(center.x, center.y)
```

### 키보드 입력
```
"Hello World 입력하고 Enter 눌러줘"
→ keyboard_type("Hello World")
→ keyboard_key("Return")
```

### 단축키 실행
```
"Ctrl+S 눌러서 저장해줘"
→ keyboard_hotkey(["ctrl", "s"])
```

## GUI 테스트 시나리오 예시

### Unity 게임 테스트
```
1. screenshot() - 현재 게임 화면 캡처
2. locate_image("start_button.png") - 시작 버튼 찾기
3. mouse_click(center.x, center.y) - 시작 버튼 클릭
4. wait(2) - 로딩 대기
5. screenshot() - 결과 확인
```

### Flutter 앱 테스트
```
1. screenshot_scaled("XGA") - 화면 캡처 (토큰 절약)
2. keyboard_type("test@example.com") - 이메일 입력
3. keyboard_key("Tab") - 다음 필드로 이동
4. keyboard_type("password123") - 비밀번호 입력
5. locate_image("login_button.png") - 로그인 버튼 찾기
6. mouse_click(x, y) - 로그인 클릭
```

## 폴더 구조

```
AG-mcp/
├── pyautogui_mcp/
│   ├── venv/              # 가상환경 (설치 후 생성)
│   ├── __init__.py
│   ├── server.py          # MCP 서버 메인
│   ├── config.py          # 설정 (AG_action 경로)
│   └── requirements.txt
├── setup_venv.bat         # 가상환경 설정 스크립트
├── start_mcp.bat          # 서버 시작 스크립트
├── start_mcp.ps1          # PowerShell 버전
└── README.md
```

## 의존성

- Python 3.10+
- mcp >= 1.0.0
- pyautogui >= 0.9.54
- Pillow >= 10.0.0
- AG_action (primitives 모듈)

## 트러블슈팅

### "AG_action not available" 에러
```
AG_action 경로를 찾을 수 없습니다.
config.py의 AG_ACTION_PATH 확인 또는 하드코딩 경로 수정.
```

### "pyautogui not available" 에러
```
pip install pyautogui Pillow
```

### "Virtual environment not found" 에러
```
setup_venv.bat를 먼저 실행하세요.
```

## 관련 문서

- [MCP Protocol](https://modelcontextprotocol.io/)
- [PyAutoGUI Docs](https://pyautogui.readthedocs.io/)
- [AG_action Primitives](../AG_action/primitives/)

# GUI Test Agent - A2A Protocol
# GUI 자동화 및 테스트 전문 에이전트 (PyAutoGUI 기반)
# Port: 8120

import os
import sys
import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found")

# AG_action 경로 추가
_ag_action_parent = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ag_action_parent))

# AG_action primitives import
try:
    from AG_action.primitives import MouseActions, KeyboardActions, ScreenActions, ScalingTarget
    AG_ACTION_AVAILABLE = True
    _mouse = MouseActions(dry_run=False)
    _keyboard = KeyboardActions(dry_run=False)
    _screen = ScreenActions(dry_run=False)
except ImportError as e:
    print(f"[WARNING] AG_action not available: {e}")
    AG_ACTION_AVAILABLE = False
    _mouse = None
    _keyboard = None
    _screen = None

# PyAutoGUI 직접 import (locate_image용)
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None


# ==============================================================================
# Tool Functions
# ==============================================================================

def take_screenshot(scale: str = "XGA", save_path: Optional[str] = None) -> Dict[str, Any]:
    """화면 스크린샷을 촬영한다.

    Args:
        scale: 스케일 타겟 - "XGA" (1024x768), "WXGA" (1280x800), "NONE" (원본)
        save_path: 저장 경로 (선택). 미지정시 임시 경로에 저장.

    Returns:
        스크린샷 정보:
        - success: 성공 여부
        - file_path: 저장된 파일 경로
        - width, height: 이미지 크기
        - base64_preview: Base64 인코딩된 이미지 (처음 1000자)
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        target = getattr(ScalingTarget, scale, ScalingTarget.XGA)
        result, scaling_info = _screen.screenshot_scaled(target=target)

        if not result.success:
            return {"success": False, "error": result.error}

        # 파일 저장
        if not save_path:
            import tempfile
            save_path = os.path.join(tempfile.gettempdir(), "gui_test_screenshot.png")

        with open(save_path, "wb") as f:
            f.write(result.data)

        return {
            "success": True,
            "file_path": save_path,
            "width": result.metadata.get("scaled_size", "").split("x")[0] if "scaled_size" in result.metadata else result.metadata.get("width"),
            "height": result.metadata.get("scaled_size", "").split("x")[1] if "scaled_size" in result.metadata else result.metadata.get("height"),
            "original_size": result.metadata.get("original_size", ""),
            "scale": scale,
            "base64_preview": result.base64_data[:200] + "..." if result.base64_data else "",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def click_at(x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
    """특정 좌표에 마우스 클릭을 수행한다.

    Args:
        x: X 좌표
        y: Y 좌표
        button: 버튼 종류 - "left", "right", "middle"
        clicks: 클릭 횟수 - 1 (단일), 2 (더블), 3 (트리플)

    Returns:
        클릭 결과:
        - success: 성공 여부
        - action: 수행된 액션
        - coordinate: [x, y]
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        coordinate = (x, y)

        if clicks == 1:
            if button == "left":
                result = _mouse.left_click(coordinate)
            elif button == "right":
                result = _mouse.right_click(coordinate)
            else:
                result = _mouse.middle_click(coordinate)
        elif clicks == 2:
            result = _mouse.double_click(coordinate)
        elif clicks == 3:
            result = _mouse.triple_click(coordinate)
        else:
            result = _mouse.left_click(coordinate)

        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def move_mouse(x: int, y: int) -> Dict[str, Any]:
    """마우스를 특정 좌표로 이동한다.

    Args:
        x: X 좌표
        y: Y 좌표

    Returns:
        이동 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _mouse.mouse_move((x, y))
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def drag_mouse(start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
    """마우스 드래그를 수행한다.

    Args:
        start_x, start_y: 시작 좌표
        end_x, end_y: 끝 좌표

    Returns:
        드래그 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _mouse.left_click_drag((start_x, start_y), (end_x, end_y))
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def type_text(text: str) -> Dict[str, Any]:
    """텍스트를 입력한다.

    Args:
        text: 입력할 텍스트

    Returns:
        입력 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _keyboard.type(text)
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def press_key(key: str) -> Dict[str, Any]:
    """특수 키 또는 조합키를 입력한다.

    Args:
        key: 키 이름 (예: "Return", "Escape", "ctrl+c", "alt+Tab")

    Returns:
        키 입력 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _keyboard.key(key)
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def hotkey(keys: List[str]) -> Dict[str, Any]:
    """조합키를 입력한다.

    Args:
        keys: 키 목록 (예: ["ctrl", "shift", "s"])

    Returns:
        조합키 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _keyboard.hotkey(*keys)
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_image_on_screen(image_path: str, confidence: float = 0.9) -> Dict[str, Any]:
    """화면에서 이미지를 찾는다. UI 요소 위치 검출에 사용.

    Args:
        image_path: 찾을 이미지 파일 경로 (PNG)
        confidence: 일치도 (0.0~1.0, 기본 0.9)

    Returns:
        검색 결과:
        - found: 발견 여부
        - location: {left, top, width, height}
        - center: {x, y} - 클릭할 중심 좌표
    """
    if not PYAUTOGUI_AVAILABLE:
        return {"found": False, "error": "pyautogui not available"}

    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            return {
                "found": True,
                "location": {
                    "left": location.left,
                    "top": location.top,
                    "width": location.width,
                    "height": location.height,
                },
                "center": {"x": center.x, "y": center.y},
                "tip": f"클릭하려면: click_at({center.x}, {center.y})"
            }
        else:
            return {"found": False, "message": "이미지를 화면에서 찾지 못했습니다."}
    except Exception as e:
        return {"found": False, "error": str(e)}


def get_screen_info() -> Dict[str, Any]:
    """화면 정보를 조회한다.

    Returns:
        화면 정보:
        - width, height: 화면 크기
        - mouse_position: 현재 마우스 위치
    """
    if not PYAUTOGUI_AVAILABLE:
        return {"error": "pyautogui not available"}

    try:
        size = pyautogui.size()
        pos = pyautogui.position()
        return {
            "width": size.width,
            "height": size.height,
            "mouse_position": {"x": pos.x, "y": pos.y}
        }
    except Exception as e:
        return {"error": str(e)}


def scroll(x: int, y: int, delta_y: int = 3, delta_x: int = 0) -> Dict[str, Any]:
    """마우스 스크롤을 수행한다.

    Args:
        x, y: 스크롤 위치
        delta_y: 수직 스크롤 양 (양수=위, 음수=아래)
        delta_x: 수평 스크롤 양

    Returns:
        스크롤 결과
    """
    if not AG_ACTION_AVAILABLE:
        return {"success": False, "error": "AG_action not available"}

    try:
        result = _mouse.scroll((x, y), delta_x, delta_y)
        return result.to_dict()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# Agent Definition
# ==============================================================================

agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="gui_test_agent",
    description="GUI 자동화 및 테스트 전문가. 화면 스크린샷, 마우스/키보드 제어, UI 요소 찾기 기능 제공. Unity, Flutter 등 데스크톱 앱 테스트에 활용.",
    instruction="""당신은 GUI 자동화 및 테스트 전문가입니다.

주요 기능:
1. take_screenshot - 화면 캡처 (XGA/WXGA 스케일 지원)
2. click_at - 특정 좌표 클릭 (단일/더블/트리플)
3. move_mouse - 마우스 이동
4. drag_mouse - 드래그
5. type_text - 텍스트 입력
6. press_key - 특수키/조합키 입력
7. hotkey - 단축키 (Ctrl+S 등)
8. find_image_on_screen - 이미지로 UI 요소 찾기
9. get_screen_info - 화면 크기, 마우스 위치 조회
10. scroll - 스크롤

사용 예시:
- "화면 스크린샷 찍어줘" → take_screenshot()
- "500, 300 좌표 클릭해줘" → click_at(500, 300)
- "play_button.png 찾아서 클릭해줘" → find_image_on_screen("play_button.png") → click_at(center.x, center.y)
- "Hello World 입력해줘" → type_text("Hello World")
- "Ctrl+S 눌러줘" → hotkey(["ctrl", "s"])

주의사항:
- 좌표는 화면 절대 좌표입니다 (왼쪽 상단이 0,0)
- 이미지 찾기는 PNG 파일이 필요합니다
- 스크린샷은 XGA(1024x768)로 스케일되어 토큰을 절약합니다
""",
    tools=[
        FunctionTool(take_screenshot),
        FunctionTool(click_at),
        FunctionTool(move_mouse),
        FunctionTool(drag_mouse),
        FunctionTool(type_text),
        FunctionTool(press_key),
        FunctionTool(hotkey),
        FunctionTool(find_image_on_screen),
        FunctionTool(get_screen_info),
        FunctionTool(scroll),
    ],
)


# ==============================================================================
# A2A Server
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("GUI Test Agent - A2A Server")
    print("=" * 50)
    print(f"AG_action available: {AG_ACTION_AVAILABLE}")
    print(f"PyAutoGUI available: {PYAUTOGUI_AVAILABLE}")
    print(f"Port: 8120")
    print("Agent Card: http://localhost:8120/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(agent, port=8120, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8120)

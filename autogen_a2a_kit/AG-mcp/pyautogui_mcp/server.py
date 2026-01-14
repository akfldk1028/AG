"""
PyAutoGUI MCP Server
====================

GUI 자동화를 위한 MCP 서버.
AG_action/primitives를 활용하여 마우스, 키보드, 스크린 제어.

Tools:
- screenshot: 스크린샷 촬영
- screenshot_scaled: 스케일된 스크린샷
- get_screen_size: 화면 크기
- mouse_click: 마우스 클릭
- mouse_move: 마우스 이동
- mouse_drag: 드래그
- mouse_scroll: 스크롤
- keyboard_type: 텍스트 입력
- keyboard_key: 키 입력
- keyboard_hotkey: 조합키
- locate_image: 이미지로 UI 요소 찾기

Usage:
    python server.py
"""

import asyncio
import base64
import json
from typing import Optional, List, Dict, Any

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

# Config (AG_action 경로 설정)
from config import (
    AG_ACTION_PATH,
    SERVER_NAME,
    SERVER_VERSION,
    PYAUTOGUI_FAILSAFE,
    PYAUTOGUI_PAUSE,
)

# AG_action primitives import
try:
    from AG_action.primitives import (
        MouseActions,
        KeyboardActions,
        ScreenActions,
        ScalingTarget,
    )
    AG_ACTION_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] AG_action not found: {e}")
    AG_ACTION_AVAILABLE = False
    MouseActions = None
    KeyboardActions = None
    ScreenActions = None
    ScalingTarget = None

# PyAutoGUI 직접 import (locate_image용)
try:
    import pyautogui
    pyautogui.FAILSAFE = PYAUTOGUI_FAILSAFE
    pyautogui.PAUSE = PYAUTOGUI_PAUSE
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None


# ==============================================================================
# MCP Server 초기화
# ==============================================================================

server = Server(SERVER_NAME)

# Primitives 인스턴스
_mouse: Optional[MouseActions] = None
_keyboard: Optional[KeyboardActions] = None
_screen: Optional[ScreenActions] = None


def _init_primitives():
    """Primitives 초기화 (lazy loading)"""
    global _mouse, _keyboard, _screen

    if AG_ACTION_AVAILABLE:
        if _mouse is None:
            _mouse = MouseActions(dry_run=False)
        if _keyboard is None:
            _keyboard = KeyboardActions(dry_run=False)
        if _screen is None:
            _screen = ScreenActions(dry_run=False)


# ==============================================================================
# Tool Definitions
# ==============================================================================

TOOLS = [
    Tool(
        name="screenshot",
        description="스크린샷 촬영. 전체 화면 또는 특정 영역 캡처.",
        inputSchema={
            "type": "object",
            "properties": {
                "region": {
                    "type": "object",
                    "description": "캡처 영역 (선택). 미지정시 전체 화면.",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"},
                    },
                },
            },
        },
    ),
    Tool(
        name="screenshot_scaled",
        description="스케일된 스크린샷. 토큰 효율을 위해 작은 해상도로 축소.",
        inputSchema={
            "type": "object",
            "properties": {
                "scale": {
                    "type": "string",
                    "description": "스케일 타겟: XGA (1024x768), WXGA (1280x800), NONE (원본)",
                    "enum": ["XGA", "WXGA", "NONE"],
                    "default": "XGA",
                },
            },
        },
    ),
    Tool(
        name="get_screen_size",
        description="화면 크기 조회 (width, height).",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="mouse_click",
        description="마우스 클릭. 좌/우/중간 버튼, 단일/더블/트리플 클릭 지원.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 좌표"},
                "y": {"type": "integer", "description": "Y 좌표"},
                "button": {
                    "type": "string",
                    "description": "버튼: left, right, middle",
                    "enum": ["left", "right", "middle"],
                    "default": "left",
                },
                "clicks": {
                    "type": "integer",
                    "description": "클릭 횟수: 1, 2 (더블), 3 (트리플)",
                    "default": 1,
                },
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="mouse_move",
        description="마우스를 특정 좌표로 이동.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 좌표"},
                "y": {"type": "integer", "description": "Y 좌표"},
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="mouse_drag",
        description="마우스 드래그 (시작점에서 끝점으로).",
        inputSchema={
            "type": "object",
            "properties": {
                "start_x": {"type": "integer"},
                "start_y": {"type": "integer"},
                "end_x": {"type": "integer"},
                "end_y": {"type": "integer"},
            },
            "required": ["start_x", "start_y", "end_x", "end_y"],
        },
    ),
    Tool(
        name="mouse_scroll",
        description="마우스 스크롤.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "스크롤 위치 X"},
                "y": {"type": "integer", "description": "스크롤 위치 Y"},
                "delta_y": {
                    "type": "integer",
                    "description": "수직 스크롤 양 (양수=위, 음수=아래)",
                    "default": 0,
                },
                "delta_x": {
                    "type": "integer",
                    "description": "수평 스크롤 양",
                    "default": 0,
                },
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="keyboard_type",
        description="텍스트 입력 (타이핑).",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "입력할 텍스트"},
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="keyboard_key",
        description="특수 키 입력 (Enter, Escape, Tab 등). 조합키는 ctrl+c 형식.",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "키 이름 (예: Return, Escape, ctrl+c, alt+Tab)",
                },
            },
            "required": ["key"],
        },
    ),
    Tool(
        name="keyboard_hotkey",
        description="조합키 입력 (예: Ctrl+Shift+S).",
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "키 목록 (예: ['ctrl', 'shift', 's'])",
                },
            },
            "required": ["keys"],
        },
    ),
    Tool(
        name="locate_image",
        description="화면에서 이미지 찾기. UI 요소 위치 검출에 사용.",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "찾을 이미지 파일 경로 (PNG)",
                },
                "confidence": {
                    "type": "number",
                    "description": "일치도 (0.0~1.0, 기본 0.9)",
                    "default": 0.9,
                },
            },
            "required": ["image_path"],
        },
    ),
    Tool(
        name="get_pixel_color",
        description="특정 좌표의 픽셀 색상 조회.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    ),
]


# ==============================================================================
# Tool Handlers
# ==============================================================================

@server.list_tools()
async def list_tools() -> List[Tool]:
    """사용 가능한 도구 목록 반환"""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
    """도구 실행"""
    _init_primitives()

    try:
        if name == "screenshot":
            return await _handle_screenshot(arguments)
        elif name == "screenshot_scaled":
            return await _handle_screenshot_scaled(arguments)
        elif name == "get_screen_size":
            return await _handle_get_screen_size(arguments)
        elif name == "mouse_click":
            return await _handle_mouse_click(arguments)
        elif name == "mouse_move":
            return await _handle_mouse_move(arguments)
        elif name == "mouse_drag":
            return await _handle_mouse_drag(arguments)
        elif name == "mouse_scroll":
            return await _handle_mouse_scroll(arguments)
        elif name == "keyboard_type":
            return await _handle_keyboard_type(arguments)
        elif name == "keyboard_key":
            return await _handle_keyboard_key(arguments)
        elif name == "keyboard_hotkey":
            return await _handle_keyboard_hotkey(arguments)
        elif name == "locate_image":
            return await _handle_locate_image(arguments)
        elif name == "get_pixel_color":
            return await _handle_get_pixel_color(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ==============================================================================
# Handler Implementations
# ==============================================================================

async def _handle_screenshot(args: Dict[str, Any]) -> List[TextContent | ImageContent]:
    """스크린샷"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    region = args.get("region")
    if region:
        region_tuple = (region["x"], region["y"], region["width"], region["height"])
    else:
        region_tuple = None

    result = _screen.screenshot(region=region_tuple)

    if result.success and result.base64_data:
        return [
            ImageContent(
                type="image",
                data=result.base64_data,
                mimeType="image/png",
            ),
            TextContent(
                type="text",
                text=json.dumps(result.metadata, indent=2),
            ),
        ]
    else:
        return [TextContent(type="text", text=f"Screenshot failed: {result.error}")]


async def _handle_screenshot_scaled(args: Dict[str, Any]) -> List[TextContent | ImageContent]:
    """스케일된 스크린샷"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    scale = args.get("scale", "XGA")
    target = getattr(ScalingTarget, scale, ScalingTarget.XGA)

    result, scaling_info = _screen.screenshot_scaled(target=target)

    if result.success and result.base64_data:
        metadata = {
            **result.metadata,
            "scaling": {
                "enabled": scaling_info.enabled,
                "scale_x": scaling_info.scale_x,
                "scale_y": scaling_info.scale_y,
            },
        }
        return [
            ImageContent(
                type="image",
                data=result.base64_data,
                mimeType="image/png",
            ),
            TextContent(
                type="text",
                text=json.dumps(metadata, indent=2),
            ),
        ]
    else:
        return [TextContent(type="text", text=f"Screenshot failed: {result.error}")]


async def _handle_get_screen_size(args: Dict[str, Any]) -> List[TextContent]:
    """화면 크기"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    width, height = _screen.get_screen_size()
    return [TextContent(type="text", text=json.dumps({"width": width, "height": height}))]


async def _handle_mouse_click(args: Dict[str, Any]) -> List[TextContent]:
    """마우스 클릭"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    x, y = args["x"], args["y"]
    button = args.get("button", "left")
    clicks = args.get("clicks", 1)

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

    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_mouse_move(args: Dict[str, Any]) -> List[TextContent]:
    """마우스 이동"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    result = _mouse.mouse_move((args["x"], args["y"]))
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_mouse_drag(args: Dict[str, Any]) -> List[TextContent]:
    """드래그"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    start = (args["start_x"], args["start_y"])
    end = (args["end_x"], args["end_y"])
    result = _mouse.left_click_drag(start, end)
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_mouse_scroll(args: Dict[str, Any]) -> List[TextContent]:
    """스크롤"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    coordinate = (args["x"], args["y"])
    delta_x = args.get("delta_x", 0)
    delta_y = args.get("delta_y", 0)
    result = _mouse.scroll(coordinate, delta_x, delta_y)
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_keyboard_type(args: Dict[str, Any]) -> List[TextContent]:
    """텍스트 입력"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    result = _keyboard.type(args["text"])
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_keyboard_key(args: Dict[str, Any]) -> List[TextContent]:
    """키 입력"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    result = _keyboard.key(args["key"])
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_keyboard_hotkey(args: Dict[str, Any]) -> List[TextContent]:
    """조합키"""
    if not AG_ACTION_AVAILABLE:
        return [TextContent(type="text", text="AG_action not available")]

    keys = args["keys"]
    result = _keyboard.hotkey(*keys)
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


async def _handle_locate_image(args: Dict[str, Any]) -> List[TextContent]:
    """이미지 찾기"""
    if not PYAUTOGUI_AVAILABLE:
        return [TextContent(type="text", text="pyautogui not available")]

    image_path = args["image_path"]
    confidence = args.get("confidence", 0.9)

    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            return [TextContent(type="text", text=json.dumps({
                "found": True,
                "location": {
                    "left": location.left,
                    "top": location.top,
                    "width": location.width,
                    "height": location.height,
                },
                "center": {"x": center.x, "y": center.y},
            }))]
        else:
            return [TextContent(type="text", text=json.dumps({"found": False}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _handle_get_pixel_color(args: Dict[str, Any]) -> List[TextContent]:
    """픽셀 색상"""
    if not PYAUTOGUI_AVAILABLE:
        return [TextContent(type="text", text="pyautogui not available")]

    x, y = args["x"], args["y"]
    try:
        color = pyautogui.pixel(x, y)
        return [TextContent(type="text", text=json.dumps({
            "x": x, "y": y,
            "color": {"r": color[0], "g": color[1], "b": color[2]},
            "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ==============================================================================
# Main
# ==============================================================================

async def main():
    """MCP 서버 실행"""
    print(f"[{SERVER_NAME}] Starting MCP server v{SERVER_VERSION}")
    print(f"[{SERVER_NAME}] AG_action available: {AG_ACTION_AVAILABLE}")
    print(f"[{SERVER_NAME}] PyAutoGUI available: {PYAUTOGUI_AVAILABLE}")
    print(f"[{SERVER_NAME}] AG_action path: {AG_ACTION_PATH}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

"""
MCP Handlers
=============

MCP Tool 및 Resource 핸들러.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

from ..fsm import FSMController, State
from ..primitives import ComputerUseExecutor


@dataclass
class ToolResult:
    """Tool 실행 결과"""
    success: bool
    content: Any
    error: Optional[str] = None

    def to_mcp_response(self) -> Dict[str, Any]:
        """MCP 응답 형식"""
        if self.success:
            return {
                "type": "text",
                "text": json.dumps(self.content, ensure_ascii=False)
            }
        else:
            return {
                "type": "text",
                "text": json.dumps({"error": self.error}, ensure_ascii=False),
                "isError": True,
            }


class ComputerToolHandler:
    """
    Computer Use Tool Handler

    MCP Tool: computer

    Claude Computer Use API의 모든 액션을 실행.
    """

    TOOL_DEFINITION = {
        "name": "computer",
        "description": "Execute Computer Use actions (screenshot, click, type, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "screenshot", "wait", "zoom",
                        "left_click", "right_click", "middle_click",
                        "double_click", "triple_click",
                        "mouse_move", "scroll", "left_click_drag",
                        "type", "key", "hold_key",
                    ],
                    "description": "Action to perform",
                },
                "coordinate": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "[x, y] coordinate for mouse actions",
                },
                "text": {
                    "type": "string",
                    "description": "Text to type (for 'type' action)",
                },
                "key": {
                    "type": "string",
                    "description": "Key to press (for 'key' action)",
                },
                "delta_x": {
                    "type": "integer",
                    "description": "Horizontal scroll amount",
                },
                "delta_y": {
                    "type": "integer",
                    "description": "Vertical scroll amount",
                },
                "seconds": {
                    "type": "number",
                    "description": "Wait duration in seconds",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self, executor: ComputerUseExecutor = None):
        self.executor = executor or ComputerUseExecutor()

    def handle(self, input_data: Dict[str, Any]) -> ToolResult:
        """Tool 실행"""
        action = input_data.get("action")
        if not action:
            return ToolResult(False, None, "Missing 'action' parameter")

        # action을 제외한 나머지 파라미터 추출
        params = {k: v for k, v in input_data.items() if k != "action"}

        # 실행
        result = self.executor.execute(action, **params)

        if result.success:
            return ToolResult(True, result.to_dict())
        else:
            return ToolResult(False, None, result.error)


class FSMToolHandler:
    """
    FSM Control Tool Handler

    MCP Tool: fsm_control

    FSM 상태 조회 및 제어.
    """

    TOOL_DEFINITION = {
        "name": "fsm_control",
        "description": "Control the FSM state machine",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["status", "start", "action", "verify", "reset"],
                    "description": "FSM command",
                },
                "request": {
                    "type": "string",
                    "description": "User request (for 'start' command)",
                },
                "action_type": {
                    "type": "string",
                    "description": "Action type (for 'action' command)",
                },
                "action_params": {
                    "type": "object",
                    "description": "Action parameters (for 'action' command)",
                },
                "is_complete": {
                    "type": "boolean",
                    "description": "Whether task is complete (for 'verify' command)",
                },
            },
            "required": ["command"],
        },
    }

    def __init__(self, controller: FSMController = None):
        self.controller = controller or FSMController()

    async def handle(self, input_data: Dict[str, Any]) -> ToolResult:
        """Tool 실행"""
        command = input_data.get("command")

        if command == "status":
            return ToolResult(True, self.controller.get_status())

        elif command == "start":
            request = input_data.get("request", "")
            success = await self.controller.start(request)
            return ToolResult(success, self.controller.get_status())

        elif command == "action":
            action_type = input_data.get("action_type", "")
            action_params = input_data.get("action_params", {})
            success = await self.controller.on_action_decided(action_type, action_params)
            return ToolResult(success, self.controller.get_status())

        elif command == "verify":
            is_complete = input_data.get("is_complete", False)
            reason = input_data.get("reason", "")
            success = await self.controller.on_verify_result(is_complete, reason)
            return ToolResult(success, self.controller.get_status())

        elif command == "reset":
            self.controller.reset()
            return ToolResult(True, self.controller.get_status())

        else:
            return ToolResult(False, None, f"Unknown command: {command}")


class FSMResourceHandler:
    """
    FSM Resource Handler

    MCP Resource: fsm://state, screenshot://latest
    """

    def __init__(self, controller: FSMController = None):
        self.controller = controller or FSMController()
        self._latest_screenshot: Optional[Dict[str, Any]] = None

    def get_resources(self):
        """사용 가능한 리소스 목록"""
        return [
            {
                "uri": "fsm://state",
                "name": "FSM State",
                "description": "Current FSM state and history",
                "mimeType": "application/json",
            },
            {
                "uri": "fsm://history",
                "name": "FSM History",
                "description": "FSM transition history",
                "mimeType": "application/json",
            },
            {
                "uri": "screenshot://latest",
                "name": "Latest Screenshot",
                "description": "Most recent screen capture",
                "mimeType": "image/png",
            },
        ]

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """리소스 읽기"""
        if uri == "fsm://state":
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(self.controller.state.to_dict(), ensure_ascii=False),
                    }
                ]
            }

        elif uri == "fsm://history":
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(self.controller.state.history, ensure_ascii=False),
                    }
                ]
            }

        elif uri == "screenshot://latest":
            if self._latest_screenshot:
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "image/png",
                            "blob": self._latest_screenshot.get("base64_data", ""),
                        }
                    ]
                }
            else:
                return {"contents": [], "error": "No screenshot available"}

        else:
            return {"contents": [], "error": f"Unknown resource: {uri}"}

    def set_screenshot(self, screenshot_data: Dict[str, Any]):
        """최신 스크린샷 설정"""
        self._latest_screenshot = screenshot_data

"""
AG_action MCP Server
=====================

Model Context Protocol Server for Computer Use Actions.

포트: 8130

Tools:
- computer: Computer Use 액션 실행
- fsm_control: FSM 상태 관리

Resources:
- fsm://state: 현재 FSM 상태
- fsm://history: FSM 전이 히스토리
- screenshot://latest: 최신 스크린샷
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any, List, Optional

# FastAPI for HTTP server
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 로컬 모듈
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
from fsm import FSMController, State
from primitives import ComputerUseExecutor
from mcp.handlers import ComputerToolHandler, FSMToolHandler, FSMResourceHandler


# ============================================
# Pydantic Models
# ============================================

class MCPRequest(BaseModel):
    """MCP JSON-RPC 요청"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC 응답"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ToolCallRequest(BaseModel):
    """Tool 호출 요청"""
    name: str
    arguments: Dict[str, Any] = {}


class ResourceReadRequest(BaseModel):
    """Resource 읽기 요청"""
    uri: str


# ============================================
# MCP Server
# ============================================

class ActionMCPServer:
    """
    AG_action MCP Server

    JSON-RPC 2.0 기반 MCP 프로토콜 구현.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8130,
        dry_run: bool = False,
    ):
        self.host = host
        self.port = port
        self.dry_run = dry_run

        # 핵심 컴포넌트
        self.executor = ComputerUseExecutor(dry_run)
        self.controller = FSMController()

        # 핸들러
        self.computer_handler = ComputerToolHandler(self.executor)
        self.fsm_handler = FSMToolHandler(self.controller)
        self.resource_handler = FSMResourceHandler(self.controller)

        # FastAPI 앱
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """FastAPI 앱 생성"""
        app = FastAPI(
            title="AG_action MCP Server",
            description="Computer Use + FSM + MCP",
            version="1.0.0",
        )

        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # ========================================
        # MCP Endpoints
        # ========================================

        @app.post("/")
        async def mcp_jsonrpc(request: MCPRequest) -> MCPResponse:
            """MCP JSON-RPC 엔드포인트"""
            try:
                result = await self._handle_rpc(request.method, request.params or {})
                return MCPResponse(id=request.id, result=result)
            except Exception as e:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32603, "message": str(e)}
                )

        @app.get("/tools")
        async def list_tools():
            """Tool 목록"""
            return {
                "tools": [
                    self.computer_handler.TOOL_DEFINITION,
                    self.fsm_handler.TOOL_DEFINITION,
                ]
            }

        @app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            """Tool 호출"""
            return await self._call_tool(request.name, request.arguments)

        @app.get("/resources")
        async def list_resources():
            """Resource 목록"""
            return {"resources": self.resource_handler.get_resources()}

        @app.post("/resources/read")
        async def read_resource(request: ResourceReadRequest):
            """Resource 읽기"""
            return self.resource_handler.read_resource(request.uri)

        # ========================================
        # REST Endpoints (편의용)
        # ========================================

        @app.get("/status")
        async def get_status():
            """서버 및 FSM 상태"""
            return {
                "server": {
                    "host": self.host,
                    "port": self.port,
                    "dry_run": self.dry_run,
                },
                "fsm": self.controller.get_status(),
                "screen_size": self.executor.get_screen_size(),
            }

        @app.post("/computer/{action}")
        async def execute_action(action: str, params: Dict[str, Any] = {}):
            """Computer Use 액션 실행"""
            result = self.executor.execute(action, **params)
            return result.to_dict()

        @app.post("/fsm/start")
        async def fsm_start(request: Dict[str, str]):
            """FSM 시작"""
            user_request = request.get("request", "")
            success = await self.controller.start(user_request)
            return {"success": success, "state": self.controller.get_status()}

        @app.post("/fsm/reset")
        async def fsm_reset():
            """FSM 리셋"""
            self.controller.reset()
            return {"success": True, "state": self.controller.get_status()}

        return app

    async def _handle_rpc(self, method: str, params: Dict[str, Any]) -> Any:
        """JSON-RPC 메서드 처리"""
        if method == "initialize":
            return self._handle_initialize(params)

        elif method == "tools/list":
            return {
                "tools": [
                    self.computer_handler.TOOL_DEFINITION,
                    self.fsm_handler.TOOL_DEFINITION,
                ]
            }

        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            return await self._call_tool(name, arguments)

        elif method == "resources/list":
            return {"resources": self.resource_handler.get_resources()}

        elif method == "resources/read":
            uri = params.get("uri", "")
            return self.resource_handler.read_resource(uri)

        else:
            raise ValueError(f"Unknown method: {method}")

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 초기화"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "ag_action",
                "version": "1.0.0",
            },
            "capabilities": {
                "tools": {},
                "resources": {},
            },
        }

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool 호출"""
        if name == "computer":
            result = self.computer_handler.handle(arguments)
            return result.to_mcp_response()

        elif name == "fsm_control":
            result = await self.fsm_handler.handle(arguments)
            return result.to_mcp_response()

        else:
            return {
                "type": "text",
                "text": json.dumps({"error": f"Unknown tool: {name}"}),
                "isError": True,
            }

    def run(self):
        """서버 실행"""
        print(f"\n[AG_action MCP Server]")
        print(f"  Host: {self.host}")
        print(f"  Port: {self.port}")
        print(f"  Dry Run: {self.dry_run}")
        print(f"\n  MCP Endpoint: http://{self.host}:{self.port}/")
        print(f"  Tools: http://{self.host}:{self.port}/tools")
        print(f"  Resources: http://{self.host}:{self.port}/resources")
        print(f"  Status: http://{self.host}:{self.port}/status")
        print()

        uvicorn.run(self.app, host=self.host, port=self.port)


# ============================================
# CLI
# ============================================

def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description="AG_action MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8130, help="Server port")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no actual actions)")
    args = parser.parse_args()

    server = ActionMCPServer(
        host=args.host,
        port=args.port,
        dry_run=args.dry_run,
    )
    server.run()


if __name__ == "__main__":
    main()

# WebSocket Bridge - Message Bus to AutoGen Studio UI
"""
AG-CLI Message Bus의 대화 이벤트를 AutoGen Studio UI로 중계합니다.

두 가지 모드:
1. Standalone: 독립 WebSocket 서버로 실행
2. Embedded: AutoGen Studio 앱에 통합

사용법:
    python studio/websocket_bridge.py --port 8102
"""
import asyncio
import json
from datetime import datetime
from typing import Set, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

# ============================================================
# Configuration
# ============================================================

MESSAGE_BUS_URL = "http://localhost:8100"
MESSAGE_BUS_WS = "ws://localhost:8100/ws"

# ============================================================
# WebSocket Manager
# ============================================================

class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.message_history: list = []  # 최근 메시지 캐시
        self.max_history = 100

    async def connect(self, websocket: WebSocket):
        """새 클라이언트 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)

        # 최근 메시지 히스토리 전송
        if self.message_history:
            await websocket.send_json({
                "type": "history",
                "messages": self.message_history[-20:]  # 최근 20개
            })

    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """모든 클라이언트에게 브로드캐스트"""
        # 히스토리에 추가
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

        # 브로드캐스트
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # 끊어진 연결 정리
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_to_ui(self, event_type: str, data: Dict[str, Any]):
        """UI 포맷으로 변환하여 전송"""
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        await self.broadcast(message)


manager = ConnectionManager()

# ============================================================
# Message Bus Subscriber
# ============================================================

async def subscribe_to_message_bus():
    """Message Bus WebSocket에 연결하여 이벤트 수신"""
    import websockets

    while True:
        try:
            async with websockets.connect(MESSAGE_BUS_WS) as ws:
                print(f"[Bridge] Connected to Message Bus: {MESSAGE_BUS_WS}")

                # Message Bus에 구독 등록
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "client": "studio_bridge"
                }))

                # 이벤트 수신 루프
                async for message in ws:
                    try:
                        event = json.loads(message)
                        await handle_message_bus_event(event)
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"[Bridge] Connection error: {e}, retrying in 5s...")
            await asyncio.sleep(5)


async def handle_message_bus_event(event: Dict[str, Any]):
    """Message Bus 이벤트를 UI 포맷으로 변환"""
    event_type = event.get("event_type", "message")

    # AutoGen Studio UI 포맷으로 변환
    ui_message = {
        "type": "agent_message",
        "source": event.get("from_agent", "unknown"),
        "target": event.get("to_agent", "all"),
        "content": event.get("message", ""),
        "metadata": {
            "event_type": event_type,
            "timestamp": event.get("timestamp", datetime.now().isoformat())
        }
    }

    await manager.send_to_ui("agent_dialogue", ui_message)


# ============================================================
# Polling Fallback (Message Bus REST API)
# ============================================================

async def poll_message_bus():
    """Message Bus REST API를 폴링하여 이벤트 수신 (WebSocket 실패 시 폴백)"""
    last_count = 0

    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f"{MESSAGE_BUS_URL}/log", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])

                    # 새 이벤트만 전송
                    new_events = events[last_count:]
                    for event in new_events:
                        await handle_message_bus_event(event)

                    last_count = len(events)

            except Exception:
                pass

            await asyncio.sleep(1)  # 1초마다 폴링


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(title="AG-CLI WebSocket Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """클라이언트 WebSocket 연결"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트에서 오는 명령 처리 (필요시)
            try:
                cmd = json.loads(data)
                if cmd.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/status")
async def get_status():
    """브릿지 상태 조회"""
    return {
        "status": "running",
        "connections": len(manager.active_connections),
        "message_history_count": len(manager.message_history),
        "message_bus_url": MESSAGE_BUS_URL
    }


@app.get("/history")
async def get_history(limit: int = 50):
    """메시지 히스토리 조회"""
    return {
        "messages": manager.message_history[-limit:],
        "total": len(manager.message_history)
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Message Bus 구독 시작"""
    # WebSocket 구독 시도, 실패하면 폴링 모드로 전환
    asyncio.create_task(subscribe_with_fallback())


async def subscribe_with_fallback():
    """WebSocket 구독 시도, 실패 시 폴링 모드"""
    try:
        # WebSocket 구독 시도
        await subscribe_to_message_bus()
    except Exception as e:
        print(f"[Bridge] WebSocket failed, switching to polling mode: {e}")
        await poll_message_bus()


# ============================================================
# HTML Viewer (Standalone)
# ============================================================

VIEWER_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>AG-CLI Dialogue Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Consolas', monospace;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        #messages {
            max-height: 70vh;
            overflow-y: auto;
            border: 1px solid #333;
            padding: 10px;
            background: #16213e;
            border-radius: 8px;
        }
        .message {
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 4px;
            border-left: 3px solid;
        }
        .message.say { border-color: #00ff88; background: rgba(0,255,136,0.1); }
        .message.ask { border-color: #ffaa00; background: rgba(255,170,0,0.1); }
        .message.work { border-color: #00d4ff; background: rgba(0,212,255,0.1); }
        .from { color: #00ff88; font-weight: bold; }
        .to { color: #888; }
        .content { color: #fff; margin-top: 4px; }
        .timestamp { color: #555; font-size: 0.8em; float: right; }
        #status {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 8px 16px;
            border-radius: 20px;
        }
        #status.connected { background: #00ff88; color: #000; }
        #status.disconnected { background: #ff4444; color: #fff; }
    </style>
</head>
<body>
    <div id="status" class="disconnected">Disconnected</div>
    <h1>AG-CLI Dialogue Viewer</h1>
    <div id="messages"></div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const statusDiv = document.getElementById('status');

        function connect() {
            const ws = new WebSocket('ws://localhost:8102/ws');

            ws.onopen = () => {
                statusDiv.textContent = 'Connected';
                statusDiv.className = 'connected';
            };

            ws.onclose = () => {
                statusDiv.textContent = 'Disconnected';
                statusDiv.className = 'disconnected';
                setTimeout(connect, 3000);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'history') {
                    data.messages.forEach(addMessage);
                } else if (data.type === 'agent_dialogue') {
                    addMessage(data);
                }
            };
        }

        function addMessage(msg) {
            const div = document.createElement('div');
            const eventType = msg.metadata?.event_type || 'say';
            div.className = 'message ' + eventType;

            const time = new Date(msg.metadata?.timestamp || Date.now())
                .toLocaleTimeString();

            div.innerHTML = `
                <span class="timestamp">${time}</span>
                <span class="from">${msg.source}</span>
                <span class="to">→ ${msg.target}</span>
                <div class="content">${msg.content}</div>
            `;

            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        connect();
    </script>
</body>
</html>
"""


@app.get("/viewer")
async def viewer():
    """HTML 뷰어 페이지"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=VIEWER_HTML)


# ============================================================
# Entry Point
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AG-CLI WebSocket Bridge")
    parser.add_argument("--port", type=int, default=8102, help="브릿지 포트 (기본값: 8102)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트")
    parser.add_argument("--message-bus", default="http://localhost:8100",
                        help="Message Bus URL")
    args = parser.parse_args()

    global MESSAGE_BUS_URL, MESSAGE_BUS_WS
    MESSAGE_BUS_URL = args.message_bus
    MESSAGE_BUS_WS = args.message_bus.replace("http://", "ws://") + "/ws"

    print("=" * 60)
    print("AG-CLI WebSocket Bridge")
    print("=" * 60)
    print(f"Bridge URL:      http://{args.host}:{args.port}")
    print(f"WebSocket:       ws://{args.host}:{args.port}/ws")
    print(f"Viewer:          http://{args.host}:{args.port}/viewer")
    print(f"Message Bus:     {MESSAGE_BUS_URL}")
    print("=" * 60)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

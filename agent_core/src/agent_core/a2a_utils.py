"""
A2A (Agent-to-Agent) 서버 유틸리티
"""

from typing import Optional
import uvicorn
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a


def create_a2a_app(
    agent: Agent,
    port: int = 8001,
    host: str = "127.0.0.1",
):
    """
    에이전트를 A2A 앱으로 변환
    
    Args:
        agent: Agent 객체
        port: 서버 포트
        host: 서버 호스트
        
    Returns:
        FastAPI/Starlette 앱 객체
    """
    return to_a2a(agent, port=port, host=host)


def run_a2a_server(
    agent: Agent,
    port: Optional[int] = None,
    host: Optional[str] = None,
    log_level: str = "info",
    reload: bool = False,
):
    """
    에이전트를 A2A 서버로 실행
    
    Args:
        agent: Agent 객체
        port: 서버 포트 (기본값: agent._config.port 또는 8001)
        host: 서버 호스트 (기본값: agent._config.host 또는 "127.0.0.1")
        log_level: 로그 레벨
        reload: 코드 변경 시 자동 재시작 (개발용)
        
    Example:
        agent = create_agent("config.yaml", tools=[my_tool])
        run_a2a_server(agent)  # 블로킹 - 서버 시작
    """
    # 설정에서 port/host 가져오기
    if hasattr(agent, "_config"):
        cfg = agent._config
        port = port or cfg.port
        host = host or cfg.host
    
    port = port or 8001
    host = host or "127.0.0.1"
    
    # 시작 메시지
    print("=" * 60)
    print(f"  {agent.name} - A2A Server")
    print("=" * 60)
    print(f"  Description: {agent.description}")
    print(f"  Model: {agent.model}")
    print(f"  Host: {host}:{port}")
    print(f"  Agent Card: http://{host}:{port}/.well-known/agent.json")
    print("=" * 60)
    
    # A2A 앱 생성
    app = create_a2a_app(agent, port=port, host=host)
    
    # 서버 실행
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
    )


async def run_a2a_server_async(
    agent: Agent,
    port: Optional[int] = None,
    host: Optional[str] = None,
):
    """
    비동기로 A2A 서버 실행 (다른 async 코드와 함께 사용)
    
    Example:
        async def main():
            await run_a2a_server_async(agent)
    """
    import asyncio
    
    if hasattr(agent, "_config"):
        cfg = agent._config
        port = port or cfg.port
        host = host or cfg.host
    
    port = port or 8001
    host = host or "127.0.0.1"
    
    app = create_a2a_app(agent, port=port, host=host)
    
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()

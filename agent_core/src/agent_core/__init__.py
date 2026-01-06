"""
Agent Core - 재사용 가능한 에이전트 라이브러리

사용법:
    from agent_core import create_agent, run_a2a_server
    
    agent = create_agent("config.yaml", tools=[my_tool])
    run_a2a_server(agent)
"""

from .config_loader import load_config, AgentConfig
from .agent_factory import create_agent, create_agent_from_config
from .a2a_utils import run_a2a_server, create_a2a_app

__version__ = "0.1.0"

__all__ = [
    "load_config",
    "AgentConfig",
    "create_agent",
    "create_agent_from_config",
    "run_a2a_server",
    "create_a2a_app",
]

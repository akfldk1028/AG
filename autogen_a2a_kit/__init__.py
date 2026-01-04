# -*- coding: utf-8 -*-
"""
AutoGen + A2A Integration Kit
=============================
어떤 프로젝트에든 복사해서 바로 사용 가능

설치:
    pip install autogen-agentchat autogen-ext[openai] requests

사용:
    from autogen_a2a_kit import create_a2a_tool, quick_agent, run_task

    tool = create_a2a_tool("http://localhost:8001/")
    result = await run_task("질문", tools=[tool])
"""

from .a2a_client import create_a2a_tool, call_a2a, check_server
from .agents import quick_agent, run_task, multi_agent_task

__all__ = [
    'create_a2a_tool',
    'call_a2a',
    'check_server',
    'quick_agent',
    'run_task',
    'multi_agent_task'
]

__version__ = "1.0.0"

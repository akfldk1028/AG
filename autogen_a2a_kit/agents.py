# -*- coding: utf-8 -*-
"""
AutoGen Agent Helpers - 간단하게 에이전트 생성
"""

import os
import asyncio
from typing import List, Callable, Optional

# .env 파일 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 지연 임포트 (설치 안되어있으면 에러 메시지)
def _check_imports():
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
        from autogen_agentchat.conditions import TextMentionTermination
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        return True
    except ImportError:
        print("=" * 50)
        print("AutoGen 패키지가 설치되지 않았습니다.")
        print("설치 명령어:")
        print("  pip install autogen-agentchat autogen-ext[openai]")
        print("=" * 50)
        return False


def quick_agent(
    name: str = "assistant",
    tools: List[Callable] = None,
    system_message: str = None,
    model: str = "gpt-4o-mini",
    api_key: str = None
):
    """
    빠르게 에이전트 생성

    Args:
        name: 에이전트 이름
        tools: 도구 함수 리스트
        system_message: 시스템 메시지
        model: 모델명
        api_key: OpenAI API Key (없으면 환경변수)

    Returns:
        AssistantAgent
    """
    if not _check_imports():
        return None

    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        print("[Error] OPENAI_API_KEY 환경변수를 설정하세요")
        return None

    client = OpenAIChatCompletionClient(model=model, api_key=key)

    return AssistantAgent(
        name=name,
        model_client=client,
        tools=tools or [],
        system_message=system_message or "You are a helpful assistant. Say TERMINATE when done."
    )


async def run_task(
    task: str,
    tools: List[Callable] = None,
    model: str = "gpt-4o-mini",
    api_key: str = None
) -> str:
    """
    단일 에이전트로 작업 실행

    Args:
        task: 수행할 작업
        tools: 도구 함수 리스트
        model: 모델명
        api_key: API Key

    Returns:
        결과 문자열
    """
    if not _check_imports():
        return "AutoGen not installed"

    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import TextMentionTermination

    agent = quick_agent("worker", tools, model=model, api_key=api_key)
    if not agent:
        return "Agent creation failed"

    team = RoundRobinGroupChat(
        participants=[agent],
        termination_condition=TextMentionTermination("TERMINATE")
    )

    result = await team.run(task=task)

    # 마지막 응답 추출
    for msg in reversed(result.messages):
        if hasattr(msg, 'content'):
            content = str(msg.content)
            if "TERMINATE" not in content and len(content) > 10:
                return content

    return str(result.messages[-1].content) if result.messages else ""


async def multi_agent_task(
    task: str,
    agents_config: List[dict],
    model: str = "gpt-4o-mini",
    api_key: str = None
) -> dict:
    """
    멀티 에이전트로 작업 실행

    Args:
        task: 수행할 작업
        agents_config: 에이전트 설정 리스트
            [{"name": "agent1", "tools": [...], "system_message": "..."}]
        model: 모델명
        api_key: API Key

    Returns:
        {"messages": [...], "result": str}
    """
    if not _check_imports():
        return {"messages": [], "result": "AutoGen not installed"}

    from autogen_agentchat.teams import SelectorGroupChat
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    key = api_key or os.environ.get("OPENAI_API_KEY")
    client = OpenAIChatCompletionClient(model=model, api_key=key)

    agents = []
    for cfg in agents_config:
        agent = quick_agent(
            name=cfg.get("name", "agent"),
            tools=cfg.get("tools", []),
            system_message=cfg.get("system_message"),
            model=model,
            api_key=key
        )
        if agent:
            agents.append(agent)

    if not agents:
        return {"messages": [], "result": "No agents created"}

    team = SelectorGroupChat(
        participants=agents,
        model_client=client,
        termination_condition=TextMentionTermination("TERMINATE")
    )

    result = await team.run(task=task)

    messages = []
    for msg in result.messages:
        if hasattr(msg, 'content') and hasattr(msg, 'source'):
            messages.append({
                "agent": msg.source,
                "content": str(msg.content)[:500]
            })

    return {"messages": messages, "result": messages[-1]["content"] if messages else ""}


# 동기 래퍼
def run_task_sync(task: str, tools: List[Callable] = None, **kwargs) -> str:
    """run_task의 동기 버전"""
    return asyncio.run(run_task(task, tools, **kwargs))


def multi_agent_sync(task: str, agents_config: List[dict], **kwargs) -> dict:
    """multi_agent_task의 동기 버전"""
    return asyncio.run(multi_agent_task(task, agents_config, **kwargs))

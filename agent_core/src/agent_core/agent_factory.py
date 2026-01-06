"""
에이전트 팩토리 - 설정에서 에이전트 생성
"""

import os
from typing import Callable, List, Optional, Union
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .config_loader import load_config, AgentConfig


def create_agent(
    config: Union[str, Path, dict, AgentConfig],
    tools: Optional[List[Callable]] = None,
    **kwargs
) -> Agent:
    """
    설정에서 에이전트 생성
    
    Args:
        config: 설정 파일 경로, dict, 또는 AgentConfig 객체
        tools: 에이전트에 추가할 도구 함수 리스트
        **kwargs: Agent 생성자에 전달할 추가 인자
        
    Returns:
        생성된 Agent 객체
        
    Example:
        # 기본 사용
        agent = create_agent("config.yaml", tools=[my_tool])
        
        # dict로 직접 설정
        agent = create_agent({
            "name": "my_agent",
            "model": "openai/gpt-4o-mini",
            "description": "내 에이전트"
        }, tools=[tool1, tool2])
        
        # 추가 옵션
        agent = create_agent("config.yaml", tools=[my_tool], temperature=0.7)
    """
    # 설정 로드
    if isinstance(config, AgentConfig):
        cfg = config
    else:
        cfg = load_config(config)
    
    # API 키 환경 변수 설정
    if cfg.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", cfg.openai_api_key)
    if cfg.anthropic_api_key:
        os.environ.setdefault("ANTHROPIC_API_KEY", cfg.anthropic_api_key)
    
    # 도구를 FunctionTool로 래핑
    function_tools = []
    if tools:
        for tool in tools:
            if isinstance(tool, FunctionTool):
                function_tools.append(tool)
            elif callable(tool):
                function_tools.append(FunctionTool(tool))
            else:
                raise ValueError(f"도구는 callable이어야 합니다: {tool}")
    
    # Agent 생성
    agent = Agent(
        model=cfg.model,
        name=cfg.name,
        description=cfg.description or f"{cfg.name} 에이전트",
        instruction=cfg.instruction or "도움이 필요하시면 말씀해주세요.",
        tools=function_tools if function_tools else None,
        **kwargs
    )
    
    # 설정 저장 (나중에 참조용)
    agent._config = cfg
    
    return agent


def create_agent_from_config(config_path: str | Path, **kwargs) -> Agent:
    """
    설정 파일에서 에이전트 생성 (도구 없이)
    
    나중에 도구를 추가하려면:
        agent.tools.append(FunctionTool(my_tool))
    """
    return create_agent(config_path, tools=None, **kwargs)


# 편의 함수들
def quick_agent(
    name: str,
    tools: List[Callable],
    model: str = "openai/gpt-4o-mini",
    description: str = "",
    instruction: str = "",
) -> Agent:
    """
    빠른 에이전트 생성 (설정 파일 없이)
    
    Example:
        agent = quick_agent(
            name="math_agent",
            tools=[add, subtract],
            description="수학 계산 에이전트"
        )
    """
    config = {
        "name": name,
        "model": model,
        "description": description,
        "instruction": instruction,
    }
    return create_agent(config, tools=tools)

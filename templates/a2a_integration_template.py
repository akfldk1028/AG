# -*- coding: utf-8 -*-
"""
=============================================================================
A2A Multi-Agent Integration Template
=============================================================================
이 템플릿을 복사하여 새 프로젝트에서 사용하세요.

사용법:
1. A2A_SERVER_URL을 원격 에이전트 주소로 변경
2. 필요한 에이전트 추가/수정
3. task 변수에 작업 입력
4. python a2a_integration_template.py 실행
=============================================================================
"""

import os
import json
import uuid
import requests
import asyncio
from typing import Optional, Callable

# ============================================================================
# CONFIGURATION - 여기를 수정하세요
# ============================================================================

OPENAI_API_KEY = "your-api-key-here"  # OpenAI API Key
A2A_SERVER_URL = "http://localhost:8001/"  # A2A 서버 주소
MODEL_NAME = "gpt-4o-mini"  # 사용할 모델

# ============================================================================
# A2A CLIENT - 재사용 가능한 A2A 클라이언트
# ============================================================================

def create_a2a_tool(
    name: str,
    description: str,
    server_url: str = A2A_SERVER_URL
) -> Callable:
    """
    A2A 도구 함수를 생성합니다.

    Args:
        name: 도구 이름 (함수명으로 사용됨)
        description: 도구 설명 (LLM이 도구 선택시 참고)
        server_url: A2A 서버 URL

    Returns:
        A2A 호출 함수
    """
    def a2a_tool(query: str) -> str:
        message_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": message_id,
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"kind": "text", "text": query}]
                }
            }
        }

        try:
            print(f"\n    [A2A] {name} -> {server_url}")
            response = requests.post(
                server_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "result" in result:
                for artifact in result["result"].get("artifacts", []):
                    for part in artifact.get("parts", []):
                        if part.get("kind") == "text":
                            text = part.get("text", "")
                            print(f"    [A2A] Response received!")
                            return f"[{name}] {text}"

            return json.dumps(result, ensure_ascii=False)

        except requests.exceptions.ConnectionError:
            return f"[Error] Cannot connect to {server_url}"
        except Exception as e:
            return f"[Error] {str(e)}"

    # 함수 메타데이터 설정
    a2a_tool.__name__ = name
    a2a_tool.__doc__ = description

    return a2a_tool


def check_a2a_server(url: str = A2A_SERVER_URL) -> bool:
    """A2A 서버 상태 확인"""
    try:
        response = requests.get(f"{url}.well-known/agent.json", timeout=5)
        agent_info = response.json()
        print(f"[OK] A2A Server: {agent_info.get('name', 'Unknown')}")
        return True
    except:
        print(f"[FAIL] Cannot connect to {url}")
        return False


# ============================================================================
# MULTI-AGENT SETUP
# ============================================================================

async def run_multi_agent_system(task: str):
    """멀티 에이전트 시스템 실행"""

    # Import AutoGen components
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import SelectorGroupChat
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    print("=" * 60)
    print("Multi-Agent System with A2A Integration")
    print("=" * 60)

    # 서버 상태 확인
    if not check_a2a_server():
        print("Warning: A2A server not available")

    # 모델 클라이언트
    model = OpenAIChatCompletionClient(model=MODEL_NAME, api_key=OPENAI_API_KEY)

    # A2A 도구 생성
    remote_agent_tool = create_a2a_tool(
        name="call_remote_agent",
        description="원격 A2A 에이전트에게 질문합니다.",
        server_url=A2A_SERVER_URL
    )

    # =========================================
    # 에이전트 정의 - 필요에 따라 수정하세요
    # =========================================

    coordinator = AssistantAgent(
        name="Coordinator",
        model_client=model,
        system_message="""You are the team coordinator.
Analyze tasks and delegate to specialists:
- Remote_Expert: for tasks requiring the remote A2A agent
When done, say TERMINATE."""
    )

    remote_expert = AssistantAgent(
        name="Remote_Expert",
        model_client=model,
        tools=[remote_agent_tool],
        system_message="""You are the remote agent specialist.
Use the call_remote_agent tool to communicate with external A2A agents.
Report findings back to the Coordinator."""
    )

    # 팀 구성
    team = SelectorGroupChat(
        participants=[coordinator, remote_expert],
        model_client=model,
        termination_condition=TextMentionTermination("TERMINATE"),
        selector_prompt="""Select the next speaker based on the conversation:
- Coordinator: for planning and summarizing
- Remote_Expert: when external agent communication is needed"""
    )

    # 실행
    print(f"\n[Task] {task}\n")
    print("-" * 60)

    result = await team.run(task=task)

    # 결과 출력
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    for msg in result.messages:
        if hasattr(msg, 'content') and hasattr(msg, 'source'):
            content = str(msg.content)
            if len(content) > 500:
                content = content[:500] + "..."
            print(f"\n[{msg.source}]\n  {content}")

    return result


# ============================================================================
# SIMPLE USAGE - 단순 A2A 호출용
# ============================================================================

def simple_a2a_call(query: str, url: str = A2A_SERVER_URL) -> str:
    """단순 A2A 호출 (에이전트 없이)"""
    tool = create_a2a_tool("simple_call", "Simple A2A call", url)
    return tool(query)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # 예시 작업
    task = "Check if 97 is a prime number using the remote agent."

    # 멀티 에이전트 실행
    asyncio.run(run_multi_agent_system(task))

    # 또는 단순 호출:
    # result = simple_a2a_call("Is 97 prime?")
    # print(result)

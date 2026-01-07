# Root Agent - A2A Protocol Demo
# 이 에이전트는 원격 A2A 에이전트를 호출하여 작업을 수행합니다

import os
import asyncio
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# 환경 변수에서 API 키 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    print("  Windows: set OPENAI_API_KEY=sk-...")
    print("  Linux:   export OPENAI_API_KEY=sk-...")
    exit(1)

# 원격 A2A 에이전트 연결
remote_prime_agent = RemoteA2aAgent(
    name="remote_prime_checker",
    description="원격 서버에서 실행 중인 소수 판별 에이전트입니다.",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}"
)

# 코디네이터 에이전트 생성
coordinator_agent = Agent(
    model="openai/gpt-4o-mini",
    name="coordinator_agent",
    description="수학 관련 질문을 처리하는 코디네이터 에이전트입니다.",
    instruction="""당신은 수학 코디네이터 에이전트입니다.

사용자가 소수나 소인수분해에 관한 질문을 하면:
1. remote_prime_checker 에이전트에게 작업을 위임하세요
2. 결과를 받아서 사용자에게 친절하게 설명해주세요

다른 수학 질문은 직접 답변할 수 있습니다.
항상 한국어로 응답해주세요.""",
    sub_agents=[remote_prime_agent]
)


def create_user_message(text: str) -> Content:
    """사용자 메시지 Content 객체 생성"""
    return Content(role="user", parts=[Part(text=text)])


async def run_demo():
    """A2A 데모 실행"""
    print("=" * 60)
    print("A2A Protocol Demo - Coordinator Agent")
    print("=" * 60)
    print("Remote agent URL: http://localhost:8001")
    print("=" * 60)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=coordinator_agent,
        app_name="a2a_demo",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="a2a_demo",
        user_id="demo_user"
    )

    test_questions = [
        "17이 소수인지 확인해줘",
        "100을 소인수분해 해줘",
        "97은 소수야?",
    ]

    print("\nRunning demo questions...\n")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Question {i}: {question}")
        print("=" * 60)

        user_message = create_user_message(question)

        async for event in runner.run_async(
            session_id=session.id,
            user_id="demo_user",
            new_message=user_message
        ):
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"\nResponse: {part.text}")

        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())

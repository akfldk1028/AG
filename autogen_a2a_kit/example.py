# -*- coding: utf-8 -*-
"""
사용 예제 - 이 파일을 참고하세요
"""

import os
import asyncio

# .env 파일 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 없으면 환경변수 직접 사용

# API Key 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY가 설정되지 않았습니다.")
    print("  1. .env.example을 .env로 복사")
    print("  2. .env 파일에 API 키 입력")
    print("  또는: set OPENAI_API_KEY=sk-...")
    exit(1)

# 이 패키지에서 임포트 (패키지 내/외부 모두 지원)
try:
    from autogen_a2a_kit import create_a2a_tool, call_a2a, check_server
    from autogen_a2a_kit import quick_agent, run_task, multi_agent_task
except ImportError:
    from a2a_client import create_a2a_tool, call_a2a, check_server
    from agents import quick_agent, run_task, multi_agent_task


# ============================================
# 예제 1: 단순 A2A 호출 (에이전트 없이)
# ============================================
def example_simple_a2a():
    print("=== 예제 1: 단순 A2A 호출 ===")

    # 서버 상태 확인
    status = check_server("http://localhost:8001/")
    print(f"Server: {status}")

    # 직접 호출
    if status["available"]:
        result = call_a2a("Is 97 a prime number?", "http://localhost:8001/")
        print(f"Result: {result}")


# ============================================
# 예제 2: 단일 에이전트 + A2A 도구
# ============================================
async def example_single_agent():
    print("\n=== 예제 2: 단일 에이전트 ===")

    # A2A 도구 생성
    prime_tool = create_a2a_tool("http://localhost:8001/", "check_prime")

    # 작업 실행
    result = await run_task(
        task="Check if 97 is a prime number using the check_prime tool",
        tools=[prime_tool]
    )
    print(f"Result: {result}")


# ============================================
# 예제 3: 멀티 에이전트 협업
# ============================================
async def example_multi_agent():
    print("\n=== 예제 3: 멀티 에이전트 ===")

    # A2A 도구
    prime_tool = create_a2a_tool("http://localhost:8001/", "check_prime")

    # 계산기 도구 (주의: eval은 예제용, 실제 사용시 안전한 파서 사용)
    def calculator(expr: str) -> str:
        """수학 계산을 수행합니다."""
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except Exception:
            return "Error: Invalid expression"

    # 에이전트 설정
    agents = [
        {
            "name": "coordinator",
            "system_message": "Coordinate tasks. Delegate to math_expert or prime_expert. Say TERMINATE when done."
        },
        {
            "name": "math_expert",
            "tools": [calculator],
            "system_message": "Do math calculations using the calculator tool."
        },
        {
            "name": "prime_expert",
            "tools": [prime_tool],
            "system_message": "Check prime numbers using check_prime tool."
        }
    ]

    # 실행
    result = await multi_agent_task(
        task="Calculate 97 * 3, then check if both 97 and the result are prime numbers.",
        agents_config=agents
    )

    print("Messages:")
    for msg in result["messages"]:
        print(f"  [{msg['agent']}] {msg['content'][:100]}...")


# ============================================
# 메인
# ============================================
if __name__ == "__main__":
    # 예제 1
    example_simple_a2a()

    # 예제 2, 3 (async)
    asyncio.run(example_single_agent())
    asyncio.run(example_multi_agent())

# Remote Agent - A2A Protocol Demo
# 이 에이전트는 A2A 서버로 노출되어 다른 에이전트가 호출할 수 있습니다

import os
import sys

# .env 파일에서 환경변수 로드
try:
    from dotenv import load_dotenv
    # 현재 파일 위치 기준으로 .env 찾기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from: {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment variables")

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# 환경 변수에서 API 키 확인
if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요!")
    print("  Windows: set OPENAI_API_KEY=sk-...")
    print("  Linux:   export OPENAI_API_KEY=sk-...")
    exit(1)


def is_prime(n: int) -> dict:
    """숫자가 소수인지 확인합니다.

    Args:
        n: 확인할 숫자

    Returns:
        소수 여부와 설명을 담은 딕셔너리
    """
    if n < 2:
        return {"number": n, "is_prime": False, "reason": f"{n}은(는) 2보다 작아서 소수가 아닙니다."}
    if n == 2:
        return {"number": n, "is_prime": True, "reason": "2는 유일한 짝수 소수입니다."}
    if n % 2 == 0:
        return {"number": n, "is_prime": False, "reason": f"{n}은(는) 짝수이므로 소수가 아닙니다."}

    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return {"number": n, "is_prime": False, "reason": f"{n}은(는) {i}로 나누어 떨어지므로 소수가 아닙니다."}

    return {"number": n, "is_prime": True, "reason": f"{n}은(는) 소수입니다!"}


def get_prime_factors(n: int) -> dict:
    """숫자의 소인수분해를 수행합니다.

    Args:
        n: 소인수분해할 숫자

    Returns:
        소인수분해 결과를 담은 딕셔너리
    """
    if n < 2:
        return {"number": n, "factors": [], "explanation": f"{n}은(는) 소인수분해할 수 없습니다."}

    factors = []
    original = n
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)

    factor_str = " × ".join(map(str, factors))
    return {
        "number": original,
        "factors": factors,
        "explanation": f"{original} = {factor_str}"
    }


# 소수 판별 에이전트 생성
prime_checker_agent = Agent(
    model="openai/gpt-4o-mini",
    name="prime_checker_agent",
    description="소수를 판별하고 소인수분해를 수행하는 수학 전문 에이전트입니다.",
    instruction="""당신은 수학 전문 에이전트입니다.

주요 기능:
1. 숫자가 소수인지 확인 (is_prime 도구 사용)
2. 숫자의 소인수분해 수행 (get_prime_factors 도구 사용)

항상 친절하고 교육적인 방식으로 설명해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(is_prime),
        FunctionTool(get_prime_factors)
    ]
)

# A2A 서버로 노출
if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Prime Checker Agent - A2A Server")
    print("=" * 50)
    print("This agent provides prime checking and factorization.")
    print("A2A server starting on port 8002...")
    print("Agent Card URL: http://localhost:8002/.well-known/agent.json")
    print("=" * 50)

    # A2A 앱 생성
    a2a_app = to_a2a(
        prime_checker_agent,
        port=8002,
        host="127.0.0.1"
    )

    # uvicorn으로 서버 실행
    uvicorn.run(a2a_app, host="127.0.0.1", port=8002)

# Calculator Agent - A2A Protocol Demo
# 기본 수학 연산을 수행하는 A2A 에이전트

import os
import sys

# .env 파일에서 환경변수 로드
try:
    from dotenv import load_dotenv
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
    exit(1)


def calculate(expression: str) -> dict:
    """수학 표현식을 계산합니다.

    Args:
        expression: 계산할 수학 표현식 (예: "2 + 3 * 4")

    Returns:
        계산 결과를 담은 딕셔너리
    """
    try:
        # 안전한 계산을 위해 허용된 문자만 사용
        allowed_chars = set("0123456789+-*/%().** ")
        if not all(c in allowed_chars for c in expression):
            return {"expression": expression, "result": None, "error": "허용되지 않는 문자가 포함되어 있습니다."}

        result = eval(expression)
        return {"expression": expression, "result": result, "error": None}
    except Exception as e:
        return {"expression": expression, "result": None, "error": str(e)}


def fibonacci(n: int) -> dict:
    """n번째 피보나치 수를 계산합니다.

    Args:
        n: 피보나치 수열의 인덱스 (0부터 시작)

    Returns:
        피보나치 수와 수열을 담은 딕셔너리
    """
    if n < 0:
        return {"n": n, "result": None, "sequence": [], "error": "음수는 허용되지 않습니다."}
    if n > 50:
        return {"n": n, "result": None, "sequence": [], "error": "너무 큰 수입니다. 50 이하로 입력해주세요."}

    sequence = []
    a, b = 0, 1
    for i in range(n + 1):
        sequence.append(a)
        a, b = b, a + b

    return {
        "n": n,
        "result": sequence[-1] if sequence else 0,
        "sequence": sequence[:min(10, len(sequence))],  # 처음 10개만 표시
        "error": None
    }


def factorial(n: int) -> dict:
    """n의 팩토리얼을 계산합니다.

    Args:
        n: 팩토리얼을 계산할 숫자

    Returns:
        팩토리얼 결과를 담은 딕셔너리
    """
    if n < 0:
        return {"n": n, "result": None, "error": "음수의 팩토리얼은 정의되지 않습니다."}
    if n > 20:
        return {"n": n, "result": None, "error": "너무 큰 수입니다. 20 이하로 입력해주세요."}

    result = 1
    for i in range(2, n + 1):
        result *= i

    return {"n": n, "result": result, "explanation": f"{n}! = {result}"}


# 계산기 에이전트 생성
calculator_agent = Agent(
    model="openai/gpt-4o-mini",
    name="calculator_agent",
    description="기본 수학 연산, 피보나치 수열, 팩토리얼 계산을 수행하는 수학 계산 에이전트입니다.",
    instruction="""당신은 수학 계산 전문 에이전트입니다.

주요 기능:
1. 수학 표현식 계산 (calculate 도구 사용) - 덧셈, 뺄셈, 곱셈, 나눗셈, 거듭제곱 등
2. 피보나치 수열 계산 (fibonacci 도구 사용)
3. 팩토리얼 계산 (factorial 도구 사용)

항상 친절하고 교육적인 방식으로 설명해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(calculate),
        FunctionTool(fibonacci),
        FunctionTool(factorial)
    ]
)

# A2A 서버로 노출
if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Calculator Agent - A2A Server")
    print("=" * 50)
    print("This agent provides calculation services.")
    print("A2A server starting on port 8003...")
    print("Agent Card URL: http://localhost:8003/.well-known/agent.json")
    print("=" * 50)

    # A2A 앱 생성
    a2a_app = to_a2a(
        calculator_agent,
        port=8003,
        host="127.0.0.1"
    )

    # uvicorn으로 서버 실행
    uvicorn.run(a2a_app, host="127.0.0.1", port=8003)

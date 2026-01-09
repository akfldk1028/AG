# Math Expert Agent - A2A Protocol
# 수학 전문가 에이전트

import os
import math
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found")


def solve_quadratic(a: float, b: float, c: float) -> dict:
    """이차방정식 ax^2 + bx + c = 0을 푼다.

    Args:
        a: x^2의 계수
        b: x의 계수
        c: 상수항

    Returns:
        해와 판별식 정보
    """
    discriminant = b**2 - 4*a*c

    if discriminant > 0:
        x1 = (-b + math.sqrt(discriminant)) / (2*a)
        x2 = (-b - math.sqrt(discriminant)) / (2*a)
        return {
            "discriminant": discriminant,
            "type": "두 개의 실근",
            "solutions": [x1, x2],
            "formula": f"x = {x1:.4f} 또는 x = {x2:.4f}"
        }
    elif discriminant == 0:
        x = -b / (2*a)
        return {
            "discriminant": discriminant,
            "type": "중근",
            "solutions": [x],
            "formula": f"x = {x:.4f}"
        }
    else:
        real = -b / (2*a)
        imag = math.sqrt(-discriminant) / (2*a)
        return {
            "discriminant": discriminant,
            "type": "두 개의 허근",
            "solutions": [f"{real:.4f} + {imag:.4f}i", f"{real:.4f} - {imag:.4f}i"],
            "formula": f"x = {real:.4f} ± {imag:.4f}i"
        }


def fibonacci_analysis(n: int) -> dict:
    """피보나치 수열 분석.

    Args:
        n: 분석할 항의 개수 (최대 30)

    Returns:
        피보나치 수열과 황금비 분석
    """
    n = min(n, 30)  # 최대 30개

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])

    # 황금비 수렴 분석
    golden_ratio = (1 + math.sqrt(5)) / 2
    ratios = []
    for i in range(2, len(fib)):
        if fib[i-1] != 0:
            ratios.append(fib[i] / fib[i-1])

    return {
        "sequence": fib[:n],
        "golden_ratio": golden_ratio,
        "ratio_convergence": ratios[-5:] if len(ratios) >= 5 else ratios,
        "sum": sum(fib[:n]),
        "nth_term": fib[n-1] if n > 0 else 0,
        "property": "각 항은 이전 두 항의 합 (F_n = F_{n-1} + F_{n-2})"
    }


def prime_factorization(n: int) -> dict:
    """소인수분해를 수행한다.

    Args:
        n: 소인수분해할 양의 정수 (최대 1000000)

    Returns:
        소인수분해 결과
    """
    if n < 2:
        return {"error": "2 이상의 정수를 입력하세요"}

    n = min(n, 1000000)
    original = n
    factors = []
    d = 2

    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1

    if n > 1:
        factors.append(n)

    # 인수 카운트
    factor_count = {}
    for f in factors:
        factor_count[f] = factor_count.get(f, 0) + 1

    # 수식 형태로 표현
    factorization = " × ".join([f"{p}^{e}" if e > 1 else str(p)
                                 for p, e in factor_count.items()])

    return {
        "number": original,
        "factors": factors,
        "unique_primes": list(factor_count.keys()),
        "factorization": f"{original} = {factorization}",
        "is_prime": len(factors) == 1,
        "divisor_count": math.prod(e + 1 for e in factor_count.values())
    }


def matrix_determinant(matrix: list) -> dict:
    """2x2 또는 3x3 행렬의 행렬식을 계산한다.

    Args:
        matrix: 2x2 또는 3x3 행렬 (2차원 리스트)

    Returns:
        행렬식 값과 특성
    """
    n = len(matrix)

    if n == 2 and len(matrix[0]) == 2:
        det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        return {
            "size": "2x2",
            "determinant": det,
            "formula": f"ad - bc = ({matrix[0][0]}×{matrix[1][1]}) - ({matrix[0][1]}×{matrix[1][0]})",
            "invertible": det != 0,
            "interpretation": "det > 0: 방향 보존, det < 0: 방향 반전, det = 0: 특이행렬"
        }
    elif n == 3 and len(matrix[0]) == 3:
        a, b, c = matrix[0]
        d, e, f = matrix[1]
        g, h, i = matrix[2]
        det = a*(e*i - f*h) - b*(d*i - f*g) + c*(d*h - e*g)
        return {
            "size": "3x3",
            "determinant": det,
            "method": "사루스 법칙 또는 여인수 전개",
            "invertible": det != 0,
            "volume_interpretation": f"|det| = {abs(det)} (평행육면체 부피)"
        }
    else:
        return {"error": "2x2 또는 3x3 행렬만 지원합니다"}


# 수학 전문 에이전트
math_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="math_agent",
    description="수학 문제 해결과 수학적 개념 설명을 전문으로 하는 에이전트입니다. 대수학, 정수론, 선형대수 등을 다룹니다.",
    instruction="""당신은 수학 전문가 에이전트입니다.

주요 기능:
1. 이차방정식 풀기 (solve_quadratic) - 판별식과 해 계산
2. 피보나치 분석 (fibonacci_analysis) - 황금비 수렴 분석
3. 소인수분해 (prime_factorization) - 정수론적 분석
4. 행렬식 계산 (matrix_determinant) - 선형대수 기초

토론 시 역할:
- 수학적 관점에서 문제를 분석합니다
- 논리적이고 엄밀한 사고를 제시합니다
- 추상화와 패턴 인식을 강조합니다
- 수학적 증명과 논증을 활용합니다

수학의 아름다움과 실용성을 모두 전달해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(solve_quadratic),
        FunctionTool(fibonacci_analysis),
        FunctionTool(prime_factorization),
        FunctionTool(matrix_determinant)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Math Expert Agent - A2A Server")
    print("=" * 50)
    print("Port: 8007")
    print("Agent Card: http://localhost:8007/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(math_agent, port=8007, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8007)

"""
공통으로 사용할 수 있는 도구들
"""

from typing import Dict, Any, List
import json
from datetime import datetime


# ============================================================
# 수학 도구
# ============================================================

def is_prime(n: int) -> Dict[str, Any]:
    """
    숫자가 소수인지 확인합니다.
    
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


def get_prime_factors(n: int) -> Dict[str, Any]:
    """
    숫자의 소인수분해를 수행합니다.
    
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


def calculate(expression: str) -> Dict[str, Any]:
    """
    수학 표현식을 계산합니다.
    
    Args:
        expression: 계산할 수학 표현식 (예: "2 + 3 * 4")
        
    Returns:
        계산 결과
    """
    try:
        # 안전한 eval (숫자와 기본 연산자만)
        allowed_chars = set("0123456789+-*/%().^ ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "허용되지 않은 문자가 포함되어 있습니다."}
        
        # ^ -> ** 변환 (거듭제곱)
        expression = expression.replace("^", "**")
        result = eval(expression)
        
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# 유틸리티 도구
# ============================================================

def get_current_time() -> Dict[str, str]:
    """현재 시간을 반환합니다."""
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
    }


def format_json(data: str) -> Dict[str, Any]:
    """
    JSON 문자열을 정리합니다.
    
    Args:
        data: JSON 문자열
        
    Returns:
        정리된 JSON
    """
    try:
        parsed = json.loads(data)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        return {"formatted": formatted, "valid": True}
    except json.JSONDecodeError as e:
        return {"error": str(e), "valid": False}


# ============================================================
# 텍스트 도구
# ============================================================

def count_words(text: str) -> Dict[str, int]:
    """
    텍스트의 단어 수를 셉니다.
    
    Args:
        text: 분석할 텍스트
        
    Returns:
        단어 수, 문자 수, 줄 수
    """
    return {
        "words": len(text.split()),
        "characters": len(text),
        "characters_no_space": len(text.replace(" ", "")),
        "lines": len(text.splitlines()),
    }


def reverse_text(text: str) -> str:
    """텍스트를 뒤집습니다."""
    return text[::-1]


# ============================================================
# 도구 모음 (편의용)
# ============================================================

MATH_TOOLS = [is_prime, get_prime_factors, calculate]
UTIL_TOOLS = [get_current_time, format_json]
TEXT_TOOLS = [count_words, reverse_text]
ALL_TOOLS = MATH_TOOLS + UTIL_TOOLS + TEXT_TOOLS

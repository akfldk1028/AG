"""
수학 에이전트 - agent_core 사용 예제

실행 방법:
    python main.py

코드가 이렇게 간단해집니다!
"""

from agent_core import create_agent, run_a2a_server
from agent_core.common_tools import MATH_TOOLS

# 1. 에이전트 생성 (설정 + 도구)
agent = create_agent("config.yaml", tools=MATH_TOOLS)

# 2. A2A 서버 실행
if __name__ == "__main__":
    run_a2a_server(agent)

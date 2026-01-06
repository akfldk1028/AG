"""
커스텀 에이전트 예제

이 예제는 직접 만든 도구를 사용하는 방법을 보여줍니다.
"""

from agent_core import create_agent, run_a2a_server
from tools import MY_TOOLS  # 내가 만든 도구들

# 에이전트 생성
agent = create_agent("config.yaml", tools=MY_TOOLS)

if __name__ == "__main__":
    run_a2a_server(agent)

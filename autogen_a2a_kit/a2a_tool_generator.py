# -*- coding: utf-8 -*-
"""
A2A Agent Card -> AutoGen Studio FunctionTool 자동 생성기

사용법:
    python a2a_tool_generator.py http://localhost:8002/.well-known/agent.json

Agent Card URL만 입력하면 AutoGen Studio에서 사용할 수 있는
FunctionTool 코드를 자동으로 생성합니다.
"""

import sys
import json
import re
import requests
from urllib.parse import urlparse


def get_agent_card(url: str) -> dict:
    """Agent Card 가져오기"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Agent Card를 가져올 수 없습니다: {e}")
        sys.exit(1)


def extract_base_url(agent_card_url: str) -> str:
    """Agent Card URL에서 기본 A2A 서버 URL 추출"""
    parsed = urlparse(agent_card_url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def sanitize_name(name: str) -> str:
    """Python 함수 이름으로 사용할 수 있도록 변환"""
    # 공백과 특수문자를 언더스코어로 변환
    name = re.sub(r'[^a-zA-Z0-9가-힣]', '_', name)
    # 숫자로 시작하면 앞에 언더스코어 추가
    if name and name[0].isdigit():
        name = '_' + name
    return name.lower()


def generate_function_tool(agent_card: dict, base_url: str) -> str:
    """FunctionTool 코드 생성"""

    agent_name = agent_card.get('name', 'a2a_agent')
    description = agent_card.get('description', 'A2A 에이전트')
    skills = agent_card.get('skills', [])

    func_name = f"call_a2a_{sanitize_name(agent_name)}"

    # 스킬 정보 문자열 생성
    skills_info = ""
    if skills:
        skills_info = "\n    사용 가능한 스킬:\n"
        for skill in skills:
            skill_name = skill.get('name', '')
            skill_desc = skill.get('description', '')
            skills_info += f"    - {skill_name}: {skill_desc}\n"

    code = f'''def {func_name}(query: str) -> str:
    """A2A 프로토콜로 {agent_name} 에이전트를 호출합니다.

    {description}{skills_info}
    Args:
        query: 에이전트에게 보낼 질문/요청

    Returns:
        에이전트의 응답 텍스트
    """
    import requests
    import json
    import uuid

    A2A_SERVER_URL = "{base_url}"

    payload = {{
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {{
            "message": {{
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{{"type": "text", "text": query}}]
            }}
        }}
    }}

    try:
        response = requests.post(
            A2A_SERVER_URL,
            json=payload,
            headers={{"Content-Type": "application/json"}},
            timeout=60
        )
        result = response.json()

        if "result" in result and "artifacts" in result["result"]:
            for artifact in result["result"]["artifacts"]:
                for part in artifact.get("parts", []):
                    if "text" in part:
                        return part["text"]

        if "error" in result:
            return f"에러: {{result['error']}}"

        return str(result)
    except Exception as e:
        return f"A2A 호출 실패: {{str(e)}}"
'''
    return code


def generate_autogen_studio_config(agent_card: dict, code: str) -> dict:
    """AutoGen Studio JSON 설정 생성"""
    agent_name = agent_card.get('name', 'a2a_agent')
    description = agent_card.get('description', 'A2A 에이전트')
    func_name = f"call_a2a_{sanitize_name(agent_name)}"

    return {
        "provider": "autogen_core.tools.FunctionTool",
        "config": {
            "source_code": code,
            "name": func_name,
            "description": f"A2A 프로토콜로 {agent_name} 호출: {description}",
            "global_imports": ["requests", "json", "uuid"],
            "has_cancellation_support": False  # 필수!
        }
    }


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("A2A Agent Card -> FunctionTool 자동 생성기")
        print("=" * 60)
        print("\n사용법:")
        print("  python a2a_tool_generator.py <agent_card_url>")
        print("\n예시:")
        print("  python a2a_tool_generator.py http://localhost:8002/.well-known/agent.json")
        print("=" * 60)
        sys.exit(0)

    agent_card_url = sys.argv[1]

    print("=" * 60)
    print("A2A Agent Card -> FunctionTool 자동 생성기")
    print("=" * 60)

    # 1. Agent Card 가져오기
    print(f"\n[1] Agent Card 가져오기: {agent_card_url}")
    agent_card = get_agent_card(agent_card_url)

    print(f"    이름: {agent_card.get('name', 'N/A')}")
    print(f"    설명: {agent_card.get('description', 'N/A')}")
    skills = agent_card.get('skills', [])
    if skills:
        print(f"    스킬: {[s.get('name') for s in skills]}")

    # 2. 기본 URL 추출
    base_url = extract_base_url(agent_card_url)
    print(f"\n[2] A2A 서버 URL: {base_url}")

    # 3. FunctionTool 코드 생성
    print("\n[3] FunctionTool 코드 생성...")
    code = generate_function_tool(agent_card, base_url)

    # 4. AutoGen Studio 설정 생성
    config = generate_autogen_studio_config(agent_card, code)

    # 출력
    print("\n" + "=" * 60)
    print("AutoGen Studio에 복사할 Python 코드")
    print("=" * 60)
    print(code)

    print("\n" + "=" * 60)
    print("AutoGen Studio JSON 설정 (Tools -> JSON Editor)")
    print("=" * 60)
    print(json.dumps(config, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("사용 방법:")
    print("=" * 60)
    print("1. AutoGen Studio -> Build -> Tools -> New Tool")
    print("2. 위의 Python 코드를 복사해서 붙여넣기")
    print("3. 또는 JSON Editor에서 위의 JSON 설정 사용")
    print("4. 반드시 has_cancellation_support: false 확인!")
    print("=" * 60)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
A2A Client - 어떤 A2A 서버든 호출 가능
"""

import requests
import uuid
import json
from typing import Callable

def call_a2a(query: str, url: str = "http://localhost:8001/", timeout: int = 30) -> str:
    """
    A2A 서버에 메시지 전송

    Args:
        query: 질문/요청
        url: A2A 서버 URL
        timeout: 타임아웃 (초)

    Returns:
        서버 응답 텍스트
    """
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
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()

        # 응답에서 텍스트 추출
        if "result" in result:
            for artifact in result["result"].get("artifacts", []):
                for part in artifact.get("parts", []):
                    if part.get("kind") == "text":
                        return part.get("text", "")

        return json.dumps(result, ensure_ascii=False)

    except requests.exceptions.ConnectionError:
        return f"[Error] Cannot connect to {url}"
    except requests.exceptions.Timeout:
        return f"[Error] Timeout after {timeout}s"
    except Exception as e:
        return f"[Error] {str(e)}"


def create_a2a_tool(url: str = "http://localhost:8001/", name: str = "call_remote_agent") -> Callable:
    """
    AutoGen용 A2A 도구 함수 생성

    Args:
        url: A2A 서버 URL
        name: 도구 이름

    Returns:
        AutoGen에서 사용할 수 있는 함수
    """
    def tool_func(query: str) -> str:
        """원격 A2A 에이전트에게 질문합니다."""
        print(f"    [A2A] -> {url}")
        result = call_a2a(query, url)
        print(f"    [A2A] <- Response received")
        return result

    tool_func.__name__ = name
    tool_func.__doc__ = f"A2A 프로토콜로 {url}의 원격 에이전트를 호출합니다."

    return tool_func


def check_server(url: str = "http://localhost:8001/") -> dict:
    """
    A2A 서버 상태 확인

    Returns:
        {"available": bool, "name": str, "description": str}
    """
    try:
        check_url = url.rstrip('/') + "/.well-known/agent.json"
        resp = requests.get(check_url, timeout=5)
        info = resp.json()
        return {
            "available": True,
            "name": info.get("name", "Unknown"),
            "description": info.get("description", "")
        }
    except Exception:
        return {"available": False, "name": None, "description": None}

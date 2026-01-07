# -*- coding: utf-8 -*-
"""
A2A Minimal Template - 최소 코드로 A2A 연동
복사해서 바로 사용하세요!
"""

import requests
import uuid

# ============= 설정 =============
A2A_URL = "http://localhost:8001/"
# ================================

def call_a2a(query: str) -> str:
    """A2A 에이전트 호출"""
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": str(uuid.uuid4()),
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": query}]
            }
        }
    }

    resp = requests.post(A2A_URL, json=payload, timeout=30).json()

    for a in resp.get("result", {}).get("artifacts", []):
        for p in a.get("parts", []):
            if p.get("kind") == "text":
                return p.get("text", "")
    return str(resp)


if __name__ == "__main__":
    # 테스트
    print(call_a2a("Is 97 a prime number?"))

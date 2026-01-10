# api/routes/a2a.py
"""
A2A Agent API
- Agent Card Import
- Agent Registry (이름으로 에이전트 관리)
- Agent Component 생성 (팀에 직접 추가 가능)
"""
import re
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from autogenstudio.a2a.registry import A2ARegistry, RegisteredAgent

router = APIRouter()

# 글로벌 레지스트리 인스턴스
_registry: Optional[A2ARegistry] = None


def get_registry() -> A2ARegistry:
    """레지스트리 인스턴스 가져오기"""
    global _registry
    if _registry is None:
        _registry = A2ARegistry()
    return _registry


# ============== Request/Response Models ==============

class A2AImportRequest(BaseModel):
    """A2A Agent Card Import 요청"""
    agent_card_url: str


class A2ARegisterRequest(BaseModel):
    """A2A 에이전트 등록 요청"""
    url: str  # A2A 서버 URL


class A2AImportResponse(BaseModel):
    """A2A Import 응답"""
    status: bool
    message: str
    agent_name: Optional[str] = None
    agent_description: Optional[str] = None
    skills: Optional[list] = None
    tool_config: Optional[dict] = None
    agent_config: Optional[dict] = None  # 에이전트로 추가할 때 사용


class A2ARegistryResponse(BaseModel):
    """레지스트리 응답"""
    status: bool
    message: str
    agents: List[dict] = []


class A2AAgentConfigResponse(BaseModel):
    """에이전트 ComponentModel 응답"""
    status: bool
    message: str
    component: Optional[dict] = None


# ============== Helper Functions ==============

def sanitize_name(name: str) -> str:
    """Python 함수 이름으로 사용할 수 있도록 변환"""
    name = re.sub(r'[^a-zA-Z0-9가-힣]', '_', name)
    if name and name[0].isdigit():
        name = '_' + name
    return name.lower()


def generate_function_code(agent_name: str, description: str, base_url: str, skills: list) -> str:
    """FunctionTool 코드 생성 (기존 도구 방식 호환)"""
    func_name = f"call_a2a_{sanitize_name(agent_name)}"

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


# ============== API Endpoints ==============

@router.post("/import")
async def import_from_agent_card(request: A2AImportRequest) -> A2AImportResponse:
    """
    A2A Agent Card URL에서 에이전트 정보를 가져와서:
    1. FunctionTool 설정 생성 (기존 방식)
    2. A2AAgent ComponentModel 생성 (팀에 에이전트로 추가)
    3. 레지스트리에 자동 등록
    """
    try:
        # 1. Agent Card 가져오기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(request.agent_card_url)
            response.raise_for_status()
            agent_card = response.json()

        # 2. 에이전트 정보 추출
        agent_name = agent_card.get('name', 'a2a_agent')
        description = agent_card.get('description', 'A2A 에이전트')
        skills = agent_card.get('skills', [])

        # 3. 기본 URL 추출
        parsed = urlparse(request.agent_card_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 4. FunctionTool 코드 생성 (기존 방식 호환)
        func_name = f"call_a2a_{sanitize_name(agent_name)}"
        source_code = generate_function_code(agent_name, description, base_url, skills)

        tool_config = {
            "provider": "autogen_core.tools.FunctionTool",
            "label": func_name,
            "description": f"A2A: {description}",
            "config": {
                "source_code": source_code,
                "name": func_name,
                "description": f"A2A 프로토콜로 {agent_name} 호출: {description}",
                "global_imports": ["requests", "json", "uuid"],
                "has_cancellation_support": False
            }
        }

        # 5. A2AAgent ComponentModel 생성 (팀에 에이전트로 추가)
        safe_name = sanitize_name(agent_name)
        agent_config = {
            "provider": "autogenstudio.a2a.A2AAgent",
            "component_type": "agent",
            "version": 1,
            "description": description,
            "label": agent_name,
            "config": {
                "name": safe_name,
                "a2a_server_url": base_url,
                "description": description,
                "timeout": 60,
                "skills": skills
            }
        }

        # 6. 레지스트리에 자동 등록
        registry = get_registry()
        registered_agent = RegisteredAgent(
            name=safe_name,
            display_name=agent_name,
            url=base_url,
            description=description,
            skills=skills,
            is_online=True
        )
        registry.register_agent(registered_agent)

        return A2AImportResponse(
            status=True,
            message=f"'{agent_name}' 에이전트를 가져왔습니다. 도구 또는 에이전트로 추가할 수 있습니다.",
            agent_name=agent_name,
            agent_description=description,
            skills=skills,
            tool_config=tool_config,
            agent_config=agent_config
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Agent Card를 가져올 수 없습니다: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Agent Card URL에 연결할 수 없습니다: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent Card 처리 중 오류: {str(e)}"
        )


@router.get("/registry")
async def list_registered_agents() -> A2ARegistryResponse:
    """등록된 모든 A2A 에이전트 목록"""
    registry = get_registry()
    agents = registry.list_agents()
    return A2ARegistryResponse(
        status=True,
        message=f"{len(agents)}개의 에이전트가 등록되어 있습니다.",
        agents=[a.model_dump() for a in agents]
    )


@router.post("/registry/register")
async def register_agent(request: A2ARegisterRequest) -> A2ARegistryResponse:
    """A2A 서버 URL에서 에이전트를 레지스트리에 등록"""
    registry = get_registry()
    agent = await registry.register_from_url(request.url)

    if agent:
        return A2ARegistryResponse(
            status=True,
            message=f"'{agent.display_name}' 에이전트가 등록되었습니다.",
            agents=[agent.model_dump()]
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="에이전트를 등록할 수 없습니다. URL을 확인해주세요."
        )


@router.delete("/registry/{name}")
async def unregister_agent(name: str) -> A2ARegistryResponse:
    """에이전트 등록 해제"""
    registry = get_registry()
    if registry.unregister_agent(name):
        return A2ARegistryResponse(
            status=True,
            message=f"'{name}' 에이전트가 등록 해제되었습니다.",
            agents=[]
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"'{name}' 에이전트를 찾을 수 없습니다."
        )


@router.get("/registry/{name}/component")
async def get_agent_component(name: str) -> A2AAgentConfigResponse:
    """에이전트의 ComponentModel 가져오기 (팀에 추가용)"""
    registry = get_registry()
    component = registry.get_agent_component_config(name)

    if component:
        return A2AAgentConfigResponse(
            status=True,
            message=f"'{name}' 에이전트 컴포넌트를 가져왔습니다.",
            component=component
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"'{name}' 에이전트를 찾을 수 없습니다."
        )


@router.post("/registry/check-all")
async def check_all_agents_status() -> A2ARegistryResponse:
    """모든 에이전트 온라인 상태 확인"""
    registry = get_registry()
    status_map = await registry.check_all_status()  # 상태 맵 가져오기
    agents = registry.list_agents()

    # 상태 맵으로 에이전트 상태 업데이트 (자동 스캔 에이전트 포함)
    for agent in agents:
        if agent.name in status_map:
            agent.is_online = status_map[agent.name]

    online_count = sum(1 for a in agents if a.is_online)
    return A2ARegistryResponse(
        status=True,
        message=f"{online_count}/{len(agents)} 에이전트가 온라인입니다.",
        agents=[a.model_dump() for a in agents]
    )


@router.get("/check")
async def check_a2a_server(url: str) -> dict:
    """A2A 서버 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Agent Card URL 시도
            if not url.endswith('/.well-known/agent.json'):
                agent_card_url = url.rstrip('/') + '/.well-known/agent.json'
            else:
                agent_card_url = url

            response = await client.get(agent_card_url)
            response.raise_for_status()
            card = response.json()

            return {
                "status": True,
                "message": "A2A 서버가 정상 동작 중입니다.",
                "agent_name": card.get('name', 'Unknown'),
                "agent_card_url": agent_card_url
            }
    except Exception as e:
        return {
            "status": False,
            "message": f"A2A 서버에 연결할 수 없습니다: {str(e)}",
            "agent_name": None,
            "agent_card_url": None
        }

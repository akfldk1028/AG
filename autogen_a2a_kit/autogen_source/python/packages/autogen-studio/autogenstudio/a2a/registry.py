# A2A Agent Registry - 에이전트 등록/관리
"""
A2A 에이전트 레지스트리 시스템.
등록된 에이전트를 이름으로 빠르게 찾아서 팀에 추가할 수 있습니다.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field


class RegisteredAgent(BaseModel):
    """등록된 A2A 에이전트 정보"""
    name: str = Field(description="에이전트 이름 (고유 식별자)")
    display_name: str = Field(description="표시 이름")
    url: str = Field(description="A2A 서버 URL")
    description: str = Field(default="", description="에이전트 설명")
    skills: List[dict] = Field(default_factory=list, description="스킬 목록")
    registered_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_checked: Optional[str] = Field(default=None, description="마지막 상태 확인 시간")
    is_online: bool = Field(default=False, description="온라인 상태")


class A2ARegistry:
    """
    A2A 에이전트 레지스트리.

    에이전트를 JSON 파일로 관리하며, 이름으로 빠르게 조회/추가할 수 있습니다.

    파일 구조:
        .autogenstudio/a2a_registry/
        ├── prime_checker.json
        ├── math_agent.json
        └── ...
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self._base_dir = Path(base_dir)
        else:
            # 기본 경로: ~/.autogenstudio/a2a_registry/
            self._base_dir = Path.home() / ".autogenstudio" / "a2a_registry"

        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _get_agent_path(self, name: str) -> Path:
        """에이전트 파일 경로"""
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        return self._base_dir / f"{safe_name}.json"

    def list_agents(self) -> List[RegisteredAgent]:
        """등록된 모든 에이전트 목록"""
        agents = []
        for file in self._base_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    agents.append(RegisteredAgent(**data))
            except Exception as e:
                print(f"Failed to load {file}: {e}")
        return agents

    def get_agent(self, name: str) -> Optional[RegisteredAgent]:
        """이름으로 에이전트 조회"""
        path = self._get_agent_path(name)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RegisteredAgent(**data)
        return None

    def register_agent(self, agent: RegisteredAgent) -> bool:
        """에이전트 등록"""
        try:
            path = self._get_agent_path(agent.name)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(agent.model_dump(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to register agent: {e}")
            return False

    def unregister_agent(self, name: str) -> bool:
        """에이전트 등록 해제"""
        path = self._get_agent_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    async def register_from_url(self, url: str) -> Optional[RegisteredAgent]:
        """URL에서 Agent Card를 가져와 등록"""
        try:
            # Agent Card URL 구성
            if not url.endswith("/.well-known/agent.json"):
                agent_card_url = url.rstrip("/") + "/.well-known/agent.json"
            else:
                agent_card_url = url

            # Agent Card 가져오기
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(agent_card_url)
                response.raise_for_status()
                card = response.json()

            # 기본 URL 추출
            base_url = url.replace("/.well-known/agent.json", "").rstrip("/")

            # 에이전트 정보 생성
            agent = RegisteredAgent(
                name=card.get("name", "unknown").replace(" ", "_").lower(),
                display_name=card.get("name", "Unknown Agent"),
                url=base_url,
                description=card.get("description", ""),
                skills=card.get("skills", []),
                is_online=True,
                last_checked=datetime.now().isoformat()
            )

            # 등록
            self.register_agent(agent)
            return agent

        except Exception as e:
            print(f"Failed to register from URL: {e}")
            return None

    async def check_agent_status(self, name: str) -> bool:
        """에이전트 온라인 상태 확인"""
        agent = self.get_agent(name)
        if not agent:
            return False

        try:
            agent_card_url = agent.url.rstrip("/") + "/.well-known/agent.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(agent_card_url)
                is_online = response.status_code == 200

            # 상태 업데이트
            agent.is_online = is_online
            agent.last_checked = datetime.now().isoformat()
            self.register_agent(agent)

            return is_online
        except:
            # 오프라인으로 표시
            agent.is_online = False
            agent.last_checked = datetime.now().isoformat()
            self.register_agent(agent)
            return False

    async def check_all_status(self) -> Dict[str, bool]:
        """모든 에이전트 상태 확인"""
        results = {}
        for agent in self.list_agents():
            results[agent.name] = await self.check_agent_status(agent.name)
        return results

    def get_agent_component_config(self, name: str) -> Optional[dict]:
        """에이전트를 ComponentModel config로 변환"""
        agent = self.get_agent(name)
        if not agent:
            return None

        return {
            "provider": "autogenstudio.a2a.A2AAgent",
            "component_type": "agent",
            "version": 1,
            "description": agent.description,
            "label": agent.display_name,
            "config": {
                "name": agent.name,
                "a2a_server_url": agent.url,
                "description": agent.description,
                "timeout": 60,
                "skills": agent.skills
            }
        }

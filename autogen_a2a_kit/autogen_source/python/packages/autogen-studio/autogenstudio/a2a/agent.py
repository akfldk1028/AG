# A2A Agent - AutoGen 팀에 직접 참여 가능한 A2A 프로토콜 에이전트
"""
A2A (Agent-to-Agent) 프로토콜을 통해 외부 에이전트와 통신하는 래퍼 에이전트.
AutoGen의 팀에 직접 에이전트로 추가할 수 있습니다.
"""
import logging
import uuid
from typing import Any, AsyncGenerator, List, Mapping, Optional, Sequence

import httpx
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    AgentEvent,
    ChatMessage,
    TextMessage,
)
from autogen_core import CancellationToken, Component, ComponentModel
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class A2AAgentConfig(BaseModel):
    """A2A Agent 설정"""
    name: str = Field(description="에이전트 이름")
    a2a_server_url: str = Field(description="A2A 서버 URL (예: http://localhost:8002)")
    description: str = Field(default="A2A 프로토콜 에이전트", description="에이전트 설명")
    timeout: int = Field(default=60, description="요청 타임아웃 (초)")
    skills: List[dict] = Field(default_factory=list, description="에이전트 스킬 목록")


class A2AAgent(BaseChatAgent, Component[A2AAgentConfig]):
    """
    A2A 프로토콜을 통해 외부 에이전트와 통신하는 에이전트.

    AutoGen 팀에 직접 참여 가능하며, 다른 에이전트와 동일하게 동작합니다.

    예시:
        ```python
        a2a_agent = A2AAgent(
            name="prime_checker",
            a2a_server_url="http://localhost:8002",
            description="소수 판별 에이전트"
        )

        team = RoundRobinGroupChat(
            participants=[assistant, a2a_agent],
            termination_condition=termination
        )
        ```
    """

    component_type = "agent"
    component_config_schema = A2AAgentConfig
    component_provider_override = "autogenstudio.a2a.A2AAgent"

    def __init__(
        self,
        name: str,
        a2a_server_url: str,
        description: str = "A2A 프로토콜 에이전트",
        timeout: int = 60,
        skills: Optional[List[dict]] = None,
    ):
        super().__init__(name=name, description=description)
        self._a2a_server_url = a2a_server_url.rstrip('/')
        self._timeout = timeout
        self._skills = skills or []
        self._session_id = str(uuid.uuid4())
        # 마지막 컨텍스트 저장 (빈 메시지 문제 해결)
        self._last_query: Optional[str] = None
        self._message_history: List[str] = []

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        """이 에이전트가 생성하는 메시지 타입"""
        return [TextMessage]

    async def _call_a2a(self, query: str) -> str:
        """A2A 프로토콜로 외부 에이전트 호출"""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{"type": "text", "text": query}]
                }
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._a2a_server_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                result = response.json()

                # 응답에서 텍스트 추출 - 여러 형식 지원
                if "result" in result:
                    res = result["result"]

                    # 형식 1: artifacts (표준 A2A 응답)
                    if "artifacts" in res:
                        for artifact in res["artifacts"]:
                            for part in artifact.get("parts", []):
                                if "text" in part:
                                    return part["text"]

                    # 형식 2: status.message (Google ADK 응답 형식)
                    # 에이전트 응답은 history가 아닌 status.message에 있음!
                    if "status" in res and "message" in res["status"]:
                        status_msg = res["status"]["message"]
                        for part in status_msg.get("parts", []):
                            text = part.get("text")
                            if text:
                                return text

                    # 형식 3: history (대화 기록 형식 - fallback)
                    if "history" in res:
                        # 마지막 assistant/agent 메시지에서 텍스트 추출 (user 제외)
                        for msg in reversed(res["history"]):
                            role = msg.get("role", "")
                            # user가 아닌 응답만 처리 (agent, assistant 등)
                            if role and role != "user":
                                for part in msg.get("parts", []):
                                    text = part.get("text")
                                    if text:
                                        return text

                if "error" in result:
                    return f"A2A 에러: {result['error']}"

                return str(result)

        except httpx.TimeoutException:
            return f"A2A 호출 타임아웃 ({self._timeout}초)"
        except Exception as e:
            return f"A2A 호출 실패: {str(e)}"

    async def on_messages(
        self,
        messages: Sequence[ChatMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        """메시지 처리 - 마지막 메시지를 A2A 서버로 전달"""
        # 마지막 메시지 추출
        if not messages:
            # 메시지가 없으면 마지막 컨텍스트 사용 시도
            if self._last_query:
                logger.info(
                    f"A2AAgent '{self.name}' received empty messages - using last context: '{self._last_query[:50]}...'"
                )
                # 마지막 쿼리로 A2A 호출 (같은 쿼리에 대한 추가 정보 요청)
                response_text = await self._call_a2a(
                    f"이전 질문에 대해 추가 정보가 있나요? (이전 질문: {self._last_query})"
                )
            else:
                logger.warning(
                    f"A2AAgent '{self.name}' received empty messages and no context - returning pass"
                )
                return Response(
                    chat_message=TextMessage(
                        content=f"[{self.name}] 컨텍스트가 없어 대기 중입니다.",
                        source=self.name
                    )
                )
        else:
            last_message = messages[-1]

            # 메시지 내용 추출
            if isinstance(last_message, TextMessage):
                query = last_message.content
            else:
                query = str(last_message)

            # 컨텍스트 저장
            self._last_query = query
            self._message_history.append(query)
            if len(self._message_history) > 10:  # 최대 10개 메시지만 유지
                self._message_history = self._message_history[-10:]

            # A2A 호출
            response_text = await self._call_a2a(query)

        return Response(
            chat_message=TextMessage(
                content=response_text,
                source=self.name
            )
        )

    async def on_messages_stream(
        self,
        messages: Sequence[ChatMessage],
        cancellation_token: CancellationToken
    ) -> AsyncGenerator[AgentEvent | Response, None]:
        """스트리밍 메시지 처리"""
        # A2A는 현재 스트리밍을 지원하지 않으므로 일반 응답 사용
        response = await self.on_messages(messages, cancellation_token)
        yield response

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """에이전트 상태 리셋"""
        self._session_id = str(uuid.uuid4())
        self._last_query = None
        self._message_history.clear()

    async def save_state(self) -> Mapping[str, Any]:
        """에이전트 상태 저장"""
        return {
            "session_id": self._session_id,
            "last_query": self._last_query,
            "message_history": self._message_history.copy(),
        }

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """에이전트 상태 로드"""
        self._session_id = state.get("session_id", str(uuid.uuid4()))
        self._last_query = state.get("last_query")
        self._message_history = list(state.get("message_history", []))

    def _to_config(self) -> A2AAgentConfig:
        """설정으로 변환"""
        return A2AAgentConfig(
            name=self.name,
            a2a_server_url=self._a2a_server_url,
            description=self.description,
            timeout=self._timeout,
            skills=self._skills
        )

    def dump_component(self) -> ComponentModel:
        """ComponentModel로 변환 (AutoGen Studio 호환)"""
        return ComponentModel(
            provider=self.component_provider_override,
            component_type=self.component_type,
            version=1,
            description=self.description,
            label=self.name,
            config=self._to_config().model_dump()
        )

    @classmethod
    def _from_config(cls, config: A2AAgentConfig) -> "A2AAgent":
        """A2AAgentConfig에서 인스턴스 생성 (Component 시스템 요구사항)"""
        return cls(
            name=config.name,
            a2a_server_url=config.a2a_server_url,
            description=config.description,
            timeout=config.timeout,
            skills=config.skills
        )

    @classmethod
    def load_component(cls, component: ComponentModel) -> "A2AAgent":
        """ComponentModel에서 로드"""
        config = A2AAgentConfig(**component.config)
        return cls._from_config(config)

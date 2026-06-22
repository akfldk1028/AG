# -*- coding: utf-8 -*-
"""
A2A Client — official a2a-sdk v1.0 based.

Provides both async (call_a2a_async) and sync (call_a2a) interfaces.
Backwards-compatible: create_a2a_tool and check_server still work.
"""

import asyncio
import logging
from typing import Callable

from a2a.client import (
    A2ACardResolver,
    ClientConfig,
    ClientFactory,
    create_text_message_object,
)
from a2a.types import (
    Role,
    SendMessageRequest,
)

logger = logging.getLogger(__name__)


async def call_a2a_async(
    query: str,
    url: str = "http://localhost:8011/a2a",
    timeout: int = 30,
) -> str:
    """Send a message to an A2A server and return the response text.

    Args:
        query: The question/request to send.
        url: Base URL of the A2A server (must serve agent-card and JSON-RPC).
        timeout: Request timeout in seconds.

    Returns:
        Agent's response text, or an error string.
    """
    try:
        # Resolve agent card
        resolver = A2ACardResolver(url)
        card = await resolver.get_agent_card()

        # Create client
        config = ClientConfig()
        factory = ClientFactory(config=config)
        client = factory.create(card)

        # Build message
        user_msg = create_text_message_object(role=Role.ROLE_USER, content=query)
        request = SendMessageRequest(message=user_msg)

        # Send and collect response
        parts_text = []
        async for stream_resp, task in client.send_message(request):
            # Extract text from streaming response parts
            if stream_resp and stream_resp.HasField("message"):
                for part in stream_resp.message.parts:
                    if part.text:
                        parts_text.append(part.text)
            if task and task.artifacts:
                for artifact in task.artifacts:
                    for part in artifact.parts:
                        if part.text:
                            parts_text.append(part.text)

        await client.close()
        return "\n".join(parts_text) if parts_text else "(empty response)"

    except Exception as e:
        logger.error("A2A call failed: %s", e)
        return f"[Error] {e}"


def call_a2a(
    query: str,
    url: str = "http://localhost:8011/a2a",
    timeout: int = 30,
) -> str:
    """Synchronous wrapper around call_a2a_async.

    Works in both sync and async contexts.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an event loop — run in a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, call_a2a_async(query, url, timeout)
            ).result(timeout=timeout + 5)
    else:
        return asyncio.run(call_a2a_async(query, url, timeout))


def create_a2a_tool(
    url: str = "http://localhost:8011/a2a",
    name: str = "call_remote_agent",
) -> Callable:
    """Create an AutoGen-compatible tool function for A2A calls."""
    def tool_func(query: str) -> str:
        """원격 A2A 에이전트에게 질문합니다."""
        print(f"    [A2A] -> {url}")
        result = call_a2a(query, url)
        print(f"    [A2A] <- Response received")
        return result

    tool_func.__name__ = name
    tool_func.__doc__ = f"A2A 프로토콜로 {url}의 원격 에이전트를 호출합니다."
    return tool_func


async def check_server_async(url: str = "http://localhost:8011/a2a") -> dict:
    """Check if an A2A server is available by resolving its agent card."""
    try:
        resolver = A2ACardResolver(url)
        card = await resolver.get_agent_card()
        return {
            "available": True,
            "name": card.name,
            "description": card.description,
        }
    except Exception:
        return {"available": False, "name": None, "description": None}


def check_server(url: str = "http://localhost:8011/a2a") -> dict:
    """Synchronous wrapper around check_server_async."""
    try:
        return asyncio.run(check_server_async(url))
    except Exception:
        return {"available": False, "name": None, "description": None}

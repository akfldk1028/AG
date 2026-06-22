# ACE MCP Server - AutoGen Studio Full Feature Parity
# Wraps ALL AutoGen Studio HTTP API + WebSocket execution as MCP tools
"""
MCP server that exposes AutoGen Studio as tools for Claude Code,
Claude Desktop, and other MCP-compatible clients.

58 tools covering:
- Execution (3): execute_team, stream_team, execute_in_session
- Team CRUD (5): list/get/create/update/delete
- Session CRUD (4): list/create/delete + get_session_runs
- Gallery CRUD (5): list/create/update/delete/sync
- A2A Agents (4): list/register/unregister/health_check
- Validation (2): validate_component, test_component
- Settings (2): get/update
- Utility (2): health_check, get_version
- Message Bus (5): send_message, broadcast, get_log, get_conversation, get_bus_status
- SharedMemory (12): store/get/get_all decisions, publish/get events,
                     api_spec, schema, acquire/release/list locks
- Patterns (3): list_patterns, get_pattern_template, create_team_from_pattern
- Law Search (4): law_search, law_search_domain, law_domains, law_health
- ARR Backend (2): arr_law_search (logged), arr_law_health
- Land Regulation (5): arr_land_analyze, arr_land_agent_analyze, arr_land_resolve, arr_land_zones, arr_land_stats

Usage:
    # stdio mode (Claude Desktop / Claude Code)
    python autogen_studio_server.py

    # streamable-http mode (remote access)
    python autogen_studio_server.py --transport streamable-http --port 8200

Environment variables (all with defaults):
    AUTOGEN_STUDIO_URL  = http://localhost:8081
    AUTOGEN_STUDIO_USER = guestuser@gmail.com
    MESSAGE_BUS_URL     = http://localhost:8100
    SHARED_MEMORY_URL   = http://localhost:8101
    LAW_BACKEND_URL     = http://localhost:8011
    ARR_BACKEND_URL     = http://localhost:8000
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any

from pathlib import Path

import httpx
import websockets

from mcp.server.fastmcp import FastMCP, Context

# JSON_MODULES base path (for pattern templates)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # -> 25_ACE/
_JSON_MODULES = _PROJECT_ROOT / "JSON_MODULES"

# --------------- Config ---------------

AUTOGEN_STUDIO_URL = os.environ.get("AUTOGEN_STUDIO_URL", "http://localhost:8081")
AUTOGEN_STUDIO_USER = os.environ.get("AUTOGEN_STUDIO_USER", "guestuser@gmail.com")
MESSAGE_BUS_URL = os.environ.get("MESSAGE_BUS_URL", "http://localhost:8100")
SHARED_MEMORY_URL = os.environ.get("SHARED_MEMORY_URL", "http://localhost:8101")
LAW_BACKEND_URL = os.environ.get("LAW_BACKEND_URL", "http://localhost:8011")
ARR_BACKEND_URL = os.environ.get("ARR_BACKEND_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("ace-mcp")

# --------------- Lifespan (shared httpx client) ---------------


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Shared httpx.AsyncClient for the server lifetime."""
    async with httpx.AsyncClient(
        base_url=AUTOGEN_STUDIO_URL,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={"Content-Type": "application/json"},
    ) as client:
        yield {"http": client}


mcp = FastMCP(
    "ACE",
    instructions=(
        "ACE MCP server - full AutoGen Studio API + AG-CLI collaboration. "
        "57 tools: team execution (WS streaming + RunSummary), CRUD, "
        "Message Bus conversations, SharedMemory events/decisions/locks, "
        "A2A agents, validation, settings, team pattern templates, "
        "law article search (Korean legal regulations via Neo4j), "
        "and land regulation analysis (건폐율/용적률/건축제한)."
    ),
    lifespan=server_lifespan,
)

# --------------- Pattern Definitions (matches frontend agentflow/types.ts) ---------------

PATTERN_DEFINITIONS = {
    "sequential": {
        "id": "sequential",
        "name": "Sequential",
        "description": "Agents take turns in fixed order (A -> B -> C)",
        "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
        "layout": "chain",
        "template_file": "sequential_team.json",
    },
    "selector": {
        "id": "selector",
        "name": "Selector",
        "description": "Central LLM selects best agent per turn",
        "provider": "autogen_agentchat.teams.SelectorGroupChat",
        "layout": "hub-spoke",
        "template_file": "selector_team.json",
    },
    "handoff": {
        "id": "handoff",
        "name": "Handoff (Swarm)",
        "description": "Agents dynamically transfer control via handoff tools",
        "provider": "autogen_agentchat.teams.Swarm",
        "layout": "mesh",
        "template_file": "handoff_team.json",
    },
    "debate": {
        "id": "debate",
        "name": "Debate",
        "description": "Agents argue different perspectives, judge decides",
        "provider": "autogen_agentchat.teams.SelectorGroupChat",
        "layout": "ring",
        "template_file": "debate_team.json",
    },
    "reflection": {
        "id": "reflection",
        "name": "Reflection",
        "description": "Generator creates, critic reviews iteratively",
        "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
        "layout": "chain",
        "template_file": "reflection_team.json",
    },
}

# --------------- Helpers ---------------


async def _get_http(ctx: Context) -> httpx.AsyncClient:
    """Retrieve httpx client from lifespan state."""
    return ctx.request_context.lifespan_context["http"]


async def _call_api(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> Any:
    """Call AutoGen Studio API and unwrap the {status, data} envelope."""
    resp = await client.request(method, path, params=params, json=json_body)
    resp.raise_for_status()
    body = resp.json()
    # AutoGen Studio wraps: {status: bool, data: T, message?: str}
    if isinstance(body, dict) and "status" in body and "data" in body:
        if not body["status"]:
            raise RuntimeError(body.get("message", "API error"))
        return body["data"]
    return body


async def _resolve_team(
    client: httpx.AsyncClient, team_name_or_id: str
) -> dict[str, Any]:
    """Resolve a team by numeric ID, label, or provider substring."""
    if team_name_or_id.isdigit():
        try:
            return await _call_api(
                client, "GET", f"/api/teams/{team_name_or_id}",
                params={"user_id": AUTOGEN_STUDIO_USER},
            )
        except (httpx.HTTPStatusError, RuntimeError):
            pass

    teams = await _call_api(
        client, "GET", "/api/teams/", params={"user_id": AUTOGEN_STUDIO_USER}
    )
    if not isinstance(teams, list):
        raise RuntimeError("Unexpected response from /api/teams/")

    needle = team_name_or_id.lower()
    # Exact match first
    for team in teams:
        comp = team.get("component") or {}
        label = (comp.get("label") or "").lower()
        provider = (comp.get("provider") or "").lower()
        if label == needle or provider == needle:
            return team
    # Partial match
    for team in teams:
        comp = team.get("component") or {}
        label = (comp.get("label") or "").lower()
        provider = (comp.get("provider") or "").lower()
        if needle in label or needle in provider:
            return team

    raise RuntimeError(
        f"Team not found: '{team_name_or_id}'. "
        f"Available: {[t.get('component', {}).get('label', '?') for t in teams]}"
    )


def _dumps(obj: Any) -> str:
    """JSON serialize with Korean support."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


# --------------- WebSocket Execution (Full Feature Parity) ---------------


async def _execute_via_ws(
    client: httpx.AsyncClient,
    team_id: int,
    task: str,
    *,
    session_id: int | None = None,
    timeout: int = 300,
    files: list[dict[str, str]] | None = None,
    team_config: dict | None = None,
    on_message: Any = None,
) -> dict[str, Any]:
    """Execute a team via WebSocket - replicates frontend ws.ts + executionStore.ts.

    Collects ALL message types:
    - message: agent text messages (source, content, models_usage)
    - message_chunk: streaming text (accumulated per source)
    - llm_call_event: LLM API calls with token usage
    - input_request: auto-responded in headless mode
    - completion/result: execution finished with RunSummary
    - error: execution failed

    Returns full result with RunSummary matching frontend RunSummaryCard.
    """
    t0 = time.monotonic()

    # 1. Create or reuse session
    if session_id is None:
        session = await _call_api(
            client, "POST", "/api/sessions/",
            json_body={"team_id": team_id, "user_id": AUTOGEN_STUDIO_USER},
        )
        session_id = session.get("id") if isinstance(session, dict) else session

    # 2. Create run
    run = await _call_api(
        client, "POST", "/api/runs/",
        json_body={"session_id": session_id, "user_id": AUTOGEN_STUDIO_USER},
    )
    run_id = run.get("run_id") if isinstance(run, dict) else run

    # 3. Connect WebSocket
    base = AUTOGEN_STUDIO_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{base}/api/ws/runs/{run_id}"

    # Collection state (matches frontend executionStore)
    agent_messages: list[dict[str, Any]] = []
    llm_events: list[dict[str, Any]] = []
    streaming_chunks: str = ""
    streaming_source: str | None = None
    completion_data: dict[str, Any] | None = None

    async def _ws_session():
        nonlocal completion_data, streaming_chunks, streaming_source
        async with websockets.connect(ws_url) as ws:
            # Send start (matches frontend ExecutionWebSocket.startExecution)
            await ws.send(json.dumps({
                "type": "start",
                "task": task,
                "files": files or [],
                "team_config": team_config,
            }, ensure_ascii=False))

            # Ping keepalive
            async def _ping():
                while True:
                    await asyncio.sleep(30)
                    try:
                        await ws.send(json.dumps({"type": "ping"}))
                    except Exception:
                        break

            ping_task = asyncio.create_task(_ping())

            try:
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    msg_type = msg.get("type", "")
                    data = msg.get("data") or {}

                    # --- message_chunk: streaming text accumulation ---
                    if msg_type == "message_chunk":
                        if isinstance(data, dict):
                            chunk_content = data.get("content", "")
                            chunk_source = data.get("source", streaming_source or "agent")
                        else:
                            chunk_content = msg.get("content", "")
                            chunk_source = msg.get("source", streaming_source or "agent")
                        streaming_chunks += chunk_content
                        streaming_source = chunk_source

                    # --- llm_call_event: LLM API call with token usage ---
                    elif msg_type == "llm_call_event" and data:
                        response = data.get("response", {}) if isinstance(data, dict) else {}
                        usage = response.get("usage", {}) if isinstance(response, dict) else {}
                        llm_events.append({
                            "model": response.get("model", ""),
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "raw": data,
                        })

                    # --- message: complete agent message ---
                    elif msg_type == "message":
                        if isinstance(data, dict) and data.get("source") and data.get("content"):
                            usage = data.get("models_usage") or {}
                            source = data["source"]
                            msg_entry = {
                                "source": source,
                                "content": data["content"],
                                "timestamp": msg.get("timestamp", ""),
                                "message_type": (
                                    "user" if source == "user"
                                    else "llm_event" if "llm_call" in source
                                    else "agent"
                                ),
                                "tokens_in": usage.get("prompt_tokens"),
                                "tokens_out": usage.get("completion_tokens"),
                            }
                            agent_messages.append(msg_entry)

                            # Flush any accumulated streaming chunks
                            if streaming_chunks:
                                streaming_chunks = ""
                                streaming_source = None

                            if on_message:
                                if asyncio.iscoroutinefunction(on_message):
                                    await on_message(msg_entry)
                                else:
                                    on_message(msg_entry)

                    # --- input_request: headless auto-respond ---
                    elif msg_type == "input_request":
                        prompt = ""
                        source = ""
                        if isinstance(data, dict):
                            prompt = data.get("prompt", "Please provide input")
                            source = data.get("source", "agent")
                        agent_messages.append({
                            "source": source or "system",
                            "content": f"[Input requested: {prompt}] Auto-responded: continue",
                            "timestamp": msg.get("timestamp", ""),
                            "message_type": "system",
                            "tokens_in": None,
                            "tokens_out": None,
                        })
                        await ws.send(json.dumps({
                            "type": "input_response",
                            "response": "continue",
                        }))

                    # --- completion / result ---
                    elif msg_type in ("completion", "result"):
                        completion_data = data if isinstance(data, dict) else msg
                        break

                    # --- error ---
                    elif msg_type == "error":
                        raise RuntimeError(msg.get("error", "Unknown execution error"))

            finally:
                ping_task.cancel()

    await asyncio.wait_for(_ws_session(), timeout=timeout)

    duration = time.monotonic() - t0

    # --- Compute RunSummary (matches frontend executionStore completion handler) ---
    task_result = {}
    if isinstance(completion_data, dict):
        task_result = completion_data.get("task_result", {})
        if not isinstance(task_result, dict):
            task_result = {}

    stop_reason = task_result.get("stop_reason")
    server_duration = completion_data.get("duration") if isinstance(completion_data, dict) else None

    agent_turns = [m for m in agent_messages if m.get("message_type") == "agent"]
    last_agent = agent_turns[-1]["source"] if agent_turns else None

    total_tokens_in = 0
    total_tokens_out = 0
    for m in agent_messages:
        total_tokens_in += m.get("tokens_in") or 0
        total_tokens_out += m.get("tokens_out") or 0
    for e in llm_events:
        total_tokens_in += e.get("prompt_tokens", 0)
        total_tokens_out += e.get("completion_tokens", 0)

    run_summary = {
        "stop_reason": stop_reason,
        "duration": server_duration if server_duration is not None else round(duration, 2),
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_tokens": total_tokens_in + total_tokens_out,
        "turn_count": len(agent_messages),
        "agent_turn_count": len(agent_turns),
        "llm_call_count": len(llm_events),
        "terminated_by": last_agent,
    }

    return {
        "session_id": session_id,
        "run_id": run_id,
        "messages": agent_messages,
        "llm_events": llm_events,
        "run_summary": run_summary,
        "result": completion_data,
    }


# ===============================================================
# MCP Tools (47 tools)
# ===============================================================

# --------------- 1. Core Execution (3) ---------------


@mcp.tool()
async def execute_team(
    team_name_or_id: str,
    task: str,
    timeout: int = 300,
    files_json: str = "[]",
    ctx: Context = None,
) -> str:
    """Execute an AutoGen Studio team and return full result with RunSummary.

    Args:
        team_name_or_id: Team numeric ID, label, or provider name
        task: The task/prompt to send to the team
        timeout: Max seconds to wait (default 300)
        files_json: JSON array of file attachments [{name, type, content(base64)}]

    Returns:
        JSON with session_id, run_id, messages, llm_events, run_summary, result.
        run_summary includes: stop_reason, duration, total_tokens_in/out,
        turn_count, agent_turn_count, llm_call_count, terminated_by.
    """
    client = await _get_http(ctx)
    team = await _resolve_team(client, team_name_or_id)
    team_id = team["id"]
    files = json.loads(files_json) if files_json and files_json != "[]" else None
    label = team.get("component", {}).get("label", "?")
    logger.info(f"execute_team {team_id} ({label}): {task[:80]}")
    output = await _execute_via_ws(client, team_id, task, timeout=timeout, files=files)
    return _dumps(output)


@mcp.tool()
async def stream_team(
    team_name_or_id: str,
    task: str,
    files_json: str = "[]",
    ctx: Context = None,
) -> str:
    """Execute a team with progress reporting for each agent message.

    Args:
        team_name_or_id: Team numeric ID, label, or provider name
        task: The task/prompt to send to the team
        files_json: JSON array of file attachments [{name, type, content(base64)}]

    Returns:
        Same as execute_team (messages, llm_events, run_summary, result)
    """
    client = await _get_http(ctx)
    team = await _resolve_team(client, team_name_or_id)
    team_id = team["id"]
    files = json.loads(files_json) if files_json and files_json != "[]" else None
    label = team.get("component", {}).get("label", "?")
    logger.info(f"stream_team {team_id} ({label}): {task[:80]}")

    msg_count = [0]

    async def on_msg(msg_entry: dict):
        msg_count[0] += 1
        source = msg_entry.get("source", "?")
        content_preview = str(msg_entry.get("content", ""))[:60]
        try:
            await ctx.report_progress(msg_count[0], 0)
        except Exception:
            pass
        logger.info(f"  [{msg_count[0]}] {source}: {content_preview}")

    output = await _execute_via_ws(
        client, team_id, task, timeout=600, files=files, on_message=on_msg,
    )
    return _dumps(output)


@mcp.tool()
async def execute_in_session(
    session_id: int,
    task: str,
    team_name_or_id: str = "",
    timeout: int = 300,
    files_json: str = "[]",
    ctx: Context = None,
) -> str:
    """Execute a task in an existing session (continues conversation history).

    Args:
        session_id: Existing session ID to execute in
        task: The task/prompt to send
        team_name_or_id: Team (needed to look up team_id for the WS flow)
        timeout: Max seconds to wait
        files_json: JSON array of file attachments

    Returns:
        Same as execute_team (messages, llm_events, run_summary, result)
    """
    client = await _get_http(ctx)
    files = json.loads(files_json) if files_json and files_json != "[]" else None

    # Get team_id from session or from provided name
    if team_name_or_id:
        team = await _resolve_team(client, team_name_or_id)
        team_id = team["id"]
    else:
        # Fetch session to find team_id
        session = await _call_api(
            client, "GET", f"/api/sessions/{session_id}",
            params={"user_id": AUTOGEN_STUDIO_USER},
        )
        team_id = session.get("team_id")
        if not team_id:
            raise RuntimeError(f"Session {session_id} has no team_id")

    logger.info(f"execute_in_session {session_id} (team {team_id}): {task[:80]}")
    output = await _execute_via_ws(
        client, team_id, task,
        session_id=session_id, timeout=timeout, files=files,
    )
    return _dumps(output)


# --------------- 2. Team CRUD (5) ---------------


@mcp.tool()
async def list_teams(ctx: Context = None) -> str:
    """List all available AutoGen Studio teams.

    Returns:
        JSON array of teams with id, label, provider, team_type, participants count
    """
    client = await _get_http(ctx)
    teams = await _call_api(
        client, "GET", "/api/teams/", params={"user_id": AUTOGEN_STUDIO_USER}
    )
    summary = []
    for t in teams:
        comp = t.get("component") or {}
        config = comp.get("config") or {}
        summary.append({
            "id": t.get("id"),
            "label": comp.get("label", ""),
            "provider": comp.get("provider", ""),
            "team_type": config.get("team_type", ""),
            "participants": len(config.get("participants", [])),
        })
    return _dumps(summary)


@mcp.tool()
async def get_team(team_name_or_id: str, ctx: Context = None) -> str:
    """Get full team configuration by ID, label, or provider name.

    Args:
        team_name_or_id: Team numeric ID, label, or provider name

    Returns:
        Full team JSON including component config with all participants
    """
    client = await _get_http(ctx)
    team = await _resolve_team(client, team_name_or_id)
    return _dumps(team)


@mcp.tool()
async def create_team(component_json: str, ctx: Context = None) -> str:
    """Create a new team from a JSON component definition.

    Args:
        component_json: Full team component JSON string

    Returns:
        Created team with id
    """
    client = await _get_http(ctx)
    component = json.loads(component_json)
    result = await _call_api(
        client, "POST", "/api/teams/",
        json_body={"user_id": AUTOGEN_STUDIO_USER, "component": component},
    )
    return _dumps(result)


@mcp.tool()
async def update_team(team_id: int, component_json: str, ctx: Context = None) -> str:
    """Update an existing team (POST upsert with id in body).

    Args:
        team_id: Team numeric ID
        component_json: Updated team component JSON string

    Returns:
        Updated team
    """
    client = await _get_http(ctx)
    component = json.loads(component_json)
    # AutoGen Studio uses POST upsert (not PUT) with id in body
    result = await _call_api(
        client, "POST", "/api/teams/",
        json_body={"id": team_id, "user_id": AUTOGEN_STUDIO_USER, "component": component},
    )
    return _dumps(result)


@mcp.tool()
async def delete_team(team_id: int, ctx: Context = None) -> str:
    """Delete a team.

    Args:
        team_id: Team numeric ID

    Returns:
        Deletion confirmation
    """
    client = await _get_http(ctx)
    await _call_api(
        client, "DELETE", f"/api/teams/{team_id}",
        params={"user_id": AUTOGEN_STUDIO_USER},
    )
    return _dumps({"deleted": True, "team_id": team_id})


# --------------- 3. Session CRUD (4) ---------------


@mcp.tool()
async def list_sessions(ctx: Context = None) -> str:
    """List all sessions.

    Returns:
        JSON array of sessions with id, team_id, name, created_at
    """
    client = await _get_http(ctx)
    sessions = await _call_api(
        client, "GET", "/api/sessions/", params={"user_id": AUTOGEN_STUDIO_USER}
    )
    return _dumps(sessions)


@mcp.tool()
async def create_session(team_id: int, name: str = "", ctx: Context = None) -> str:
    """Create a new session for a team.

    Args:
        team_id: Team numeric ID to create session for
        name: Optional session name

    Returns:
        Created session with id
    """
    client = await _get_http(ctx)
    body: dict[str, Any] = {"team_id": team_id, "user_id": AUTOGEN_STUDIO_USER}
    if name:
        body["name"] = name
    result = await _call_api(client, "POST", "/api/sessions/", json_body=body)
    return _dumps(result)


@mcp.tool()
async def get_session_runs(session_id: int, ctx: Context = None) -> str:
    """Get all runs and messages for a session.

    Args:
        session_id: Session numeric ID

    Returns:
        JSON with runs array containing messages
    """
    client = await _get_http(ctx)
    runs = await _call_api(
        client, "GET", f"/api/sessions/{session_id}/runs",
        params={"user_id": AUTOGEN_STUDIO_USER},
    )
    return _dumps(runs)


@mcp.tool()
async def delete_session(session_id: int, ctx: Context = None) -> str:
    """Delete a session and all its runs.

    Args:
        session_id: Session numeric ID

    Returns:
        Deletion confirmation
    """
    client = await _get_http(ctx)
    await _call_api(
        client, "DELETE", f"/api/sessions/{session_id}",
        params={"user_id": AUTOGEN_STUDIO_USER},
    )
    return _dumps({"deleted": True, "session_id": session_id})


# --------------- 4. Gallery CRUD (5) ---------------


@mcp.tool()
async def list_gallery(ctx: Context = None) -> str:
    """List gallery items (pre-built component templates).

    Returns:
        JSON array of gallery items
    """
    client = await _get_http(ctx)
    gallery = await _call_api(
        client, "GET", "/api/gallery/", params={"user_id": AUTOGEN_STUDIO_USER}
    )
    return _dumps(gallery)


@mcp.tool()
async def create_gallery(gallery_json: str, ctx: Context = None) -> str:
    """Create a new gallery item.

    Args:
        gallery_json: Gallery item JSON string

    Returns:
        Created gallery item
    """
    client = await _get_http(ctx)
    data = json.loads(gallery_json)
    data["user_id"] = data.get("user_id", AUTOGEN_STUDIO_USER)
    result = await _call_api(client, "POST", "/api/gallery/", json_body=data)
    return _dumps(result)


@mcp.tool()
async def update_gallery(gallery_id: int, gallery_json: str, ctx: Context = None) -> str:
    """Update an existing gallery item.

    Args:
        gallery_id: Gallery item numeric ID
        gallery_json: Updated gallery JSON string

    Returns:
        Updated gallery item
    """
    client = await _get_http(ctx)
    data = json.loads(gallery_json)
    data["user_id"] = data.get("user_id", AUTOGEN_STUDIO_USER)
    result = await _call_api(
        client, "PUT", f"/api/gallery/{gallery_id}",
        params={"user_id": AUTOGEN_STUDIO_USER},
        json_body=data,
    )
    return _dumps(result)


@mcp.tool()
async def delete_gallery(gallery_id: int, ctx: Context = None) -> str:
    """Delete a gallery item.

    Args:
        gallery_id: Gallery item numeric ID

    Returns:
        Deletion confirmation
    """
    client = await _get_http(ctx)
    await _call_api(
        client, "DELETE", f"/api/gallery/{gallery_id}",
        params={"user_id": AUTOGEN_STUDIO_USER},
    )
    return _dumps({"deleted": True, "gallery_id": gallery_id})


@mcp.tool()
async def sync_gallery(url: str, ctx: Context = None) -> str:
    """Import a gallery from an external URL.

    Args:
        url: URL to fetch gallery JSON from

    Returns:
        Fetched gallery data
    """
    async with httpx.AsyncClient(timeout=30.0) as ext_client:
        resp = await ext_client.get(url)
        resp.raise_for_status()
        return _dumps(resp.json())


# --------------- 5. A2A Agent Management (4) ---------------


@mcp.tool()
async def list_a2a_agents(ctx: Context = None) -> str:
    """List all registered A2A agents.

    Returns:
        JSON with agents array (name, url, skills, is_online)
    """
    client = await _get_http(ctx)
    result = await _call_api(client, "GET", "/api/a2a/registry")
    return _dumps(result)


@mcp.tool()
async def register_a2a_agent(url: str, ctx: Context = None) -> str:
    """Register a new A2A agent by URL.

    Args:
        url: A2A agent server URL (e.g. http://localhost:8003)

    Returns:
        Registration confirmation
    """
    client = await _get_http(ctx)
    result = await _call_api(
        client, "POST", "/api/a2a/registry/register",
        json_body={"url": url},
    )
    return _dumps(result)


@mcp.tool()
async def unregister_a2a_agent(name: str, ctx: Context = None) -> str:
    """Unregister an A2A agent by name.

    Args:
        name: Agent name to unregister

    Returns:
        Unregistration confirmation
    """
    client = await _get_http(ctx)
    await _call_api(client, "DELETE", f"/api/a2a/registry/{name}")
    return _dumps({"unregistered": True, "name": name})


@mcp.tool()
async def check_a2a_health(ctx: Context = None) -> str:
    """Check health of all registered A2A agents.

    Returns:
        JSON with agents array including is_online/healthy status
    """
    client = await _get_http(ctx)
    result = await _call_api(client, "POST", "/api/a2a/registry/check-all")
    # Map is_online -> healthy for frontend compat
    if isinstance(result, dict) and "agents" in result:
        for agent in result["agents"]:
            if isinstance(agent, dict):
                agent["healthy"] = agent.get("healthy", agent.get("is_online", False))
    return _dumps(result)


# --------------- 6. Validation & Testing (2) ---------------


@mcp.tool()
async def validate_component(component_json: str, ctx: Context = None) -> str:
    """Validate a component definition (agent, model, tool, termination).

    Args:
        component_json: Component JSON string to validate

    Returns:
        JSON with is_valid, errors[], warnings[] (each with field, error, suggestion)
    """
    client = await _get_http(ctx)
    component = json.loads(component_json)
    result = await _call_api(
        client, "POST", "/api/validate/",
        json_body={"component": component},
    )
    return _dumps(result)


@mcp.tool()
async def test_component(component_json: str, timeout: int = 60, ctx: Context = None) -> str:
    """Functionally test a component (tries to instantiate and run it).

    Args:
        component_json: Component JSON string to test
        timeout: Test timeout in seconds (default 60)

    Returns:
        JSON with status (bool), message, logs[]
    """
    client = await _get_http(ctx)
    component = json.loads(component_json)
    result = await _call_api(
        client, "POST", "/api/validate/test",
        json_body={"component": component, "timeout": timeout},
    )
    return _dumps(result)


# --------------- 7. Settings (2) ---------------


@mcp.tool()
async def get_settings(ctx: Context = None) -> str:
    """Get current AutoGen Studio settings (environment, default model, UI config).

    Returns:
        JSON with environment variables, default_model_client, and UI settings
    """
    client = await _get_http(ctx)
    result = await _call_api(
        client, "GET", "/api/settings/", params={"user_id": AUTOGEN_STUDIO_USER}
    )
    return _dumps(result)


@mcp.tool()
async def update_settings(settings_json: str, ctx: Context = None) -> str:
    """Update AutoGen Studio settings.

    Args:
        settings_json: Settings JSON string with environment, default_model_client, ui

    Returns:
        Updated settings
    """
    client = await _get_http(ctx)
    settings = json.loads(settings_json)
    settings["user_id"] = settings.get("user_id", AUTOGEN_STUDIO_USER)
    result = await _call_api(
        client, "PUT", "/api/settings/", json_body=settings,
    )
    return _dumps(result)


# --------------- 8. Health & Version (2) ---------------


@mcp.tool()
async def health_check(ctx: Context = None) -> str:
    """Check AutoGen Studio health status.

    Returns:
        JSON with status (boolean) and message
    """
    client = await _get_http(ctx)
    resp = await client.get("/api/health")
    resp.raise_for_status()
    return json.dumps(resp.json(), ensure_ascii=False)


@mcp.tool()
async def get_version(ctx: Context = None) -> str:
    """Get AutoGen Studio version.

    Returns:
        JSON with version string
    """
    client = await _get_http(ctx)
    resp = await client.get("/api/version")
    resp.raise_for_status()
    return json.dumps(resp.json(), ensure_ascii=False)


# --------------- 9. Message Bus - Conversations (5) ---------------


async def _bus_client() -> httpx.AsyncClient:
    """Create a short-lived httpx client for Message Bus calls."""
    return httpx.AsyncClient(base_url=MESSAGE_BUS_URL, timeout=5.0)


@mcp.tool()
async def send_message(to_agent: str, message: str, from_agent: str = "mcp_client", ctx: Context = None) -> str:
    """Send a message to an agent via the AG-CLI Message Bus.

    Args:
        to_agent: Target agent name
        message: Message content
        from_agent: Sender name (default: mcp_client)

    Returns:
        JSON status from Message Bus
    """
    try:
        async with await _bus_client() as client:
            resp = await client.post(
                "/send",
                params={"from_agent": from_agent, "to_agent": to_agent, "message": message},
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False)
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def broadcast_message(message: str, from_agent: str = "mcp_client", ctx: Context = None) -> str:
    """Broadcast a message to ALL connected agents via the Message Bus.

    Args:
        message: Message content
        from_agent: Sender name (default: mcp_client)

    Returns:
        JSON status from Message Bus
    """
    try:
        async with await _bus_client() as client:
            resp = await client.post(
                "/broadcast",
                params={"from_agent": from_agent, "message": message},
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False)
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_conversation_log(limit: int = 100, ctx: Context = None) -> str:
    """Get full conversation history from the Message Bus (all agents).

    Args:
        limit: Maximum number of messages to return (default 100)

    Returns:
        JSON array of dialogue events [{timestamp, from_agent, to_agent, message, event_type}]
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get("/log", params={"limit": limit})
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_agent_conversation(agent1: str, agent2: str, ctx: Context = None) -> str:
    """Get conversation history between two specific agents.

    Args:
        agent1: First agent name
        agent2: Second agent name

    Returns:
        JSON array of dialogue events between the two agents
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get(f"/conversation/{agent1}/{agent2}")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_bus_status(ctx: Context = None) -> str:
    """Get Message Bus status: connected agents list, message count.

    Returns:
        JSON with service name, connected_agents list, log_count
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get("/")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 10. SharedMemory - Decisions (3) ---------------


async def _mem_client() -> httpx.AsyncClient:
    """Create a short-lived httpx client for SharedMemory calls."""
    return httpx.AsyncClient(base_url=SHARED_MEMORY_URL, timeout=5.0)


@mcp.tool()
async def get_shared_data(key: str, ctx: Context = None) -> str:
    """Retrieve a shared decision/data by category key from SharedMemory.

    Args:
        key: Decision category key (e.g. schema, api_spec, types)

    Returns:
        JSON value stored under the key
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get(f"/decision/{key}")
            if resp.status_code == 404:
                return _dumps({"error": f"Key not found: {key}"})
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def store_decision(category: str, decision_json: str, agent: str = "mcp_client", ctx: Context = None) -> str:
    """Store an architectural decision in SharedMemory.

    Args:
        category: Decision category (schema, api_spec, types, etc.)
        decision_json: Decision content as JSON string
        agent: Agent name storing the decision

    Returns:
        Stored decision with version info
    """
    try:
        decision = json.loads(decision_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/decision",
                json={"category": category, "decision": decision, "agent": agent},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_all_decisions(ctx: Context = None) -> str:
    """Get all shared decisions from SharedMemory.

    Returns:
        JSON dict of {category: {value, updated_by, updated_at, version}}
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get("/decisions")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 11. SharedMemory - Events (2) ---------------


@mcp.tool()
async def publish_event(event_type: str, data_json: str, source: str = "mcp_client", ctx: Context = None) -> str:
    """Publish an event to SharedMemory (notifies all subscribed agents).

    Common event types: schema_ready, api_ready, file_changed, task_done.

    Args:
        event_type: Event type string
        data_json: Event payload as JSON string
        source: Source agent name

    Returns:
        Published event with event_id and timestamp
    """
    try:
        data = json.loads(data_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/event",
                json={"event_type": event_type, "data": data, "source": source},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_events(event_type: str = "", limit: int = 100, ctx: Context = None) -> str:
    """Get event history from SharedMemory with optional type filter.

    Args:
        event_type: Filter by event type (empty = all events)
        limit: Maximum events to return

    Returns:
        JSON array of events [{event_id, event_type, data, source, timestamp}]
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        async with await _mem_client() as client:
            resp = await client.get("/events", params=params)
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 12. SharedMemory - API Spec & Schema (4) ---------------


@mcp.tool()
async def publish_api_spec(endpoints_json: str, agent: str = "backend", ctx: Context = None) -> str:
    """Publish API specification to SharedMemory (triggers api_ready event).

    Args:
        endpoints_json: JSON array of endpoints [{path, methods, description}]
        agent: Publishing agent name

    Returns:
        Publish confirmation with endpoint count
    """
    try:
        endpoints = json.loads(endpoints_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/api-spec",
                json={"endpoints": endpoints, "agent": agent},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_api_spec(ctx: Context = None) -> str:
    """Get shared API specification from SharedMemory.

    Returns:
        JSON array of API endpoints
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get("/api-spec")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def publish_schema(tables_json: str, agent: str = "db", ctx: Context = None) -> str:
    """Publish DB schema to SharedMemory (triggers schema_ready event).

    Args:
        tables_json: JSON dict of table definitions {table_name: {col: type, ...}}
        agent: Publishing agent name

    Returns:
        Publish confirmation with table count
    """
    try:
        tables = json.loads(tables_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/schema",
                json={"tables": tables, "agent": agent},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_schema(ctx: Context = None) -> str:
    """Get shared DB schema from SharedMemory.

    Returns:
        JSON dict of table definitions
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get("/schema")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 13. SharedMemory - File Locks (3) ---------------


@mcp.tool()
async def acquire_lock(file_path: str, agent: str = "mcp_client", timeout_seconds: int = 300, ctx: Context = None) -> str:
    """Acquire a distributed file lock in SharedMemory (prevents concurrent edits).

    Args:
        file_path: File path to lock
        agent: Agent requesting the lock
        timeout_seconds: Lock expiration in seconds (default 300)

    Returns:
        JSON with status: acquired or error if held by another agent
    """
    try:
        async with await _mem_client() as client:
            resp = await client.post(
                "/lock/acquire",
                json={"file_path": file_path, "agent": agent, "timeout_seconds": timeout_seconds},
            )
            if resp.status_code == 409:
                return _dumps({"error": "Lock held by another agent", "file_path": file_path})
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def release_lock(file_path: str, agent: str = "mcp_client", ctx: Context = None) -> str:
    """Release a distributed file lock in SharedMemory.

    Args:
        file_path: File path to unlock
        agent: Agent releasing the lock (must be the holder)

    Returns:
        JSON with status: released or not_held
    """
    try:
        async with await _mem_client() as client:
            resp = await client.post(
                "/lock/release",
                json={"file_path": file_path, "agent": agent, "timeout_seconds": 0},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def list_locks(ctx: Context = None) -> str:
    """List all active file locks in SharedMemory.

    Returns:
        JSON dict of {file_path: {locked_by, locked_at, expires_at}}
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get("/locks")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 14. Team Patterns (3) ---------------


@mcp.tool()
async def list_patterns(ctx: Context = None) -> str:
    """List all available team patterns with their configurations.

    Returns 5 built-in patterns: sequential, selector, handoff, debate, reflection.
    Each includes provider, layout type, and description.

    Returns:
        JSON dict of pattern definitions
    """
    return _dumps(PATTERN_DEFINITIONS)


@mcp.tool()
async def get_pattern_template(pattern: str, ctx: Context = None) -> str:
    """Get a full team template JSON for a pattern from JSON_MODULES.

    Args:
        pattern: Pattern name (sequential, selector, handoff, debate, reflection)

    Returns:
        Complete team component JSON ready for create_team
    """
    pattern_lower = pattern.lower()
    if pattern_lower not in PATTERN_DEFINITIONS:
        return _dumps({
            "error": f"Unknown pattern: {pattern}",
            "available": list(PATTERN_DEFINITIONS.keys()),
        })

    template_file = PATTERN_DEFINITIONS[pattern_lower]["template_file"]

    # Try templates/ first, then templates_compact/
    for subdir in ("templates", "templates_compact"):
        path = _JSON_MODULES / subdir / template_file
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                template = json.load(f)
            return _dumps(template)

    return _dumps({"error": f"Template file not found: {template_file}"})


@mcp.tool()
async def create_team_from_pattern(
    pattern: str,
    team_label: str,
    agent_names: str = "",
    ctx: Context = None,
) -> str:
    """Create a new team from a pattern template and register it in AutoGen Studio.

    Loads the pattern template, optionally customizes agent names, and
    POSTs the team to AutoGen Studio.

    Args:
        pattern: Pattern name (sequential, selector, handoff, debate, reflection)
        team_label: Display name for the new team
        agent_names: Comma-separated agent names to override template defaults (optional)

    Returns:
        Created team with id from AutoGen Studio
    """
    pattern_lower = pattern.lower()
    if pattern_lower not in PATTERN_DEFINITIONS:
        return _dumps({
            "error": f"Unknown pattern: {pattern}",
            "available": list(PATTERN_DEFINITIONS.keys()),
        })

    # Load template
    template_file = PATTERN_DEFINITIONS[pattern_lower]["template_file"]
    template = None
    for subdir in ("templates", "templates_compact"):
        path = _JSON_MODULES / subdir / template_file
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                template = json.load(f)
            break

    if template is None:
        return _dumps({"error": f"Template file not found: {template_file}"})

    # Customize label
    template["label"] = team_label

    # Optionally override agent names
    if agent_names:
        names = [n.strip() for n in agent_names.split(",") if n.strip()]
        participants = template.get("config", {}).get("participants", [])
        for i, name in enumerate(names):
            if i < len(participants):
                participants[i].setdefault("config", {})["name"] = name

    # Create in AutoGen Studio
    client = await _get_http(ctx)
    result = await _call_api(
        client, "POST", "/api/teams/",
        json_body={"user_id": AUTOGEN_STUDIO_USER, "component": template},
    )
    return _dumps(result)


# --------------- 15. Law Search (4) ---------------


async def _law_client() -> httpx.AsyncClient:
    """Create a short-lived httpx client for law-domain-agents calls."""
    return httpx.AsyncClient(
        base_url=LAW_BACKEND_URL,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={"Content-Type": "application/json"},
    )


@mcp.tool()
async def law_search(
    query: str,
    limit: int = 10,
    ctx: Context = None,
) -> str:
    """Search Korean law articles by keyword or article number (e.g. '제17조', '건축법').

    Uses hybrid search: exact_match + vector_search + relationship_search + RNE expansion,
    merged via Reciprocal Rank Fusion (RRF). Auto-routes to the best domain.

    Requires: AG law-domain-agents server on LAW_BACKEND_URL (default :8011) + Neo4j.

    Args:
        query: Search query (Korean law text, article number, or keyword)
        limit: Maximum results to return (default 10)

    Returns:
        JSON with results [{hang_id, content, unit_path, similarity, stages, law_name, law_type, article}],
        stats {total, vector_count, relationship_count, graph_expansion_count},
        domain_id, domain_name, response_time (ms)
    """
    try:
        async with await _law_client() as client:
            resp = await client.post(
                "/api/search",
                json={"query": query, "limit": limit},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Law backend not reachable at {LAW_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def law_search_domain(
    domain_id: str,
    query: str,
    limit: int = 10,
    ctx: Context = None,
) -> str:
    """Search law articles within a specific domain (use law_domains to list available).

    Same hybrid search as law_search but restricted to one domain.

    Args:
        domain_id: Domain ID (e.g. 'domain_09b3af0d') from law_domains
        query: Search query (Korean law text, article number, or keyword)
        limit: Maximum results to return (default 10)

    Returns:
        Same format as law_search
    """
    try:
        async with await _law_client() as client:
            resp = await client.post(
                f"/api/domain/{domain_id}/search",
                json={"query": query, "limit": limit},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Law backend not reachable at {LAW_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def law_domains(ctx: Context = None) -> str:
    """List all available law domains (regulation categories) from Neo4j.

    Returns:
        JSON with total count and domains array [{domain_id, domain_name, node_count}]
    """
    try:
        async with await _law_client() as client:
            resp = await client.get("/api/domains")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Law backend not reachable at {LAW_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def law_health(ctx: Context = None) -> str:
    """Check law domain agent server health (Neo4j connection, loaded domains, agents).

    Returns:
        JSON with status, domains_loaded, agents_created, timestamp
    """
    try:
        async with await _law_client() as client:
            resp = await client.get("/api/health")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Law backend not reachable at {LAW_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# --------------- 16. ARR Backend Law Proxy (2) ---------------


async def _arr_client() -> httpx.AsyncClient:
    """Create a short-lived httpx client for ARR Django backend calls."""
    return httpx.AsyncClient(
        base_url=ARR_BACKEND_URL,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={"Content-Type": "application/json"},
    )


@mcp.tool()
async def arr_law_search(
    query: str,
    limit: int = 10,
    ctx: Context = None,
) -> str:
    """Search Korean law via ARR backend proxy (results stored in Django DB for history/analytics).

    Same hybrid search as law_search, but routed through ARR Django backend (port 8000)
    which logs each search to its database. Use this when you want searches to be recorded.

    Args:
        query: Search query (Korean law text, article number, or keyword)
        limit: Maximum results to return (default 10)

    Returns:
        Same format as law_search (proxied from law-domain-agents via ARR)
    """
    try:
        async with await _arr_client() as client:
            resp = await client.post(
                "/law/search/",
                json={"q": query, "limit": limit},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_law_health(ctx: Context = None) -> str:
    """Check ARR backend + law-domain-agents health (both services).

    Returns:
        JSON with ARR backend status and proxied law-domain-agents health
    """
    result = {}
    # Check ARR backend
    try:
        async with await _arr_client() as client:
            resp = await client.get("/law/health/")
            resp.raise_for_status()
            result["arr_backend"] = {"status": True, "url": ARR_BACKEND_URL}
            result["law_agents"] = resp.json()
    except httpx.ConnectError:
        result["arr_backend"] = {"status": False, "url": ARR_BACKEND_URL, "error": "not reachable"}
        # Try direct law-domain-agents
        try:
            async with await _law_client() as client:
                resp = await client.get("/api/health")
                resp.raise_for_status()
                result["law_agents"] = resp.json()
        except Exception:
            result["law_agents"] = {"status": False, "url": LAW_BACKEND_URL, "error": "not reachable"}
    except Exception as e:
        result["arr_backend"] = {"status": False, "error": str(e)}

    return _dumps(result)


# --------------- 17. ARR Backend Land Regulation (4) ---------------


@mcp.tool()
async def arr_land_analyze(
    input: str,
    input_type: str = "pnu",
    zones: list[str] | None = None,
    include_law: bool = True,
    ctx: Context = None,
) -> str:
    """Analyze land parcel for 41 building regulations with legal article references.

    Returns 10 core regulations (BCR, FAR, height, sunlight, corner cutoff,
    road diagonal, building line, adjacent setback, parking, landscaping) plus
    31 extended regulations in regulations.extended (zone-dependent 5, scale-dependent 10,
    text-only 16 — covering fire safety, accessibility, energy, CPTED, etc.).

    Args:
        input: PNU code (19 digits) or address string
        input_type: "pnu" or "address" (default "pnu")
        zones: Optional list of zoning names (e.g. ["제1종일반주거지역"])
        include_law: Whether to search related law articles (default True)

    Returns:
        JSON with pnu, regulations (10 core + 31 extended with articles), zone_info,
        land_info, law_articles, restrictions
    """
    try:
        payload: dict[str, Any] = {
            "input": input,
            "input_type": input_type,
            "include_law": include_law,
        }
        if zones:
            payload["zones"] = zones
        async with await _arr_client() as client:
            resp = await client.post("/land/analyze/", json=payload)
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_resolve(
    input: str,
    input_type: str = "address",
    ctx: Context = None,
) -> str:
    """Resolve address to PNU code or validate an existing PNU.

    Args:
        input: Address string or PNU code to resolve/validate
        input_type: "address" (geocode to PNU) or "pnu" (validate)

    Returns:
        JSON with resolved PNU info (sido, sigungu, etc.)
    """
    try:
        async with await _arr_client() as client:
            resp = await client.post(
                "/land/resolve/",
                json={"input": input, "input_type": input_type},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_zones(ctx: Context = None) -> str:
    """List all 21 zoning types with their building regulation limits.

    Returns:
        JSON list of zones with bcr_limit (건폐율) and far_limit (용적률)
    """
    try:
        async with await _arr_client() as client:
            resp = await client.get("/land/zones/")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_stats(ctx: Context = None) -> str:
    """Get land regulation query statistics.

    Returns:
        JSON with total queries, average response time, zone distribution
    """
    try:
        async with await _arr_client() as client:
            resp = await client.get("/land/stats/")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_agent_analyze(
    input: str,
    input_type: str = "pnu",
    zones: list[str] | None = None,
    timeout: int = 600,
    ctx: Context = None,
) -> str:
    """Analyze land parcel with 6-agent collaborative team (deep analysis).

    Runs quick analysis first (41 regulations), then delegates to the
    Land Swarm Analysis Team (6 agents: land_analyst, legal_interpreter,
    regulatory_monitor, spatial_analyzer, market_analyst, report_writer)
    for comprehensive multi-perspective analysis.

    Args:
        input: PNU code (19 digits) or address string
        input_type: "pnu" or "address" (default "pnu")
        zones: Optional list of zoning names (e.g. ["제1종일반주거지역"])
        timeout: Max execution time in seconds (default 600)

    Returns:
        JSON with quick_result (41 regulations), agent_messages, report,
        and run_summary (duration, tokens, turns)
    """
    result: dict[str, Any] = {}

    # Phase 1: Quick analysis via ARR backend
    try:
        payload: dict[str, Any] = {
            "input": input,
            "input_type": input_type,
            "include_law": True,
        }
        if zones:
            payload["zones"] = zones
        async with await _arr_client() as client:
            resp = await client.post("/land/analyze/", json=payload)
            resp.raise_for_status()
            result["quick_result"] = resp.json()
    except httpx.ConnectError:
        return _dumps({"error": f"ARR backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": f"Quick analysis failed: {e}"})

    # Phase 2: Agent team execution
    try:
        async with httpx.AsyncClient(
            base_url=AUTOGEN_STUDIO_URL, timeout=httpx.Timeout(30.0)
        ) as client:
            team = await _resolve_team(client, "Land Swarm Analysis Team")
            team_id = team.get("id")
            if not team_id:
                result["agent_error"] = "Team found but has no ID"
                return _dumps(result)

            qr = result.get("quick_result", {})
            pnu_info = qr.get("pnu", {})
            pnu_str = pnu_info.get("pnu", input) if isinstance(pnu_info, dict) else input
            addr_str = pnu_info.get("address", "") if isinstance(pnu_info, dict) else ""
            zone_info = qr.get("zone_info") or {}
            zone_list = zone_info.get("zones", [])
            regs = qr.get("regulations") or {}
            bcr = regs.get("bcr", {})
            far = regs.get("far", {})

            task = (
                f"토지 규제 심화 분석을 수행해주세요.\n"
                f"PNU: {pnu_str}\n"
                f"주소: {addr_str}\n"
                f"용도지역: {', '.join(zone_list) if zone_list else '미확인'}\n"
                f"건폐율: {bcr.get('limit_pct', '?')}%\n"
                f"용적률: {far.get('limit_pct', '?')}%\n"
                f"기본 분석에서 {len(qr.get('restrictions', []))}개 규제, "
                f"{(qr.get('law_articles') or {}).get('total_count', 0)}개 법조항 발견.\n"
                f"각 에이전트는 전문 분야에 맞는 심화 분석을 수행하세요."
            )

            ws_result = await _execute_via_ws(
                client, team_id, task, timeout=timeout,
            )
            result["agent_messages"] = ws_result.get("messages", [])
            result["run_summary"] = ws_result.get("run_summary", {})

            # Extract report from last agent message
            agent_turns = [
                m for m in result["agent_messages"]
                if m.get("message_type") == "agent"
            ]
            result["report"] = agent_turns[-1]["content"] if agent_turns else ""

    except Exception as e:
        result["agent_error"] = str(e)

    return _dumps(result)


# ===============================================================
# Main entry point
# ===============================================================


def main():
    parser = argparse.ArgumentParser(description="ACE MCP Server - AutoGen Studio")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport mode (default: stdio)",
    )
    parser.add_argument(
        "--port", type=int, default=8200,
        help="Port for streamable-http transport (default: 8200)",
    )
    args = parser.parse_args()

    logger.info(
        f"Starting ACE MCP Server "
        f"(transport={args.transport}, studio={AUTOGEN_STUDIO_URL}, 57 tools)"
    )

    if args.transport == "streamable-http":
        mcp._host = "127.0.0.1"
        mcp._port = args.port

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()

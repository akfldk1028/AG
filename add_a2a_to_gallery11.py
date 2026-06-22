"""Add A2A agents from AG/agent to Gallery 11"""
import sqlite3, json, copy
from datetime import datetime

conn = sqlite3.connect(r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db")

# Load Gallery 11
row = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg = json.loads(row[0])

# =============================================
# A2A TOOL 정의 - AutoGen FunctionTool 형식
# =============================================
# AutoGen Studio에서 tool은 Python 함수로 정의됨
# A2A 호출은 requests.post로 JSON-RPC 2.0 메시지를 보내는 방식

def make_a2a_tool(label, description, func_name, url, port):
    """A2A tool component for Gallery"""
    # AutoGen Studio tool format: Python source code as string
    source_code = f'''def {func_name}(query: str) -> str:
    """
    {description}
    A2A Protocol (JSON-RPC 2.0) - Port {port}

    Args:
        query: 질문 또는 요청 텍스트

    Returns:
        에이전트 응답 텍스트
    """
    import requests, uuid, json
    message_id = str(uuid.uuid4())
    payload = {{
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": message_id,
        "params": {{
            "message": {{
                "messageId": message_id,
                "role": "user",
                "parts": [{{"kind": "text", "text": query}}]
            }}
        }}
    }}
    try:
        resp = requests.post("{url}", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        # Google ADK format
        if "result" in result:
            for artifact in result["result"].get("artifacts", []):
                for part in artifact.get("parts", []):
                    if part.get("kind") == "text" or part.get("type") == "text":
                        return part.get("text", "")
            # LangGraph/FastAPI format
            parts = result["result"].get("parts", [])
            for part in parts:
                if part.get("kind") == "text" or part.get("type") == "text":
                    return part.get("text", "")
        return json.dumps(result, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        return f"[Error] A2A server not running at {url}. Start the agent first."
    except Exception as e:
        return f"[Error] {{str(e)}}"
'''
    return {
        "provider": "autogen_ext.tools.code_execution.PythonCodeExecutionTool",
        "component_type": "tool",
        "version": 1,
        "component_version": 1,
        "label": label,
        "description": description,
        "config": {
            "name": func_name,
            "description": description,
            "content": source_code,
            "global_imports": []
        }
    }


# =============================================
# A2A 에이전트 정의 (AG/agent 프로젝트들)
# =============================================

# --- Model reference (Sonnet for A2A coordinator) ---
model_sonnet = {
    "provider": "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient",
    "component_type": "model", "version": 1, "component_version": 1,
    "label": "Claude Sonnet 4.5 (Max OAuth)",
    "description": "Claude Sonnet 4.5 - Max OAuth. Balanced speed/quality.",
    "config": {"model": "claude-sonnet-4-5-20250929"}
}

def make_agent(name, label, desc, system_msg, model_client):
    return {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent", "version": 2, "component_version": 2,
        "description": desc, "label": label,
        "config": {
            "name": name,
            "model_client": copy.deepcopy(model_client),
            "model_context": {
                "provider": "autogen_core.model_context.UnboundedChatCompletionContext",
                "component_type": "chat_completion_context", "version": 1, "component_version": 1,
                "description": "An unbounded chat completion context.",
                "label": "UnboundedChatCompletionContext", "config": {}
            },
            "description": desc,
            "system_message": system_msg,
            "model_client_stream": False,
            "reflect_on_tool_use": False,
            "tool_call_summary_format": "{result}",
            "metadata": {}
        }
    }

# =============================================
# 1. A2A Tools - a2a 프로젝트 (8001, 8002)
# =============================================
tool_history = make_a2a_tool(
    "A2A: History Helper (8001)",
    "A2A Protocol로 역사 전문 에이전트를 호출합니다. Google ADK 기반, 포트 8001.",
    "call_history_agent",
    "http://127.0.0.1:8001/",
    8001
)

tool_philosophy = make_a2a_tool(
    "A2A: Philosophy Helper (8002)",
    "A2A Protocol로 철학 전문 에이전트를 호출합니다. LangGraph 기반, 포트 8002.",
    "call_philosophy_agent",
    "http://127.0.0.1:8002/messages",
    8002
)

# =============================================
# 2. A2A Tools - law-domain-agents (8011)
# =============================================
tool_law_search = make_a2a_tool(
    "A2A: Law Domain Search (8011)",
    "A2A Protocol로 법률 도메인 에이전트를 호출합니다. Neo4j 기반 법률 검색, 포트 8011.",
    "call_law_domain_agent",
    "http://127.0.0.1:8011/messages/domain-1",
    8011
)

# =============================================
# 3. A2A Tools - 기존 a2a_demo (8003-8006, 8120)
# =============================================
tool_poetry = make_a2a_tool(
    "A2A: Poetry Agent (8003)",
    "A2A Protocol로 시/문학 분석 에이전트를 호출합니다. 포트 8003.",
    "call_poetry_agent",
    "http://127.0.0.1:8003/",
    8003
)

tool_calc = make_a2a_tool(
    "A2A: Calculator Agent (8006)",
    "A2A Protocol로 수학 계산 에이전트를 호출합니다. 포트 8006.",
    "call_calculator_agent",
    "http://127.0.0.1:8006/",
    8006
)

tool_gui = make_a2a_tool(
    "A2A: GUI Test Agent (8120)",
    "A2A Protocol로 GUI 자동화 에이전트(PyAutoGUI)를 호출합니다. 포트 8120.",
    "call_gui_test_agent",
    "http://127.0.0.1:8120/",
    8120
)

a2a_tools = [tool_history, tool_philosophy, tool_law_search, tool_poetry, tool_calc, tool_gui]

# =============================================
# 4. A2A Coordinator Agent
# =============================================
a2a_coordinator = make_agent(
    "a2a_coordinator_agent",
    "A2A Coordinator",
    "A2A Protocol을 통해 외부 에이전트들을 조율하는 코디네이터. History(8001), Philosophy(8002), Law(8011), Poetry(8003), Calculator(8006), GUI(8120) 연결.",
    """You are the A2A Coordinator Agent. You can call external agents via A2A Protocol (JSON-RPC 2.0).

Available A2A Agents:
- call_history_agent: History homework helper (port 8001, Google ADK)
- call_philosophy_agent: Philosophy homework helper (port 8002, LangGraph)
- call_law_domain_agent: Korean law search with Neo4j (port 8011)
- call_poetry_agent: Poetry/literary analysis (port 8003)
- call_calculator_agent: Math calculations (port 8006)
- call_gui_test_agent: GUI automation via PyAutoGUI (port 8120)

When a user asks a question:
1. Determine which agent(s) are best suited
2. Call the appropriate tool(s)
3. Synthesize the results into a coherent response
4. If an agent is unavailable, inform the user and suggest alternatives

Always respond in the same language as the user's input.
When done, say TERMINATE.""",
    model_sonnet
)

# =============================================
# 5. A2A Team (Selector - routes to right agent)
# =============================================
term_terminate = {
    "provider": "autogen_agentchat.conditions.TextMentionTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Terminate when TERMINATE is mentioned.",
    "label": "TextMentionTermination",
    "config": {"text": "TERMINATE"}
}
term_max10 = {
    "provider": "autogen_agentchat.conditions.MaxMessageTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Max 10 messages.",
    "label": "MaxMessageTermination(10)",
    "config": {"max_messages": 10, "include_agent_event": False}
}

user_proxy = {
    "provider": "autogen_agentchat.agents.UserProxyAgent",
    "component_type": "agent", "version": 1, "component_version": 1,
    "description": "A human user proxy agent.",
    "label": "UserProxyAgent",
    "config": {"name": "user_proxy", "description": "A human user proxy."}
}

a2a_team = {
    "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
    "component_type": "team", "version": 1, "component_version": 1,
    "description": "A2A Protocol 팀: Coordinator가 외부 A2A 에이전트(History, Philosophy, Law, Poetry, Calculator, GUI)를 호출하여 응답.",
    "label": "Auto-Claude A2A Protocol Team",
    "config": {
        "name": "RoundRobinGroupChat",
        "description": "A2A Protocol team with external agent integration.",
        "participants": [copy.deepcopy(a2a_coordinator), copy.deepcopy(user_proxy)],
        "termination_condition": {
            "provider": "autogen_agentchat.base.OrTerminationCondition",
            "component_type": "termination", "version": 1, "component_version": 1,
            "label": "OrTerminationCondition",
            "config": {"conditions": [term_terminate, term_max10]}
        },
        "emit_team_events": False
    }
}

# =============================================
# Gallery 업데이트
# =============================================
# Add tools
cfg["components"]["tools"].extend(a2a_tools)

# Add agent
cfg["components"]["agents"].append(a2a_coordinator)

# Add team
cfg["components"]["teams"].append(a2a_team)

# Update metadata
cfg["metadata"]["version"] = "3.0.0"
cfg["metadata"]["description"] = (
    "Auto-Claude + A2A Protocol Gallery. "
    "Build Pipeline, Spec Creation, QA Loop teams + "
    "A2A Protocol Team (History/Philosophy/Law/Poetry/Calculator/GUI agents)."
)

# Save
conn.execute("UPDATE gallery SET config = ? WHERE id = 11",
    (json.dumps(cfg, ensure_ascii=False),))
conn.commit()

# Also create team in team table for Playground
now = datetime.now().isoformat()
conn.execute(
    "INSERT INTO team (created_at, updated_at, user_id, version, component) VALUES (?, ?, ?, ?, ?)",
    (now, now, "guestuser@gmail.com", "1", json.dumps(a2a_team, ensure_ascii=False))
)
conn.commit()

# Get new team ID
new_team_id = conn.execute("SELECT id FROM team ORDER BY id DESC LIMIT 1").fetchone()[0]

# Verify
row2 = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg2 = json.loads(row2[0])
comps = cfg2["components"]
print("=== Gallery 11 Updated (v3.0.0 - A2A Protocol Added) ===")
print(f"version: {cfg2['metadata']['version']}")
for key in comps:
    items = comps[key]
    print(f"\n{key}: {len(items)} items")
    for item in items:
        if isinstance(item, dict):
            label = item.get("label", "?")
            ct = item.get("component_type", "?")
            if "A2A" in label:
                print(f"  ★ [{ct}] {label}")
            else:
                print(f"  [{ct}] {label}")

print(f"\nNew A2A Team created in Playground: ID={new_team_id}")

conn.close()
print("\nDONE")

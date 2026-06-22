"""
Fix Team 37 in AutoGen Studio DB:
  - deep_research_agent's tool: PythonCodeExecutionTool -> FunctionTool
"""

import sqlite3
import json
import textwrap

DB_PATH = r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db"
TEAM_ID = 37

FUNCTION_SOURCE = textwrap.dedent('''\
def call_deep_research(query: str) -> str:
    """Deep research via A2A Protocol (port 9013)"""
    import requests, uuid, json
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
        resp = requests.post("http://127.0.0.1:9013/", json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        if "result" in result:
            for artifact in result["result"].get("artifacts", []):
                for part in artifact.get("parts", []):
                    if part.get("kind") == "text" or part.get("type") == "text":
                        return part.get("text", "")
            parts = result["result"].get("parts", [])
            for part in parts:
                if part.get("kind") == "text" or part.get("type") == "text":
                    return part.get("text", "")
        return json.dumps(result, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        return "[Error] A2A server not running at port 9013"
    except Exception as e:
        return f"[Error] {str(e)}"
''')

NEW_TOOL = {
    "provider": "autogen_ext.tools.FunctionTool",
    "component_type": "tool",
    "version": 1,
    "component_version": 1,
    "label": "A2A: Deep Research (9013)",
    "description": "A2A Deep Research agent call via port 9013",
    "config": {
        "source_code": FUNCTION_SOURCE,
        "name": "call_deep_research",
        "description": "A2A Deep Research agent call"
    }
}


def find_and_fix_tool(node):
    """Recursively find deep_research_agent and fix its tool."""
    changed = False

    # Check if this node is the deep_research_agent participant
    config = node.get("config", {})
    label = node.get("label", "")
    name = config.get("name", "")

    is_deep_research = "deep_research" in label.lower() or "deep_research" in name.lower()

    if is_deep_research and "tools" in config:
        tools = config["tools"]
        for i, tool in enumerate(tools):
            provider = tool.get("provider", "")
            if "PythonCodeExecutionTool" in provider or "deep_research" in tool.get("label", "").lower():
                print(f"  [FIX] Replacing tool [{i}]: {provider}")
                print(f"         Old label: {tool.get('label', 'N/A')}")
                tools[i] = NEW_TOOL
                changed = True
                print(f"         New provider: {NEW_TOOL['provider']}")

    # Recurse into participants
    for participant in config.get("participants", []):
        if find_and_fix_tool(participant):
            changed = True

    # Recurse into team component if nested
    if "component" in node:
        if find_and_fix_tool(node["component"]):
            changed = True

    return changed


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, component FROM team WHERE id = ?", (TEAM_ID,))
    row = cursor.fetchone()
    if not row:
        print(f"[ERROR] Team {TEAM_ID} not found!")
        conn.close()
        return

    team_id, component_json = row
    component = json.loads(component_json)

    print(f"Team {team_id}: {component.get('label', 'N/A')}")
    print(f"Provider: {component.get('provider', 'N/A')}")
    print()

    changed = find_and_fix_tool(component)

    if changed:
        new_json = json.dumps(component, ensure_ascii=False)
        cursor.execute("UPDATE team SET component = ? WHERE id = ?", (new_json, team_id))
        conn.commit()
        print("\n[OK] Database updated successfully.")
    else:
        print("\n[WARN] No matching tool found to fix.")

    # Verify: print deep_research_agent's tools
    print("\n--- Verification ---")
    cursor.execute("SELECT component FROM team WHERE id = ?", (TEAM_ID,))
    row = cursor.fetchone()
    comp = json.loads(row[0])

    def print_tools(node, depth=0):
        cfg = node.get("config", {})
        lbl = node.get("label", "")
        nm = cfg.get("name", "")
        if "deep_research" in lbl.lower() or "deep_research" in nm.lower():
            print(f"{'  '*depth}Participant: {lbl} (name={nm})")
            for t in cfg.get("tools", []):
                print(f"{'  '*depth}  Tool provider: {t.get('provider')}")
                print(f"{'  '*depth}  Tool label:    {t.get('label')}")
                print(f"{'  '*depth}  Tool config keys: {list(t.get('config', {}).keys())}")
                print(f"{'  '*depth}  Tool config name: {t['config'].get('name', 'N/A')}")
        for p in cfg.get("participants", []):
            print_tools(p, depth + 1)

    print_tools(comp)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

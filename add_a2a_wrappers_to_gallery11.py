"""Add 17 A2A wrapper tools (ports 9001-9017) to Gallery 11"""
import sqlite3, json, copy
from datetime import datetime

conn = sqlite3.connect(r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db")

# Load Gallery 11
row = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg = json.loads(row[0])

def make_a2a_tool(label, description, func_name, url, port):
    """A2A tool component for Gallery"""
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
        resp = requests.post("{url}", json=payload, timeout=60)
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
        return f"[Error] A2A server not running at {url}. Start with: python a2a_server.py"
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

# 17 new A2A wrapper tools
new_tools = [
    make_a2a_tool(
        "A2A: ChatGPT Clone (9001)",
        "A2A Protocol로 ChatGPT 클론 에이전트를 호출합니다. 웹 검색, 이미지 생성, 코드 실행. 포트 9001.",
        "call_chatgpt_clone", "http://127.0.0.1:9001/", 9001),
    make_a2a_tool(
        "A2A: Customer Support (9002)",
        "A2A Protocol로 고객 지원 에이전트를 호출합니다. 5개 전문 에이전트 기반. 포트 9002.",
        "call_customer_support", "http://127.0.0.1:9002/", 9002),
    make_a2a_tool(
        "A2A: Tutor Agent (9003)",
        "A2A Protocol로 AI 튜터 에이전트를 호출합니다. LangGraph 기반. 포트 9003.",
        "call_tutor_agent", "http://127.0.0.1:9003/", 9003),
    make_a2a_tool(
        "A2A: LangGraph Poet (9004)",
        "A2A Protocol로 시 작성 에이전트를 호출합니다. LangGraph Mr. Poet. 포트 9004.",
        "call_langgraph_poet", "http://127.0.0.1:9004/", 9004),
    make_a2a_tool(
        "A2A: Multi-Agent Arch (9005)",
        "A2A Protocol로 멀티 에이전트 아키텍처 에이전트를 호출합니다. Swarm/Supervisor/Hierarchical 패턴. 포트 9005.",
        "call_multi_agent_arch", "http://127.0.0.1:9005/", 9005),
    make_a2a_tool(
        "A2A: Content Pipeline (9006)",
        "A2A Protocol로 콘텐츠 파이프라인 에이전트를 호출합니다. CrewAI 기반. 포트 9006.",
        "call_content_pipeline", "http://127.0.0.1:9006/", 9006),
    make_a2a_tool(
        "A2A: Job Hunter (9007)",
        "A2A Protocol로 구직 자동화 에이전트를 호출합니다. CrewAI 기반. 포트 9007.",
        "call_job_hunter", "http://127.0.0.1:9007/", 9007),
    make_a2a_tool(
        "A2A: News Reader (9008)",
        "A2A Protocol로 뉴스 수집 에이전트를 호출합니다. CrewAI 기반. 포트 9008.",
        "call_news_reader", "http://127.0.0.1:9008/", 9008),
    make_a2a_tool(
        "A2A: YouTube Thumbnail (9009)",
        "A2A Protocol로 YouTube 썸네일 생성 에이전트를 호출합니다. LangGraph 기반. 포트 9009.",
        "call_youtube_thumbnail", "http://127.0.0.1:9009/", 9009),
    make_a2a_tool(
        "A2A: Workflow Testing (9010)",
        "A2A Protocol로 워크플로우 테스팅 에이전트를 호출합니다. LangGraph 기반. 포트 9010.",
        "call_workflow_testing", "http://127.0.0.1:9010/", 9010),
    make_a2a_tool(
        "A2A: Deployment Agent (9011)",
        "A2A Protocol로 프로덕션 배포 에이전트를 호출합니다. OpenAI Agents 기반. 포트 9011.",
        "call_deployment_agent", "http://127.0.0.1:9011/", 9011),
    make_a2a_tool(
        "A2A: Financial Analyst (9012)",
        "A2A Protocol로 금융 분석 에이전트를 호출합니다. Google ADK 기반, 주식/뉴스 분석. 포트 9012.",
        "call_financial_analyst", "http://127.0.0.1:9012/", 9012),
    make_a2a_tool(
        "A2A: Deep Research (9013)",
        "A2A Protocol로 심층 리서치 에이전트를 호출합니다. AutoGen 기반. 포트 9013.",
        "call_deep_research", "http://127.0.0.1:9013/", 9013),
    make_a2a_tool(
        "A2A: Email Refiner (9014)",
        "A2A Protocol로 이메일 개선 에이전트를 호출합니다. Google ADK 기반. 포트 9014.",
        "call_email_refiner", "http://127.0.0.1:9014/", 9014),
    make_a2a_tool(
        "A2A: YouTube Shorts (9015)",
        "A2A Protocol로 YouTube Shorts 제작 에이전트를 호출합니다. Google ADK 기반. 포트 9015.",
        "call_youtube_shorts", "http://127.0.0.1:9015/", 9015),
    make_a2a_tool(
        "A2A: Workflow Arch (9016)",
        "A2A Protocol로 워크플로우 아키텍처 에이전트를 호출합니다. LangGraph 기반. 포트 9016.",
        "call_workflow_arch", "http://127.0.0.1:9016/", 9016),
    make_a2a_tool(
        "A2A: First Agent (9017)",
        "A2A Protocol로 기본 에이전트를 호출합니다. OpenAI SDK 기반. 포트 9017.",
        "call_first_agent", "http://127.0.0.1:9017/", 9017),
]

# Add tools to Gallery 11
cfg["components"]["tools"].extend(new_tools)

# Update A2A Coordinator's system message to include new agents
for agent in cfg["components"]["agents"]:
    if agent.get("config", {}).get("name") == "a2a_coordinator_agent":
        agent["config"]["system_message"] = """You are the A2A Coordinator Agent. You can call external agents via A2A Protocol (JSON-RPC 2.0).

Available A2A Agents (Native):
- call_history_agent: History homework helper (port 8001, Google ADK)
- call_philosophy_agent: Philosophy homework helper (port 8002, LangGraph)
- call_law_domain_agent: Korean law search with Neo4j (port 8011)
- call_poetry_agent: Poetry/literary analysis (port 8003)
- call_calculator_agent: Math calculations (port 8006)
- call_gui_test_agent: GUI automation via PyAutoGUI (port 8120)

Available A2A Agents (Wrapped):
- call_chatgpt_clone: ChatGPT clone with web search, image gen, code exec (port 9001)
- call_customer_support: Customer support with 5 specialist agents (port 9002)
- call_tutor_agent: AI tutor system (port 9003)
- call_langgraph_poet: Poetry writing bot - Mr. Poet (port 9004)
- call_multi_agent_arch: Multi-agent architecture patterns (port 9005)
- call_content_pipeline: Content pipeline automation (port 9006)
- call_job_hunter: Job hunting automation (port 9007)
- call_news_reader: News collection and analysis (port 9008)
- call_youtube_thumbnail: YouTube thumbnail generation (port 9009)
- call_workflow_testing: Workflow testing methodology (port 9010)
- call_deployment_agent: Production deployment patterns (port 9011)
- call_financial_analyst: Financial analysis - stocks, news, investment (port 9012)
- call_deep_research: Deep research automation (port 9013)
- call_email_refiner: Email text refinement (port 9014)
- call_youtube_shorts: YouTube Shorts creation (port 9015)
- call_workflow_arch: Workflow architecture patterns (port 9016)
- call_first_agent: Basic agent with weather tool (port 9017)

When a user asks a question:
1. Determine which agent(s) are best suited
2. Call the appropriate tool(s)
3. Synthesize the results into a coherent response
4. If an agent is unavailable, inform the user and suggest alternatives

Always respond in the same language as the user's input.
When done, say TERMINATE."""
        # Also add tools to the coordinator agent
        agent["config"]["tools"] = [copy.deepcopy(t) for t in new_tools]
        break

# Also update the A2A team's coordinator participant
for team in cfg["components"]["teams"]:
    if "A2A" in team.get("label", ""):
        for participant in team["config"]["participants"]:
            if participant.get("config", {}).get("name") == "a2a_coordinator_agent":
                # Find the updated coordinator agent from components
                for ag in cfg["components"]["agents"]:
                    if ag.get("config", {}).get("name") == "a2a_coordinator_agent":
                        participant["config"]["system_message"] = ag["config"]["system_message"]
                        participant["config"]["tools"] = [copy.deepcopy(t) for t in new_tools]
                        break
                break
        break

# Update metadata
cfg["metadata"]["version"] = "4.0.0"
cfg["metadata"]["description"] = (
    "Auto-Claude + Full A2A Protocol Gallery. "
    "Build Pipeline, Spec Creation, QA Loop teams + "
    "A2A Protocol Team with 23 external agents (6 native + 17 wrapped)."
)

# Save
conn.execute("UPDATE gallery SET config = ? WHERE id = 11",
    (json.dumps(cfg, ensure_ascii=False),))
conn.commit()

# Update team in team table too
team_row = conn.execute("SELECT id, component FROM team ORDER BY id DESC LIMIT 1").fetchone()
if team_row:
    team_id = team_row[0]
    team_cfg = json.loads(team_row[1])
    if "A2A" in team_cfg.get("label", ""):
        # Update the team's coordinator with new tools
        for participant in team_cfg["config"]["participants"]:
            if participant.get("config", {}).get("name") == "a2a_coordinator_agent":
                for agent in cfg["components"]["agents"]:
                    if agent.get("config", {}).get("name") == "a2a_coordinator_agent":
                        participant["config"]["system_message"] = agent["config"]["system_message"]
                        participant["config"]["tools"] = agent["config"].get("tools", [])
                        break
                break
        now = datetime.now().isoformat()
        conn.execute("UPDATE team SET component = ?, updated_at = ? WHERE id = ?",
            (json.dumps(team_cfg, ensure_ascii=False), now, team_id))
        conn.commit()
        print(f"Updated Team {team_id} with new A2A tools")

# Verify
row2 = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg2 = json.loads(row2[0])
comps = cfg2["components"]
print("=== Gallery 11 Updated (v4.0.0 - Full A2A) ===")
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

conn.close()
print("\nDONE")

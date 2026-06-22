"""Add 23 individual A2A agents to Gallery 11 agents section"""
import sqlite3, json, copy
from datetime import datetime

conn = sqlite3.connect(r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db")
row = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg = json.loads(row[0])

# Model
model_sonnet = {
    "provider": "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient",
    "component_type": "model", "version": 1, "component_version": 1,
    "label": "Claude Sonnet 4.5 (Max OAuth)",
    "description": "Claude Sonnet 4.5 - Max OAuth.",
    "config": {"model": "claude-sonnet-4-5-20250929"}
}

# Collect A2A tools by label
a2a_tools = {t["label"]: t for t in cfg["components"]["tools"] if "A2A" in t.get("label", "")}

def make_a2a_agent(name, label, desc, system_msg, tool_label):
    tool = a2a_tools.get(tool_label)
    agent = {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent", "version": 2, "component_version": 2,
        "description": desc, "label": label,
        "config": {
            "name": name,
            "model_client": copy.deepcopy(model_sonnet),
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
    if tool:
        agent["config"]["tools"] = [copy.deepcopy(tool)]
    return agent

# =============================================
# 23 A2A Agents
# =============================================
new_agents = [
    # Native A2A (8001-8120)
    make_a2a_agent("history_agent", "A2A: History Helper",
        "A2A 역사 전문 에이전트 (Google ADK, port 8001)",
        "You are a History expert agent. Use call_history_agent tool to answer history questions. Always call the tool, then synthesize. Respond in user's language. When done, say TERMINATE.",
        "A2A: History Helper (8001)"),

    make_a2a_agent("philosophy_agent", "A2A: Philosophy Helper",
        "A2A 철학 전문 에이전트 (LangGraph, port 8002)",
        "You are a Philosophy expert agent. Use call_philosophy_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Philosophy Helper (8002)"),

    make_a2a_agent("law_domain_agent", "A2A: Law Domain Search",
        "A2A 법률 검색 에이전트 (Neo4j, port 8011)",
        "You are a Korean Law search agent. Use call_law_domain_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Law Domain Search (8011)"),

    make_a2a_agent("poetry_agent", "A2A: Poetry Agent",
        "A2A 시/문학 에이전트 (Google ADK, port 8003)",
        "You are a Poetry and literary analysis agent. Use call_poetry_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Poetry Agent (8003)"),

    make_a2a_agent("calculator_agent", "A2A: Calculator Agent",
        "A2A 수학 계산 에이전트 (port 8006)",
        "You are a Calculator agent. Use call_calculator_agent tool. When done, say TERMINATE.",
        "A2A: Calculator Agent (8006)"),

    make_a2a_agent("gui_test_agent", "A2A: GUI Test Agent",
        "A2A GUI 자동화 에이전트 (PyAutoGUI, port 8120)",
        "You are a GUI automation agent using PyAutoGUI. Use call_gui_test_agent tool. When done, say TERMINATE.",
        "A2A: GUI Test Agent (8120)"),

    # Wrapped A2A (9001-9017)
    make_a2a_agent("chatgpt_clone_agent", "A2A: ChatGPT Clone",
        "A2A ChatGPT 클론 - 웹검색/이미지생성/코드실행 (port 9001)",
        "You are a ChatGPT Clone agent with web search, image gen, code exec. Use call_chatgpt_clone tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: ChatGPT Clone (9001)"),

    make_a2a_agent("customer_support_agent", "A2A: Customer Support",
        "A2A 고객지원 에이전트 - 5개 전문 에이전트 (port 9002)",
        "You are a Customer Support agent with 5 specialists. Use call_customer_support tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Customer Support (9002)"),

    make_a2a_agent("tutor_agent", "A2A: Tutor Agent",
        "A2A AI 튜터 에이전트 (LangGraph, port 9003)",
        "You are an AI Tutor agent. Use call_tutor_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Tutor Agent (9003)"),

    make_a2a_agent("langgraph_poet_agent", "A2A: LangGraph Poet",
        "A2A 시 작성 에이전트 Mr. Poet (LangGraph, port 9004)",
        "You are a Poetry writing agent (Mr. Poet). Use call_langgraph_poet tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: LangGraph Poet (9004)"),

    make_a2a_agent("multi_agent_arch_agent", "A2A: Multi-Agent Arch",
        "A2A 멀티에이전트 아키텍처 (LangGraph, port 9005)",
        "You are a Multi-Agent Architecture expert. Use call_multi_agent_arch tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Multi-Agent Arch (9005)"),

    make_a2a_agent("content_pipeline_agent", "A2A: Content Pipeline",
        "A2A 콘텐츠 파이프라인 (CrewAI, port 9006)",
        "You are a Content Pipeline agent. Use call_content_pipeline tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Content Pipeline (9006)"),

    make_a2a_agent("job_hunter_agent", "A2A: Job Hunter",
        "A2A 구직 자동화 (CrewAI, port 9007)",
        "You are a Job Hunter agent. Use call_job_hunter tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Job Hunter (9007)"),

    make_a2a_agent("news_reader_agent", "A2A: News Reader",
        "A2A 뉴스 수집 (CrewAI, port 9008)",
        "You are a News Reader agent. Use call_news_reader tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: News Reader (9008)"),

    make_a2a_agent("youtube_thumbnail_agent", "A2A: YouTube Thumbnail",
        "A2A YouTube 썸네일 생성 (LangGraph, port 9009)",
        "You are a YouTube Thumbnail maker. Use call_youtube_thumbnail tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: YouTube Thumbnail (9009)"),

    make_a2a_agent("workflow_testing_agent", "A2A: Workflow Testing",
        "A2A 워크플로우 테스팅 (LangGraph, port 9010)",
        "You are a Workflow Testing agent. Use call_workflow_testing tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Workflow Testing (9010)"),

    make_a2a_agent("deployment_agent", "A2A: Deployment Agent",
        "A2A 프로덕션 배포 (OpenAI Agents, port 9011)",
        "You are a Deployment agent. Use call_deployment_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Deployment Agent (9011)"),

    make_a2a_agent("financial_analyst_agent", "A2A: Financial Analyst",
        "A2A 금융 분석 - 주식/뉴스 (Google ADK, port 9012)",
        "You are a Financial Analyst agent. Use call_financial_analyst tool for stocks, news, investment. Respond in user's language. When done, say TERMINATE.",
        "A2A: Financial Analyst (9012)"),

    make_a2a_agent("deep_research_agent", "A2A: Deep Research",
        "A2A 심층 리서치 (AutoGen, port 9013)",
        "You are a Deep Research agent. Use call_deep_research tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Deep Research (9013)"),

    make_a2a_agent("email_refiner_agent", "A2A: Email Refiner",
        "A2A 이메일 개선 (Google ADK, port 9014)",
        "You are an Email Refiner agent. Use call_email_refiner tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Email Refiner (9014)"),

    make_a2a_agent("youtube_shorts_agent", "A2A: YouTube Shorts",
        "A2A YouTube Shorts 제작 (Google ADK, port 9015)",
        "You are a YouTube Shorts maker. Use call_youtube_shorts tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: YouTube Shorts (9015)"),

    make_a2a_agent("workflow_arch_agent", "A2A: Workflow Arch",
        "A2A 워크플로우 아키텍처 (LangGraph, port 9016)",
        "You are a Workflow Architecture agent. Use call_workflow_arch tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: Workflow Arch (9016)"),

    make_a2a_agent("first_agent", "A2A: First Agent",
        "A2A 기본 에이전트 (OpenAI SDK, port 9017)",
        "You are a basic agent with weather tool. Use call_first_agent tool. Respond in user's language. When done, say TERMINATE.",
        "A2A: First Agent (9017)"),
]

# Add to gallery agents
cfg["components"]["agents"].extend(new_agents)

# Update version
cfg["metadata"]["version"] = "5.0.0"
cfg["metadata"]["description"] = (
    "Auto-Claude + Full A2A Gallery. "
    "Build/Spec/QA teams + 23 individual A2A agents (each with own tool). "
    "Agents can be freely combined into custom teams for workflow design."
)

conn.execute("UPDATE gallery SET config = ? WHERE id = 11",
    (json.dumps(cfg, ensure_ascii=False),))
conn.commit()

# Verify
row2 = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg2 = json.loads(row2[0])
agents = cfg2["components"]["agents"]
print("=== Gallery 11 v5.0.0 ===")
print(f"Total agents: {len(agents)}")
print()

a2a_count = 0
for a in agents:
    label = a.get("label", "?")
    tools = a.get("config", {}).get("tools", [])
    tool_names = [t.get("label", "") for t in tools]
    if "A2A" in label:
        a2a_count += 1
        print(f"  * {label} -> {tool_names}")
    else:
        print(f"  {label}")

print(f"\nA2A agents: {a2a_count}")
total = sum(len(v) for v in cfg2["components"].values())
print(f"Total components: {total}")

conn.close()
print("\nDONE")

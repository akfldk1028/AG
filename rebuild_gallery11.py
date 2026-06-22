"""Rebuild Gallery 11 with Auto-Claude components"""
import sqlite3, json, copy

conn = sqlite3.connect(r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db")

# Default Gallery에서 tools/terminations/workbenches 가져오기
row = conn.execute("SELECT config FROM gallery WHERE id=10").fetchone()
default_cfg = json.loads(row[0])

# =============================================
# MODEL 정의
# =============================================
def make_model(label, model_id, desc):
    return {
        "provider": "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient",
        "component_type": "model", "version": 1, "component_version": 1,
        "label": label, "description": desc,
        "config": {"model": model_id}
    }

model_opus = make_model("Claude Opus 4.5 (Max OAuth)", "claude-opus-4-5-20251101",
    "Claude Opus 4.5 - Max OAuth. Auto-Claude Complex/Auto profile.")
model_sonnet = make_model("Claude Sonnet 4.5 (Max OAuth)", "claude-sonnet-4-5-20250929",
    "Claude Sonnet 4.5 - Max OAuth. Auto-Claude Balanced profile.")
model_haiku = make_model("Claude Haiku 4.5 (Max OAuth)", "claude-haiku-4-5-20251001",
    "Claude Haiku 4.5 - Max OAuth. Auto-Claude Quick Edits profile.")

# =============================================
# AGENT 정의
# =============================================
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

user_proxy = {
    "provider": "autogen_agentchat.agents.UserProxyAgent",
    "component_type": "agent", "version": 1, "component_version": 1,
    "description": "A human user proxy agent.",
    "label": "UserProxyAgent",
    "config": {"name": "user_proxy", "description": "A human user proxy."}
}

# Build Pipeline Agents
planner = make_agent("planner_agent", "Auto-Claude Planner",
    "Planner Agent - codebase investigation then subtask-based implementation plan.",
    "You are the Planner Agent in an autonomous development process. Your job is to create a subtask-based implementation plan. Investigate the codebase deeply first, then create ordered subtasks that respect dependencies. Each subtask should be scoped to one service. When done, say TERMINATE.",
    model_opus)

coder = make_agent("coder_agent", "Auto-Claude Coder",
    "Coder Agent - implements subtasks one at a time, verifies each.",
    "You are the Coding Agent. Work on ONE subtask at a time. Complete it, verify it, move on. Use relative paths. Never assume paths exist - check first. When all subtasks are done, say TERMINATE.",
    model_sonnet)

qa_reviewer = make_agent("qa_reviewer_agent", "Auto-Claude QA Reviewer",
    "QA Reviewer - validates completeness, correctness, production-readiness.",
    "You are the QA Reviewer Agent. Validate that the implementation is complete, correct, and production-ready. Check for edge cases, missing tests, security vulnerabilities, console errors, and broken functionality. If everything passes, say APPROVED. If issues found, describe them clearly for the QA Fixer.",
    model_opus)

qa_fixer = make_agent("qa_fixer_agent", "Auto-Claude QA Fixer",
    "QA Fixer - fixes all issues found by QA Reviewer.",
    "You are the QA Fix Agent. Fix ALL issues found by the QA Reviewer efficiently and correctly. Do not introduce new issues. When all fixes are complete, say FIXED.",
    model_opus)

# Spec Agents
spec_writer = make_agent("spec_writer_agent", "Auto-Claude Spec Writer",
    "Spec Writer - synthesizes context into actionable spec.md.",
    "You are the Spec Writer Agent. Read project_index.json, requirements.json, and context.json, then write a complete spec.md document with all required sections. Do not interact with the user. When done, say TERMINATE.",
    model_opus)

spec_critic = make_agent("spec_critic_agent", "Auto-Claude Spec Critic",
    "Spec Critic - deep analysis to find spec issues before implementation.",
    "You are the Spec Critic Agent. Use deep analytical thinking to critically review spec.md. Find issues, inconsistencies, missing requirements, and fix them. Output a critique_report.json summarizing issues and fixes. When done, say TERMINATE.",
    model_opus)

# Utility Agents
insights = make_agent("insights_agent", "Auto-Claude Insights",
    "Insights Agent - codebase analysis and pattern discovery.",
    "You are the Insights Agent. Analyze code and provide insights about patterns, issues, and improvements. When done, say TERMINATE.",
    model_sonnet)

agents = [planner, coder, qa_reviewer, qa_fixer, spec_writer, spec_critic, insights, user_proxy]

# =============================================
# TERMINATION 정의
# =============================================
term_terminate = {
    "provider": "autogen_agentchat.conditions.TextMentionTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Terminate when TERMINATE is mentioned.",
    "label": "TextMentionTermination",
    "config": {"text": "TERMINATE"}
}
term_approved = {
    "provider": "autogen_agentchat.conditions.TextMentionTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Terminate when APPROVED is mentioned.",
    "label": "ApprovedTermination",
    "config": {"text": "APPROVED"}
}
term_max20 = {
    "provider": "autogen_agentchat.conditions.MaxMessageTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Max 20 messages.",
    "label": "MaxMessageTermination(20)",
    "config": {"max_messages": 20, "include_agent_event": False}
}
term_max10 = {
    "provider": "autogen_agentchat.conditions.MaxMessageTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Max 10 messages.",
    "label": "MaxMessageTermination(10)",
    "config": {"max_messages": 10, "include_agent_event": False}
}

def make_or_term(*conditions):
    return {
        "provider": "autogen_agentchat.base.OrTerminationCondition",
        "component_type": "termination", "version": 1, "component_version": 1,
        "label": "OrTerminationCondition",
        "config": {"conditions": list(conditions)}
    }

# =============================================
# TEAM 정의
# =============================================
def make_team(label, desc, provider, participants, termination, extra_config=None):
    team_name = provider.split(".")[-1]
    cfg = {
        "name": team_name,
        "description": desc,
        "participants": [copy.deepcopy(p) for p in participants],
        "termination_condition": termination,
        "emit_team_events": False
    }
    if extra_config:
        cfg.update(extra_config)
    return {
        "provider": provider,
        "component_type": "team", "version": 1, "component_version": 1,
        "description": desc, "label": label,
        "config": cfg
    }

# Sonnet versions for Balanced team
planner_s = make_agent("planner_agent", "Planner (Sonnet)", "Planner - Sonnet Balanced.",
    "You are the Planner Agent. Create subtask-based implementation plans. When done, say TERMINATE.",
    model_sonnet)
coder_s = make_agent("coder_agent", "Coder (Sonnet)", "Coder - Sonnet Balanced.",
    "You are the Coding Agent. Work on ONE subtask at a time. When done, say TERMINATE.",
    model_sonnet)
qa_s = make_agent("qa_reviewer_agent", "QA Reviewer (Sonnet)", "QA Reviewer - Sonnet Balanced.",
    "You are the QA Reviewer. Validate implementation. If approved, say APPROVED. Otherwise describe issues.",
    model_sonnet)

teams = [
    # 1. Build Pipeline (Auto - Opus)
    make_team("Auto-Claude Build (Auto/Opus)",
        "Auto-Claude Build Pipeline: Planner -> Coder -> QA Reviewer. Opus model, optimized thinking.",
        "autogen_agentchat.teams.RoundRobinGroupChat",
        [planner, coder, qa_reviewer],
        make_or_term(term_terminate, term_approved, term_max20)),

    # 2. Build Pipeline (Balanced - Sonnet)
    make_team("Auto-Claude Build (Balanced/Sonnet)",
        "Auto-Claude Build Pipeline: Planner -> Coder -> QA Reviewer. Sonnet model, balanced speed/quality.",
        "autogen_agentchat.teams.RoundRobinGroupChat",
        [planner_s, coder_s, qa_s],
        make_or_term(term_terminate, term_approved, term_max20)),

    # 3. Spec Creation Team
    make_team("Auto-Claude Spec Creation",
        "Spec creation: Spec Writer -> Spec Critic. Deep analysis with Opus.",
        "autogen_agentchat.teams.RoundRobinGroupChat",
        [spec_writer, spec_critic],
        make_or_term(term_terminate, term_max10)),

    # 4. QA Loop (Selector)
    make_team("Auto-Claude QA Loop",
        "QA loop: QA Reviewer <-> QA Fixer. Reviewer finds issues, Fixer resolves them.",
        "autogen_agentchat.teams.SelectorGroupChat",
        [qa_reviewer, qa_fixer],
        make_or_term(term_approved, term_max10),
        extra_config={
            "selector_prompt": "You are coordinating a QA validation loop.\n\nAvailable agents:\n- qa_reviewer_agent: Validates implementation completeness and correctness\n- qa_fixer_agent: Fixes issues found by the reviewer\n\nRules:\n1. Always start with qa_reviewer_agent\n2. If issues are found, select qa_fixer_agent\n3. After fixes, select qa_reviewer_agent to re-validate\n4. Never select the same agent twice in a row\n\nReturn ONLY the agent name.",
            "allow_repeated_speaker": False
        }),
]

# =============================================
# GALLERY CONFIG 조립
# =============================================
gallery_config = {
    "id": "claude_max_models",
    "name": "Claude Max Models (OAuth) - Auto-Claude",
    "metadata": {
        "author": "AG_Cohub + Auto-Claude",
        "description": "Auto-Claude project-based Claude Max OAuth Gallery. Includes Build Pipeline, Spec Creation, QA Loop teams with Planner/Coder/QA/Spec agents.",
        "version": "2.0.0"
    },
    "components": {
        "models": [model_opus, model_sonnet, model_haiku],
        "agents": agents,
        "teams": teams,
        "tools": default_cfg["components"]["tools"],
        "terminations": default_cfg["components"]["terminations"],
        "workbenches": default_cfg["components"]["workbenches"],
    }
}

# DB 업데이트
conn.execute("UPDATE gallery SET config = ? WHERE id = 11",
    (json.dumps(gallery_config, ensure_ascii=False),))
conn.commit()

# 검증
row2 = conn.execute("SELECT config FROM gallery WHERE id=11").fetchone()
cfg2 = json.loads(row2[0])
comps = cfg2["components"]
print("=== Gallery 11 Updated (Auto-Claude Based) ===")
print(f"name: {cfg2['name']}")
print(f"version: {cfg2['metadata']['version']}")
for key in comps:
    items = comps[key]
    print(f"\n{key}: {len(items)} items")
    for item in items:
        if isinstance(item, dict):
            label = item.get("label", "?")
            ct = item.get("component_type", "?")
            mc = item.get("config", {}).get("model_client", {})
            model_info = mc.get("config", {}).get("model", "") if mc else ""
            if ct == "team":
                parts = item.get("config", {}).get("participants", [])
                provider = item.get("provider", "").split(".")[-1]
                print(f"  [{ct}] {label} ({provider}, {len(parts)} agents)")
            elif model_info:
                print(f"  [{ct}] {label} (model: {model_info})")
            else:
                print(f"  [{ct}] {label}")

conn.close()
print("\nDONE")

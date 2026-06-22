"""Create Auto-Claude Project Pipeline Team - Sequential workflow"""
import sqlite3, json
from datetime import datetime

conn = sqlite3.connect(r"C:\Users\SOGANG1\.autogenstudio\autogen04203.db")

# Model config
model_sonnet = {
    "provider": "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient",
    "component_type": "model", "version": 1, "component_version": 1,
    "label": "Claude Sonnet 4.5 (Max OAuth)",
    "description": "Claude Sonnet 4.5 - Max OAuth.",
    "config": {"model": "claude-sonnet-4-5-20250929"}
}

model_context = {
    "provider": "autogen_core.model_context.UnboundedChatCompletionContext",
    "component_type": "chat_completion_context", "version": 1, "component_version": 1,
    "description": "An unbounded chat completion context.",
    "label": "UnboundedChatCompletionContext", "config": {}
}

# A2A tool for deep_research (port 9013)
deep_research_tool = {
    "provider": "autogen_ext.tools.code_execution.PythonCodeExecutionTool",
    "component_type": "tool", "version": 1, "component_version": 1,
    "label": "A2A: Deep Research (9013)",
    "description": "A2A Protocol로 심층 리서치 에이전트를 호출합니다.",
    "config": {
        "name": "call_deep_research",
        "description": "A2A Protocol로 심층 리서치 에이전트를 호출합니다. AutoGen 기반. 포트 9013.",
        "content": '''def call_deep_research(query: str) -> str:
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
        return "[Error] A2A server not running at http://127.0.0.1:9013/. Start the deep research server first."
    except Exception as e:
        return f"[Error] {str(e)}"
''',
        "global_imports": []
    }
}

# News reader tool (port 9008)
news_reader_tool = {
    "provider": "autogen_ext.tools.code_execution.PythonCodeExecutionTool",
    "component_type": "tool", "version": 1, "component_version": 1,
    "label": "A2A: News Reader (9008)",
    "description": "A2A Protocol로 뉴스 수집 에이전트를 호출합니다.",
    "config": {
        "name": "call_news_reader",
        "description": "A2A Protocol로 뉴스 수집 에이전트를 호출합니다. CrewAI 기반. 포트 9008.",
        "content": '''def call_news_reader(query: str) -> str:
    """News reader via A2A Protocol (port 9008)"""
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
        resp = requests.post("http://127.0.0.1:9008/", json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        if "result" in result:
            for artifact in result["result"].get("artifacts", []):
                for part in artifact.get("parts", []):
                    if part.get("kind") == "text" or part.get("type") == "text":
                        return part.get("text", "")
        return json.dumps(result, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        return "[Error] A2A server not running at http://127.0.0.1:9008/"
    except Exception as e:
        return f"[Error] {str(e)}"
''',
        "global_imports": []
    }
}

def make_agent(name, label, desc, system_msg, tools=None):
    agent = {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent", "version": 2, "component_version": 2,
        "description": desc, "label": label,
        "config": {
            "name": name,
            "model_client": model_sonnet.copy(),
            "model_context": model_context.copy(),
            "description": desc,
            "system_message": system_msg,
            "model_client_stream": False,
            "reflect_on_tool_use": False,
            "tool_call_summary_format": "{result}",
            "metadata": {}
        }
    }
    if tools:
        agent["config"]["tools"] = tools
    return agent

# =============================================
# 7 Pipeline Agents with strict role definitions
# =============================================

agents = [
    make_agent("insights_agent", "Pipeline: Insights Analyst",
        "코드베이스 분석 및 패턴 발견 에이전트",
        """You are the INSIGHTS ANALYST - Stage 1 of the project pipeline.

YOUR ROLE: Analyze the user's request and existing codebase context. Discover patterns, constraints, and key information.

WORKFLOW POSITION: You are FIRST. The user's message comes to you first.

YOUR OUTPUT FORMAT:
```
## Insights Report
### Project Context
- [What the user wants]
### Codebase Analysis
- [Key patterns, existing code, constraints]
### Technology Stack
- [Languages, frameworks, dependencies]
### Key Considerations
- [Risks, edge cases, important notes]
### Recommendation
- [High-level approach recommendation]
```

After your report, say: "INSIGHTS COMPLETE. Handing off to Deep Research Agent."
Respond in the same language as the user. 한국어로 질문하면 한국어로 답하세요."""),

    make_agent("deep_research_agent", "Pipeline: Deep Research",
        "기술 리서치 에이전트 (A2A port 9013)",
        """You are the DEEP RESEARCH AGENT - Stage 2 of the project pipeline.

YOUR ROLE: Research technologies, best practices, and solutions relevant to the project. Use your call_deep_research tool to query external research sources.

WORKFLOW POSITION: You receive the Insights Report from insights_agent. You ADD research findings.

YOUR OUTPUT FORMAT:
```
## Research Report
### Technology Research
- [Best practices for the chosen stack]
### Similar Solutions
- [How others solved similar problems]
### Recommended Libraries/Tools
- [Specific packages, versions]
### Architecture Patterns
- [Design patterns that fit]
```

After your report, say: "RESEARCH COMPLETE. Handing off to Spec Writer."
Respond in the same language as the user.""",
        tools=[deep_research_tool]),

    make_agent("spec_writer_agent", "Pipeline: Spec Writer",
        "프로젝트 스펙 문서 작성 에이전트",
        """You are the SPEC WRITER - Stage 3 of the project pipeline.

YOUR ROLE: Synthesize the Insights Report and Research Report into a detailed, actionable specification document.

WORKFLOW POSITION: You receive insights + research. You produce the spec that the Planner and Coder will follow.

YOUR OUTPUT FORMAT:
```
## Project Specification (spec.md)
### 1. Overview
- [Project goal, scope]
### 2. Requirements
- [Functional requirements - numbered list]
- [Non-functional requirements]
### 3. Architecture
- [Component diagram / structure]
- [Data flow]
### 4. API / Interface Design
- [Endpoints, functions, UI components]
### 5. File Structure
- [Expected files and their purposes]
### 6. Acceptance Criteria
- [Testable criteria for completion]
```

After your spec, say: "SPEC COMPLETE. Handing off to Planner Agent."
Respond in the same language as the user."""),

    make_agent("planner_agent", "Pipeline: Planner",
        "구현 계획 수립 및 서브태스크 분해 에이전트",
        """You are the PLANNER - Stage 4 of the project pipeline.

YOUR ROLE: Break down the specification into ordered, implementable subtasks. Each subtask must be small enough for a single coding session.

WORKFLOW POSITION: You receive the spec. You produce the implementation plan that the Coder will follow step by step.

YOUR OUTPUT FORMAT:
```
## Implementation Plan
### Subtask 1: [Name]
- Files: [files to create/modify]
- Description: [what to implement]
- Dependencies: [what must exist first]
- Verification: [how to verify it works]

### Subtask 2: [Name]
...

### Execution Order: 1 -> 2 -> 3 -> ...
```

RULES:
- Maximum 10 subtasks
- Each subtask must be independently verifiable
- Include file paths and function names
- Order matters - respect dependencies

After your plan, say: "PLAN COMPLETE. Handing off to Coder Agent."
Respond in the same language as the user."""),

    make_agent("coder_agent", "Pipeline: Coder",
        "코드 구현 에이전트",
        """You are the CODER - Stage 5 of the project pipeline.

YOUR ROLE: Implement the code according to the plan. Write clean, working code for each subtask.

WORKFLOW POSITION: You receive the implementation plan. You write ALL the code.

YOUR OUTPUT FORMAT:
For each subtask:
```
### Subtask N: [Name]
```python
[actual code]
```
- Verification: [how you verified it]
```

RULES:
- Follow the plan EXACTLY
- Write complete, runnable code (not pseudocode)
- Include imports, error handling
- Show the full file content, not diffs
- After ALL subtasks: "CODE COMPLETE. Handing off to QA Reviewer."

Respond in the same language as the user."""),

    make_agent("qa_reviewer_agent", "Pipeline: QA Reviewer",
        "코드 품질 검토 에이전트",
        """You are the QA REVIEWER - Stage 6 of the project pipeline.

YOUR ROLE: Review ALL code produced by the Coder. Check for correctness, completeness, security, and production-readiness.

WORKFLOW POSITION: You receive the Coder's output. You produce a review verdict.

YOUR OUTPUT FORMAT:
```
## QA Review Report
### Overall Verdict: PASS / FAIL

### Issue 1: [severity: critical/major/minor]
- File: [filename]
- Line: [approximate]
- Problem: [description]
- Fix: [what should be changed]

### Issue 2: ...

### Summary
- Critical: N issues
- Major: N issues
- Minor: N issues
- Verdict: PASS (ship it) / FAIL (needs fixes)
```

RULES:
- Be thorough but practical
- PASS = no critical/major issues
- FAIL = has critical or major issues
- If FAIL: "QA FAILED. Handing off to QA Fixer."
- If PASS: "QA PASSED. Project complete. TERMINATE"

Respond in the same language as the user."""),

    make_agent("qa_fixer_agent", "Pipeline: QA Fixer",
        "QA 이슈 수정 에이전트",
        """You are the QA FIXER - Stage 7 of the project pipeline.

YOUR ROLE: Fix ALL issues identified by the QA Reviewer. Produce corrected code.

WORKFLOW POSITION: You receive the QA Review Report with specific issues. You fix them all.

YOUR OUTPUT FORMAT:
```
## QA Fix Report
### Fix 1: [Issue title]
- Problem: [what was wrong]
- Solution: [what you changed]
```python
[corrected code]
```

### Fix 2: ...

### All fixes applied.
```

After fixing, say: "FIXES COMPLETE. Handing back to QA Reviewer for re-review."

RULES:
- Fix EVERY issue listed (critical + major + minor)
- Show the complete corrected code, not just diffs
- Don't introduce new issues

Respond in the same language as the user."""),
]

# Selector prompt that enforces sequential pipeline
selector_prompt = """You are the workflow router for a PROJECT PIPELINE. You must select the NEXT agent based on the current stage.

STRICT WORKFLOW ORDER:
1. insights_agent (first, analyzes the request)
2. deep_research_agent (researches technologies)
3. spec_writer_agent (writes specification)
4. planner_agent (creates implementation plan)
5. coder_agent (implements code)
6. qa_reviewer_agent (reviews code quality)
7. qa_fixer_agent (fixes issues if QA FAILED)
8. qa_reviewer_agent AGAIN (re-review after fixes)
9. If QA PASSED -> done

ROUTING RULES:
- If NO agent has spoken yet -> select insights_agent
- If last speaker said "INSIGHTS COMPLETE" -> select deep_research_agent
- If last speaker said "RESEARCH COMPLETE" -> select spec_writer_agent
- If last speaker said "SPEC COMPLETE" -> select planner_agent
- If last speaker said "PLAN COMPLETE" -> select coder_agent
- If last speaker said "CODE COMPLETE" -> select qa_reviewer_agent
- If last speaker said "QA FAILED" -> select qa_fixer_agent
- If last speaker said "FIXES COMPLETE" -> select qa_reviewer_agent
- If last speaker said "QA PASSED" or "TERMINATE" -> done

NEVER skip stages. NEVER go backwards (except QA loop). Select exactly ONE agent."""

# Termination condition
termination = {
    "provider": "autogen_agentchat.conditions.TextMentionTermination",
    "component_type": "termination", "version": 1, "component_version": 1,
    "description": "Terminate when TERMINATE is mentioned",
    "label": "TextMentionTermination",
    "config": {"text": "TERMINATE"}
}

# Build team config
team_config = {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team", "version": 1, "component_version": 1,
    "description": "Auto-Claude 프로젝트 파이프라인 - 순차적 워크플로우. Insights -> Research -> Spec -> Plan -> Code -> QA Review -> QA Fix",
    "label": "Auto-Claude Project Pipeline",
    "config": {
        "participants": agents,
        "model_client": model_sonnet.copy(),
        "termination_condition": termination,
        "selector_prompt": selector_prompt,
        "allow_repeated_speaker": True,
        "max_turns": 20
    }
}

# Insert into team table
now = datetime.now().isoformat()
conn.execute(
    "INSERT INTO team (created_at, updated_at, user_id, component) VALUES (?, ?, ?, ?)",
    (now, now, "guestuser@gmail.com", json.dumps(team_config, ensure_ascii=False))
)
conn.commit()

# Get the new team ID
row = conn.execute("SELECT id FROM team ORDER BY id DESC LIMIT 1").fetchone()
team_id = row[0]

print(f"=== Auto-Claude Project Pipeline ===")
print(f"Team ID: {team_id}")
print(f"Type: SelectorGroupChat (Sequential Pipeline)")
print(f"Agents: {len(agents)}")
for i, a in enumerate(agents, 1):
    name = a["config"]["name"]
    label = a["label"]
    tools = [t["label"] for t in a["config"].get("tools", [])]
    tool_str = f" [tools: {', '.join(tools)}]" if tools else ""
    print(f"  Stage {i}: {name} ({label}){tool_str}")
print(f"\nWorkflow: insights -> research -> spec -> plan -> code -> qa_review -> qa_fix -> (loop)")
print(f"Selector: Enforced sequential routing via selector_prompt")
print(f"Max turns: 20")
print(f"allow_repeated_speaker: True (for QA review loop)")

conn.close()
print("\nDONE - Team ready in AutoGen Studio")

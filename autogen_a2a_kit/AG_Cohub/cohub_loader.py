"""
AG_Cohub Loader - AutoGen Studio 연동 스크립트

이 스크립트는 AG_Cohub의 협업 패턴을 AutoGen Studio에서
실행 가능한 팀 템플릿으로 변환하고 등록합니다.

사용법:
    python cohub_loader.py --action generate  # 템플릿 생성
    python cohub_loader.py --action import    # AutoGen Studio에 import
    python cohub_loader.py --action list      # 사용 가능한 패턴 목록
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# AutoGen imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.conditions import (
        MaxMessageTermination,
        TextMentionTermination,
    )
    from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat, Swarm
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen packages not available. Some features disabled.")

# ★ Model Factory (Claude 및 다중 모델 지원 - 2026-01-24)
try:
    from .model_factory import get_model_client, list_available_models, check_provider_availability
    MODEL_FACTORY_AVAILABLE = True
except ImportError:
    # Fallback: 직접 import
    try:
        from model_factory import get_model_client, list_available_models, check_provider_availability
        MODEL_FACTORY_AVAILABLE = True
    except ImportError:
        MODEL_FACTORY_AVAILABLE = False
        print("Warning: model_factory not available. Using OpenAI only.")


class CoHubLoader:
    """AG_Cohub 패턴을 AutoGen Studio 팀 템플릿으로 변환"""

    def __init__(self, cohub_path: Optional[str] = None):
        self.cohub_path = Path(cohub_path or Path(__file__).parent)
        self.patterns_path = self.cohub_path / "patterns"
        self.templates_path = self.cohub_path / "templates"
        self.templates_path.mkdir(exist_ok=True)

    def list_patterns(self) -> list:
        """사용 가능한 패턴 목록 반환"""
        patterns = []
        for f in sorted(self.patterns_path.glob("*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                patterns.append({
                    "id": data["id"],
                    "name": data["name"]["ko"],
                    "complexity": data["complexity"],
                    "file": f.name
                })
        return patterns

    def load_pattern(self, pattern_id: str) -> dict:
        """특정 패턴 JSON 로드"""
        for f in self.patterns_path.glob("*.json"):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if data["id"] == pattern_id:
                    return data
        raise ValueError(f"Pattern not found: {pattern_id}")

    def generate_sequential_template(self, model_name: str = "claude-sonnet-4-5") -> dict:
        """Sequential (RoundRobinGroupChat) 팀 템플릿 생성

        ★ Claude 모델 지원 (2026-01-24):
           model_name에 claude-* 모델을 직접 사용할 수 있습니다.
           예: "claude-sonnet-4-5", "claude-3-5-haiku", "gpt-4o-mini"
        """
        if not AUTOGEN_AVAILABLE:
            return self._generate_static_sequential_template()

        # ★ Model Factory를 통한 다중 모델 지원
        if MODEL_FACTORY_AVAILABLE:
            model = get_model_client(model_name)
        else:
            # Fallback: OpenAI only
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = OpenAIChatCompletionClient(model=model_name)

        agent1 = AssistantAgent(
            name="researcher",
            system_message="당신은 리서처입니다. 주어진 주제에 대해 조사하고 정보를 수집하세요.",
            model_client=model,
        )

        agent2 = AssistantAgent(
            name="writer",
            system_message="당신은 작가입니다. 리서처가 수집한 정보를 바탕으로 글을 작성하세요.",
            model_client=model,
        )

        agent3 = AssistantAgent(
            name="reviewer",
            system_message="당신은 리뷰어입니다. 작성된 글을 검토하고 피드백을 제공하세요. 완료되면 TERMINATE라고 말하세요.",
            model_client=model,
        )

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(10)

        team = RoundRobinGroupChat(
            participants=[agent1, agent2, agent3],
            termination_condition=termination
        )

        return team.dump_component().model_dump()

    def generate_selector_template(self, model_name: str = "claude-sonnet-4-5") -> dict:
        """Selector (SelectorGroupChat) 팀 템플릿 생성"""
        if not AUTOGEN_AVAILABLE:
            return self._generate_static_selector_template()

        # ★ Model Factory를 통한 다중 모델 지원
        if MODEL_FACTORY_AVAILABLE:
            model = get_model_client(model_name)
        else:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = OpenAIChatCompletionClient(model=model_name)

        coordinator = AssistantAgent(
            name="coordinator",
            system_message="당신은 코디네이터입니다. 다른 전문가에게 적합하지 않은 일반적인 질문을 처리합니다.",
            description="일반적인 질문 및 조율 담당",
            model_client=model,
        )

        history_expert = AssistantAgent(
            name="history_expert",
            system_message="당신은 역사 전문가입니다. 역사 관련 질문에 상세하게 답변하세요.",
            description="역사 관련 질문 전문가",
            model_client=model,
        )

        science_expert = AssistantAgent(
            name="science_expert",
            system_message="당신은 과학 전문가입니다. 과학 관련 질문에 상세하게 답변하세요.",
            description="과학 관련 질문 전문가",
            model_client=model,
        )

        math_expert = AssistantAgent(
            name="math_expert",
            system_message="당신은 수학 전문가입니다. 수학 문제를 풀고 설명하세요. 완료되면 TERMINATE라고 말하세요.",
            description="수학 문제 해결 전문가",
            model_client=model,
        )

        selector_prompt = """다음 역할들이 있습니다: {roles}

대화 내용을 읽고 다음 발언에 가장 적합한 역할을 선택하세요:
- 역사 관련 질문: history_expert
- 과학 관련 질문: science_expert
- 수학 관련 질문: math_expert
- 기타 일반 질문: coordinator

{history}

역할 이름만 반환하세요."""

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(10)

        team = SelectorGroupChat(
            participants=[coordinator, history_expert, science_expert, math_expert],
            model_client=model,
            selector_prompt=selector_prompt,
            termination_condition=termination
        )

        return team.dump_component().model_dump()

    def generate_handoff_template(self, model_name: str = "claude-sonnet-4-5") -> dict:
        """Handoff (Swarm) 팀 템플릿 생성"""
        if not AUTOGEN_AVAILABLE:
            return self._generate_static_handoff_template()

        # ★ Model Factory를 통한 다중 모델 지원
        if MODEL_FACTORY_AVAILABLE:
            model = get_model_client(model_name)
        else:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = OpenAIChatCompletionClient(model=model_name)

        triage = AssistantAgent(
            name="triage_agent",
            system_message="""당신은 고객 서비스 분류 담당입니다.
고객의 문의를 분석하고 적절한 담당자에게 연결하세요:
- 기술 지원 필요: 'support_agent에게 전달합니다'
- 영업 문의: 'sales_agent에게 전달합니다'
- 환불/반품: 'refund_agent에게 전달합니다'""",
            model_client=model,
            handoffs=["support_agent", "sales_agent", "refund_agent"],
        )

        support = AssistantAgent(
            name="support_agent",
            system_message="당신은 기술 지원 담당입니다. 기술적 문제를 해결하세요. 해결 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        sales = AssistantAgent(
            name="sales_agent",
            system_message="당신은 영업 담당입니다. 제품 문의와 구매를 도와주세요. 완료 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        refund = AssistantAgent(
            name="refund_agent",
            system_message="당신은 환불 담당입니다. 환불 및 반품을 처리하세요. 완료 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(15)

        team = Swarm(
            participants=[triage, support, sales, refund],
            termination_condition=termination
        )

        return team.dump_component().model_dump()

    def generate_debate_template(self, model_name: str = "claude-sonnet-4-5") -> dict:
        """Debate 팀 템플릿 생성"""
        if not AUTOGEN_AVAILABLE:
            return self._generate_static_debate_template()

        # ★ Model Factory를 통한 다중 모델 지원
        if MODEL_FACTORY_AVAILABLE:
            model = get_model_client(model_name)
        else:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = OpenAIChatCompletionClient(model=model_name)

        advocate = AssistantAgent(
            name="advocate",
            system_message="""당신은 제안의 지지자입니다.
- 장점과 기회를 강조하세요
- 반대 의견에 논리적으로 반박하세요
- 긍정적인 관점에서 분석하세요""",
            description="제안을 지지하고 장점을 강조",
            model_client=model,
        )

        critic = AssistantAgent(
            name="critic",
            system_message="""당신은 비평가입니다.
- 약점, 리스크, 잠재적 문제를 지적하세요
- 지지자의 주장에 도전하세요
- 비판적 관점에서 분석하세요""",
            description="비판적 분석과 리스크 지적",
            model_client=model,
        )

        judge = AssistantAgent(
            name="judge",
            system_message="""당신은 중립적 심판입니다.
- 양측의 논증을 공정하게 평가하세요
- 균형 잡힌 최종 판단을 내리세요
- 결론을 내린 후 TERMINATE라고 말하세요""",
            description="중립적 심판 및 최종 결정",
            model_client=model,
        )

        selector_prompt = """토론 참가자: {roles}

토론 규칙:
1. advocate와 critic이 번갈아 발언합니다
2. 각 측이 2-3회 발언 후 judge가 결론을 내립니다

대화 기록:
{history}

다음 발언자를 선택하세요. 역할 이름만 반환하세요."""

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(8)

        team = SelectorGroupChat(
            participants=[advocate, critic, judge],
            model_client=model,
            selector_prompt=selector_prompt,
            termination_condition=termination
        )

        return team.dump_component().model_dump()

    def generate_reflection_template(self, model_name: str = "claude-sonnet-4-5") -> dict:
        """Reflection 팀 템플릿 생성"""
        if not AUTOGEN_AVAILABLE:
            return self._generate_static_reflection_template()

        # ★ Model Factory를 통한 다중 모델 지원
        if MODEL_FACTORY_AVAILABLE:
            model = get_model_client(model_name)
        else:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = OpenAIChatCompletionClient(model=model_name)

        generator = AssistantAgent(
            name="generator",
            system_message="""당신은 콘텐츠 생성자입니다.
주어진 작업을 수행하고 결과를 생성하세요.
비평을 받으면 피드백을 반영하여 개선된 버전을 제공하세요.""",
            model_client=model,
        )

        critic = AssistantAgent(
            name="critic",
            system_message="""당신은 품질 검토자입니다.
생성된 결과를 검토하고 구체적인 개선점을 제시하세요.
- 문제가 있으면: 구체적인 개선 제안
- 충분히 좋으면: 'APPROVED'라고 말하세요""",
            model_client=model,
        )

        termination = TextMentionTermination("APPROVED") | TextMentionTermination("TERMINATE") | MaxMessageTermination(6)

        team = RoundRobinGroupChat(
            participants=[generator, critic],
            termination_condition=termination
        )

        return team.dump_component().model_dump()

    def _generate_static_sequential_template(self) -> dict:
        """정적 Sequential 템플릿 (AutoGen 없이)"""
        return {
            "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
            "component_type": "team",
            "version": 1,
            "description": "순차적 오케스트레이션 팀 - 리서처 → 작가 → 리뷰어",
            "label": "Sequential Team (Template)",
            "config": {
                "participants": [
                    {"name": "researcher", "type": "AssistantAgent"},
                    {"name": "writer", "type": "AssistantAgent"},
                    {"name": "reviewer", "type": "AssistantAgent"}
                ],
                "termination_condition": {
                    "type": "OrTermination",
                    "conditions": ["TextMentionTermination(TERMINATE)", "MaxMessageTermination(10)"]
                }
            },
            "_note": "이 템플릿은 AutoGen이 설치된 환경에서 cohub_loader.py를 실행하여 완전한 버전을 생성하세요."
        }

    def _generate_static_selector_template(self) -> dict:
        """정적 Selector 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.SelectorGroupChat",
            "component_type": "team",
            "version": 1,
            "description": "선택자 오케스트레이션 팀 - 질문 유형별 전문가 라우팅",
            "label": "Selector Team (Template)",
            "config": {
                "participants": [
                    {"name": "coordinator", "type": "AssistantAgent"},
                    {"name": "history_expert", "type": "AssistantAgent"},
                    {"name": "science_expert", "type": "AssistantAgent"},
                    {"name": "math_expert", "type": "AssistantAgent"}
                ],
                "selector_prompt": "역할 선택 프롬프트...",
                "model_client": {"model": "gpt-4o-mini"}
            },
            "_note": "이 템플릿은 AutoGen이 설치된 환경에서 cohub_loader.py를 실행하여 완전한 버전을 생성하세요."
        }

    def _generate_static_handoff_template(self) -> dict:
        """정적 Handoff 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.Swarm",
            "component_type": "team",
            "version": 1,
            "description": "핸드오프 팀 - 고객 서비스 라우팅",
            "label": "Handoff Team (Template)",
            "config": {
                "participants": [
                    {"name": "triage_agent", "handoffs": ["support_agent", "sales_agent", "refund_agent"]},
                    {"name": "support_agent", "handoffs": ["triage_agent"]},
                    {"name": "sales_agent", "handoffs": ["triage_agent"]},
                    {"name": "refund_agent", "handoffs": ["triage_agent"]}
                ]
            },
            "_note": "이 템플릿은 AutoGen이 설치된 환경에서 cohub_loader.py를 실행하여 완전한 버전을 생성하세요."
        }

    def _generate_static_debate_template(self) -> dict:
        """정적 Debate 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.SelectorGroupChat",
            "component_type": "team",
            "version": 1,
            "description": "토론 팀 - 찬성/반대/심판 구조",
            "label": "Debate Team (Template)",
            "config": {
                "participants": [
                    {"name": "advocate", "role": "지지자"},
                    {"name": "critic", "role": "비평가"},
                    {"name": "judge", "role": "심판"}
                ],
                "selector_prompt": "토론 규칙에 따른 발언자 선택..."
            },
            "_note": "이 템플릿은 AutoGen이 설치된 환경에서 cohub_loader.py를 실행하여 완전한 버전을 생성하세요."
        }

    def _generate_static_reflection_template(self) -> dict:
        """정적 Reflection 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
            "component_type": "team",
            "version": 1,
            "description": "반성 팀 - 생성 → 비평 → 개선 루프",
            "label": "Reflection Team (Template)",
            "config": {
                "participants": [
                    {"name": "generator", "role": "콘텐츠 생성"},
                    {"name": "critic", "role": "품질 검토"}
                ],
                "termination": "APPROVED 또는 최대 6회"
            },
            "_note": "이 템플릿은 AutoGen이 설치된 환경에서 cohub_loader.py를 실행하여 완전한 버전을 생성하세요."
        }

    def generate_all_templates(self, model_name: str = "claude-sonnet-4-5"):
        """모든 패턴의 템플릿 생성"""
        templates = {
            "sequential": self.generate_sequential_template(model_name),
            "selector": self.generate_selector_template(model_name),
            "handoff": self.generate_handoff_template(model_name),
            "debate": self.generate_debate_template(model_name),
            "reflection": self.generate_reflection_template(model_name),
        }

        for name, template in templates.items():
            output_file = self.templates_path / f"{name}_team.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print(f"Generated: {output_file}")

        return templates

    def import_to_autogen_studio(self, user_id: str = "admin"):
        """템플릿을 AutoGen Studio에 import (API 호출)"""
        import requests

        api_base = os.environ.get("AUTOGEN_STUDIO_API", "http://localhost:8081/api")

        for template_file in self.templates_path.glob("*_team.json"):
            with open(template_file, "r", encoding="utf-8") as f:
                template = json.load(f)

            try:
                response = requests.post(
                    f"{api_base}/teams/",
                    json={
                        "user_id": user_id,
                        "component": template
                    }
                )
                if response.status_code == 200:
                    print(f"Imported: {template_file.name}")
                else:
                    print(f"Failed to import {template_file.name}: {response.text}")
            except requests.exceptions.ConnectionError:
                print(f"Cannot connect to AutoGen Studio API at {api_base}")
                print("Make sure AutoGen Studio is running.")
                break

    def import_compact(self, template_dir: str = "templates_compact", user_id: str = "admin"):
        """Resolve compact templates and import to AutoGen Studio.

        Uses ref_resolver to expand $ref references before POSTing.
        """
        import requests

        # JSON_MODULES 경로: AG/autogen_a2a_kit/AG_Cohub/ → 3 levels up → repo root / JSON_MODULES
        json_modules_dir = Path(
            os.environ.get("JSON_MODULES_DIR",
                           Path(__file__).resolve().parent.parent.parent.parent / "JSON_MODULES")
        )
        if not json_modules_dir.exists():
            print(f"Error: JSON_MODULES not found at {json_modules_dir}")
            print("Set JSON_MODULES_DIR env var to override.")
            return

        sys.path.insert(0, str(json_modules_dir))
        try:
            from ref_resolver import resolve_file
        finally:
            sys.path.remove(str(json_modules_dir))

        api_base = os.environ.get("AUTOGEN_STUDIO_API", "http://localhost:8081/api")
        compact_dir = json_modules_dir / template_dir

        if not compact_dir.exists():
            print(f"Error: {compact_dir} not found")
            return

        for template_file in sorted(compact_dir.glob("*.json")):
            try:
                resolved = resolve_file(template_file, json_modules_dir)
                response = requests.post(
                    f"{api_base}/teams/",
                    json={"user_id": user_id, "component": resolved}
                )
                if response.status_code == 200:
                    team_id = response.json().get("id", "?")
                    print(f"Imported (compact): {template_file.name} -> id={team_id}")
                else:
                    print(f"Failed: {template_file.name}: {response.status_code} {response.text[:200]}")
            except requests.exceptions.ConnectionError:
                print(f"Cannot connect to AutoGen Studio API at {api_base}")
                break
            except Exception as e:
                print(f"Error resolving {template_file.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="AG_Cohub Loader - AutoGen Studio 연동")
    parser.add_argument("--action", choices=["list", "generate", "import", "compact"], default="list",
                       help="수행할 작업 (list: 패턴 목록, generate: 템플릿 생성, import: Studio에 등록, compact: $ref 템플릿 resolve+import)")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="사용할 모델 (기본: claude-sonnet-4-5, 옵션: gpt-4o-mini, claude-3-5-haiku 등)")
    parser.add_argument("--user-id", default="admin", help="AutoGen Studio 사용자 ID")

    args = parser.parse_args()

    loader = CoHubLoader()

    if args.action == "list":
        print("\n=== AG_Cohub 협업 패턴 목록 ===\n")
        patterns = loader.list_patterns()
        for p in patterns:
            print(f"  [{p['complexity']:12}] {p['id']:15} - {p['name']}")
        print(f"\n총 {len(patterns)}개 패턴")

    elif args.action == "generate":
        print(f"\n=== 템플릿 생성 (모델: {args.model}) ===\n")
        if not AUTOGEN_AVAILABLE:
            print("Warning: AutoGen이 설치되지 않아 정적 템플릿만 생성됩니다.")
        loader.generate_all_templates(args.model)
        print("\n템플릿이 templates/ 폴더에 생성되었습니다.")

    elif args.action == "import":
        print(f"\n=== AutoGen Studio에 Import (user: {args.user_id}) ===\n")
        loader.import_to_autogen_studio(args.user_id)

    elif args.action == "compact":
        print(f"\n=== Compact Template Resolve + Import (user: {args.user_id}) ===\n")
        loader.import_compact(user_id=args.user_id)


if __name__ == "__main__":
    main()

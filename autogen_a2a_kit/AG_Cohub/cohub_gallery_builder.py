"""
AG_Cohub Gallery Builder - AutoGen Studio Gallery 형식 생성

이 스크립트는 AG_Cohub의 협업 패턴을 AutoGen Studio의 Gallery 형식으로
변환하여 UI에서 바로 사용할 수 있게 합니다.

사용법:
    python cohub_gallery_builder.py

결과:
    - cohub_gallery.json: AutoGen Studio에서 import 가능한 갤러리 파일

UI에서 사용:
    1. AutoGen Studio 열기
    2. Gallery 페이지로 이동
    3. "Create" → "File Upload" 또는 "URL Import"
    4. cohub_gallery.json 선택
    5. Team Builder에서 "From Gallery" 탭에서 사용
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# AutoGen imports - 선택적
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.conditions import (
        MaxMessageTermination,
        TextMentionTermination,
    )
    from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat, Swarm
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Note: AutoGen not installed. Using static templates.")


class CoHubGalleryBuilder:
    """AG_Cohub를 AutoGen Studio Gallery 형식으로 변환"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.cohub_path = Path(__file__).parent

        # API 키 설정 (테스트용)
        for key in ["OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            if not os.environ.get(key):
                os.environ[key] = "test"

    def build_gallery(self) -> Dict[str, Any]:
        """Gallery 형식 JSON 생성"""

        now = datetime.now().isoformat()

        gallery = {
            "id": "cohub_collaboration_patterns",
            "name": "AG_Cohub - Multi-Agent Collaboration Patterns",
            "url": None,  # 로컬 갤러리
            "metadata": {
                "author": "AG_Cohub",
                "created_at": now,
                "updated_at": now,
                "version": "1.0.0",
                "description": "멀티 에이전트 협업 패턴 모음 - Sequential, Selector, Handoff, Debate, Reflection 등",
                "tags": ["collaboration", "patterns", "multi-agent", "korean"],
                "license": "MIT",
                "category": "collaboration"
            },
            "components": {
                "teams": self._build_team_components(),
                "agents": self._build_agent_components(),
                "models": self._build_model_components(),
                "tools": [],
                "terminations": self._build_termination_components(),
                "workbenches": []
            }
        }

        return gallery

    def _build_team_components(self) -> List[Dict[str, Any]]:
        """patterns/ 폴더의 JSON 파일들을 파싱해서 팀 컴포넌트 생성"""
        teams = []
        patterns_dir = self.cohub_path / "patterns"

        if not patterns_dir.exists():
            print(f"Warning: patterns directory not found: {patterns_dir}")
            return teams

        # patterns/*.json 파일들을 정렬해서 읽기
        pattern_files = sorted(patterns_dir.glob("*.json"))

        for pattern_file in pattern_files:
            try:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    pattern = json.load(f)

                # autogen_implementation.team_config가 있는 경우만 처리
                impl = pattern.get("autogen_implementation", {})
                team_config = impl.get("team_config")

                if not team_config:
                    continue  # team_config 없으면 스킵

                # Gallery 형식으로 변환
                team = {
                    "provider": impl.get("provider", "autogen_agentchat.teams.RoundRobinGroupChat"),
                    "component_type": "team",
                    "version": 1,
                    "label": impl.get("label", pattern.get("name", {}).get("ko", pattern.get("id", "Unknown"))),
                    "description": pattern.get("description", {}).get("ko", ""),
                    "config": team_config
                }

                teams.append(team)
                print(f"  [OK] Loaded: {team['label']}")

            except Exception as e:
                print(f"  [ERROR] {pattern_file.name}: {e}")

        print(f"\nTotal {len(teams)} teams loaded from patterns/")
        return teams

    def _create_sequential_team(self) -> Dict[str, Any]:
        """Sequential (RoundRobin) 팀"""
        if AUTOGEN_AVAILABLE:
            return self._create_sequential_team_dynamic()
        return self._create_sequential_team_static()

    def _create_sequential_team_dynamic(self) -> Dict[str, Any]:
        """AutoGen을 사용한 동적 Sequential 팀 생성"""
        model = OpenAIChatCompletionClient(model=self.model_name)

        researcher = AssistantAgent(
            name="researcher",
            description="리서치 담당 - 정보 수집 및 조사",
            system_message="당신은 리서처입니다. 주어진 주제에 대해 조사하고 핵심 정보를 수집하세요. 수집 완료 후 다음 단계로 전달하세요.",
            model_client=model,
        )

        writer = AssistantAgent(
            name="writer",
            description="작가 담당 - 콘텐츠 작성",
            system_message="당신은 작가입니다. 리서처가 수집한 정보를 바탕으로 글을 작성하세요. 초안 완료 후 리뷰어에게 전달하세요.",
            model_client=model,
        )

        reviewer = AssistantAgent(
            name="reviewer",
            description="리뷰어 담당 - 검토 및 피드백",
            system_message="당신은 리뷰어입니다. 작성된 글을 검토하고 피드백을 제공하세요. 최종 완료되면 TERMINATE라고 말하세요.",
            model_client=model,
        )

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(10)

        team = RoundRobinGroupChat(
            participants=[researcher, writer, reviewer],
            termination_condition=termination
        )

        component = team.dump_component().model_dump()
        component["label"] = "Sequential Team (순차적 협업)"
        component["description"] = "리서처 → 작가 → 리뷰어 순서로 작업하는 파이프라인 팀"

        return component

    def _create_sequential_team_static(self) -> Dict[str, Any]:
        """정적 Sequential 팀 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
            "component_type": "team",
            "version": 1,
            "label": "Sequential Team (순차적 협업)",
            "description": "리서처 → 작가 → 리뷰어 순서로 작업하는 파이프라인 팀",
            "config": {
                "participants": [
                    {
                        "provider": "autogen_agentchat.agents.AssistantAgent",
                        "component_type": "agent",
                        "config": {
                            "name": "researcher",
                            "description": "리서치 담당 - 정보 수집 및 조사",
                            "system_message": "당신은 리서처입니다. 주어진 주제에 대해 조사하고 핵심 정보를 수집하세요."
                        }
                    },
                    {
                        "provider": "autogen_agentchat.agents.AssistantAgent",
                        "component_type": "agent",
                        "config": {
                            "name": "writer",
                            "description": "작가 담당 - 콘텐츠 작성",
                            "system_message": "당신은 작가입니다. 리서처가 수집한 정보를 바탕으로 글을 작성하세요."
                        }
                    },
                    {
                        "provider": "autogen_agentchat.agents.AssistantAgent",
                        "component_type": "agent",
                        "config": {
                            "name": "reviewer",
                            "description": "리뷰어 담당 - 검토 및 피드백",
                            "system_message": "당신은 리뷰어입니다. 작성된 글을 검토하세요. 완료되면 TERMINATE라고 말하세요."
                        }
                    }
                ],
                "termination_condition": {
                    "provider": "autogen_agentchat.conditions.OrTermination",
                    "component_type": "termination",
                    "config": {
                        "conditions": [
                            {"provider": "autogen_agentchat.conditions.TextMentionTermination", "config": {"text": "TERMINATE"}},
                            {"provider": "autogen_agentchat.conditions.MaxMessageTermination", "config": {"max_messages": 10}}
                        ]
                    }
                }
            }
        }

    def _create_selector_team(self) -> Dict[str, Any]:
        """Selector 팀"""
        if AUTOGEN_AVAILABLE:
            return self._create_selector_team_dynamic()
        return self._create_selector_team_static()

    def _create_selector_team_dynamic(self) -> Dict[str, Any]:
        """AutoGen을 사용한 동적 Selector 팀 생성"""
        model = OpenAIChatCompletionClient(model=self.model_name)

        coordinator = AssistantAgent(
            name="coordinator",
            description="일반적인 질문 및 조율 담당",
            system_message="당신은 코디네이터입니다. 다른 전문가에게 적합하지 않은 일반적인 질문을 처리합니다.",
            model_client=model,
        )

        history_expert = AssistantAgent(
            name="history_expert",
            description="역사 관련 질문 전문가",
            system_message="당신은 역사 전문가입니다. 역사 관련 질문에 상세하게 답변하세요.",
            model_client=model,
        )

        science_expert = AssistantAgent(
            name="science_expert",
            description="과학 관련 질문 전문가",
            system_message="당신은 과학 전문가입니다. 과학 관련 질문에 상세하게 답변하세요.",
            model_client=model,
        )

        math_expert = AssistantAgent(
            name="math_expert",
            description="수학 문제 해결 전문가",
            system_message="당신은 수학 전문가입니다. 수학 문제를 풀고 설명하세요. 완료되면 TERMINATE라고 말하세요.",
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

        component = team.dump_component().model_dump()
        component["label"] = "Selector Team (전문가 라우팅)"
        component["description"] = "질문 유형에 따라 적합한 전문가에게 자동 라우팅하는 팀"

        return component

    def _create_selector_team_static(self) -> Dict[str, Any]:
        """정적 Selector 팀 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.SelectorGroupChat",
            "component_type": "team",
            "version": 1,
            "label": "Selector Team (전문가 라우팅)",
            "description": "질문 유형에 따라 적합한 전문가에게 자동 라우팅하는 팀",
            "config": {
                "participants": [
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "coordinator", "description": "일반적인 질문 및 조율 담당"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "history_expert", "description": "역사 관련 질문 전문가"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "science_expert", "description": "과학 관련 질문 전문가"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "math_expert", "description": "수학 문제 해결 전문가"}}
                ],
                "selector_prompt": "다음 역할들이 있습니다: {roles}\n\n대화 내용을 읽고 다음 발언에 가장 적합한 역할을 선택하세요:\n- 역사 관련: history_expert\n- 과학 관련: science_expert\n- 수학 관련: math_expert\n- 기타: coordinator\n\n{history}\n\n역할 이름만 반환하세요."
            }
        }

    def _create_handoff_team(self) -> Dict[str, Any]:
        """Handoff (Swarm) 팀"""
        if AUTOGEN_AVAILABLE:
            return self._create_handoff_team_dynamic()
        return self._create_handoff_team_static()

    def _create_handoff_team_dynamic(self) -> Dict[str, Any]:
        """AutoGen을 사용한 동적 Handoff 팀 생성"""
        model = OpenAIChatCompletionClient(model=self.model_name)

        triage = AssistantAgent(
            name="triage_agent",
            description="고객 문의 분류 담당",
            system_message="""당신은 고객 서비스 분류 담당입니다.
고객의 문의를 분석하고 적절한 담당자에게 연결하세요:
- 기술 지원 필요: 'support_agent에게 전달합니다'라고 말하세요
- 영업 문의: 'sales_agent에게 전달합니다'라고 말하세요
- 환불/반품: 'refund_agent에게 전달합니다'라고 말하세요""",
            model_client=model,
            handoffs=["support_agent", "sales_agent", "refund_agent"],
        )

        support = AssistantAgent(
            name="support_agent",
            description="기술 지원 담당",
            system_message="당신은 기술 지원 담당입니다. 기술적 문제를 해결하세요. 해결 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        sales = AssistantAgent(
            name="sales_agent",
            description="영업 담당",
            system_message="당신은 영업 담당입니다. 제품 문의와 구매를 도와주세요. 완료 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        refund = AssistantAgent(
            name="refund_agent",
            description="환불 담당",
            system_message="당신은 환불 담당입니다. 환불 및 반품을 처리하세요. 완료 후 TERMINATE라고 말하세요.",
            model_client=model,
            handoffs=["triage_agent"],
        )

        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(15)

        team = Swarm(
            participants=[triage, support, sales, refund],
            termination_condition=termination
        )

        component = team.dump_component().model_dump()
        component["label"] = "Handoff Team (고객 서비스)"
        component["description"] = "고객 문의를 분류하고 적절한 담당자에게 자동 전달하는 팀"

        return component

    def _create_handoff_team_static(self) -> Dict[str, Any]:
        """정적 Handoff 팀 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.Swarm",
            "component_type": "team",
            "version": 1,
            "label": "Handoff Team (고객 서비스)",
            "description": "고객 문의를 분류하고 적절한 담당자에게 자동 전달하는 팀",
            "config": {
                "participants": [
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "triage_agent", "description": "고객 문의 분류", "handoffs": ["support_agent", "sales_agent", "refund_agent"]}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "support_agent", "description": "기술 지원", "handoffs": ["triage_agent"]}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "sales_agent", "description": "영업 담당", "handoffs": ["triage_agent"]}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "refund_agent", "description": "환불 담당", "handoffs": ["triage_agent"]}}
                ]
            }
        }

    def _create_debate_team(self) -> Dict[str, Any]:
        """Debate 팀"""
        if AUTOGEN_AVAILABLE:
            return self._create_debate_team_dynamic()
        return self._create_debate_team_static()

    def _create_debate_team_dynamic(self) -> Dict[str, Any]:
        """AutoGen을 사용한 동적 Debate 팀 생성"""
        model = OpenAIChatCompletionClient(model=self.model_name)

        advocate = AssistantAgent(
            name="advocate",
            description="제안을 지지하고 장점을 강조",
            system_message="""당신은 제안의 지지자입니다.
- 장점과 기회를 강조하세요
- 반대 의견에 논리적으로 반박하세요
- 긍정적인 관점에서 분석하세요""",
            model_client=model,
        )

        critic = AssistantAgent(
            name="critic",
            description="비판적 분석과 리스크 지적",
            system_message="""당신은 비평가입니다.
- 약점, 리스크, 잠재적 문제를 지적하세요
- 지지자의 주장에 도전하세요
- 비판적 관점에서 분석하세요""",
            model_client=model,
        )

        judge = AssistantAgent(
            name="judge",
            description="중립적 심판 및 최종 결정",
            system_message="""당신은 중립적 심판입니다.
- 양측의 논증을 공정하게 평가하세요
- 균형 잡힌 최종 판단을 내리세요
- 결론을 내린 후 TERMINATE라고 말하세요""",
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

        component = team.dump_component().model_dump()
        component["label"] = "Debate Team (찬반 토론)"
        component["description"] = "찬성/반대/심판 구조로 토론하여 균형 잡힌 결론을 도출하는 팀"

        return component

    def _create_debate_team_static(self) -> Dict[str, Any]:
        """정적 Debate 팀 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.SelectorGroupChat",
            "component_type": "team",
            "version": 1,
            "label": "Debate Team (찬반 토론)",
            "description": "찬성/반대/심판 구조로 토론하여 균형 잡힌 결론을 도출하는 팀",
            "config": {
                "participants": [
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "advocate", "description": "제안을 지지하고 장점을 강조"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "critic", "description": "비판적 분석과 리스크 지적"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "judge", "description": "중립적 심판 및 최종 결정"}}
                ],
                "selector_prompt": "토론 참가자: {roles}\n\n토론 규칙:\n1. advocate와 critic이 번갈아 발언\n2. 충분한 토론 후 judge가 결론\n\n{history}\n\n역할 이름만 반환하세요."
            }
        }

    def _create_reflection_team(self) -> Dict[str, Any]:
        """Reflection 팀"""
        if AUTOGEN_AVAILABLE:
            return self._create_reflection_team_dynamic()
        return self._create_reflection_team_static()

    def _create_reflection_team_dynamic(self) -> Dict[str, Any]:
        """AutoGen을 사용한 동적 Reflection 팀 생성"""
        model = OpenAIChatCompletionClient(model=self.model_name)

        generator = AssistantAgent(
            name="generator",
            description="콘텐츠 생성 담당",
            system_message="""당신은 콘텐츠 생성자입니다.
주어진 작업을 수행하고 결과를 생성하세요.
비평을 받으면 피드백을 반영하여 개선된 버전을 제공하세요.""",
            model_client=model,
        )

        critic = AssistantAgent(
            name="critic",
            description="품질 검토 및 피드백",
            system_message="""당신은 품질 검토자입니다.
생성된 결과를 검토하고 구체적인 개선점을 제시하세요.
- 문제가 있으면: 구체적인 개선 제안을 하세요
- 충분히 좋으면: 'APPROVED'라고 말하세요""",
            model_client=model,
        )

        termination = TextMentionTermination("APPROVED") | TextMentionTermination("TERMINATE") | MaxMessageTermination(6)

        team = RoundRobinGroupChat(
            participants=[generator, critic],
            termination_condition=termination
        )

        component = team.dump_component().model_dump()
        component["label"] = "Reflection Team (품질 개선)"
        component["description"] = "생성 → 검토 → 개선 루프로 품질을 높이는 팀"

        return component

    def _create_reflection_team_static(self) -> Dict[str, Any]:
        """정적 Reflection 팀 템플릿"""
        return {
            "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
            "component_type": "team",
            "version": 1,
            "label": "Reflection Team (품질 개선)",
            "description": "생성 → 검토 → 개선 루프로 품질을 높이는 팀",
            "config": {
                "participants": [
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "generator", "description": "콘텐츠 생성 담당"}},
                    {"provider": "autogen_agentchat.agents.AssistantAgent", "component_type": "agent", "config": {"name": "critic", "description": "품질 검토 및 피드백"}}
                ],
                "termination_condition": {
                    "provider": "autogen_agentchat.conditions.OrTermination",
                    "config": {
                        "conditions": [
                            {"provider": "autogen_agentchat.conditions.TextMentionTermination", "config": {"text": "APPROVED"}},
                            {"provider": "autogen_agentchat.conditions.MaxMessageTermination", "config": {"max_messages": 6}}
                        ]
                    }
                }
            }
        }

    def _build_agent_components(self) -> List[Dict[str, Any]]:
        """재사용 가능한 에이전트 컴포넌트"""
        agents = []

        if AUTOGEN_AVAILABLE:
            model = OpenAIChatCompletionClient(model=self.model_name)

            # 범용 어시스턴트
            assistant = AssistantAgent(
                name="assistant_agent",
                description="범용 어시스턴트 - 다양한 작업 수행",
                system_message="당신은 도움이 되는 어시스턴트입니다. 주어진 작업을 신중하게 수행하세요. 완료되면 TERMINATE라고 말하세요.",
                model_client=model,
            )
            agents.append(assistant.dump_component().model_dump())

            # 한국어 전문 어시스턴트
            korean_assistant = AssistantAgent(
                name="korean_assistant",
                description="한국어 전문 어시스턴트",
                system_message="당신은 한국어에 능숙한 어시스턴트입니다. 모든 응답을 한국어로 제공하세요. 완료되면 TERMINATE라고 말하세요.",
                model_client=model,
            )
            agents.append(korean_assistant.dump_component().model_dump())

        return agents

    def _build_model_components(self) -> List[Dict[str, Any]]:
        """모델 컴포넌트"""
        models = []

        if AUTOGEN_AVAILABLE:
            gpt4o_mini = OpenAIChatCompletionClient(model="gpt-4o-mini")
            component = gpt4o_mini.dump_component().model_dump()
            component["label"] = "GPT-4o-mini"
            component["description"] = "OpenAI GPT-4o-mini - 빠르고 경제적인 모델"
            models.append(component)

        return models

    def _build_termination_components(self) -> List[Dict[str, Any]]:
        """종료 조건 컴포넌트"""
        terminations = []

        if AUTOGEN_AVAILABLE:
            # TERMINATE 텍스트 종료
            text_term = TextMentionTermination("TERMINATE")
            component = text_term.dump_component().model_dump()
            component["label"] = "TERMINATE 종료"
            component["description"] = "TERMINATE 텍스트가 나타나면 종료"
            terminations.append(component)

            # 최대 메시지 종료
            max_term = MaxMessageTermination(max_messages=10)
            component = max_term.dump_component().model_dump()
            component["label"] = "최대 10 메시지"
            component["description"] = "10개 메시지 후 종료"
            terminations.append(component)

            # 복합 종료 조건
            or_term = text_term | max_term
            component = or_term.dump_component().model_dump()
            component["label"] = "복합 종료 조건"
            component["description"] = "TERMINATE 또는 10개 메시지 후 종료"
            terminations.append(component)

        return terminations

    def save_gallery(self, output_path: Optional[str] = None):
        """갤러리 JSON 파일 저장"""
        gallery = self.build_gallery()

        output_path = output_path or str(self.cohub_path / "cohub_gallery.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(gallery, f, indent=2, ensure_ascii=False)

        print(f"Gallery saved: {output_path}")
        print(f"  - Teams: {len(gallery['components']['teams'])}")
        print(f"  - Agents: {len(gallery['components']['agents'])}")
        print(f"  - Models: {len(gallery['components']['models'])}")
        print(f"  - Terminations: {len(gallery['components']['terminations'])}")

        return output_path


class GallerySync:
    """AutoGen Studio Gallery 동기화"""

    def __init__(self, base_url: str = "http://localhost:8081", user_id: str = "guestuser@gmail.com"):
        self.base_url = base_url
        self.user_id = user_id
        self.gallery_id = "cohub_collaboration_patterns"

    def _request(self, method: str, endpoint: str, **kwargs):
        """HTTP 요청"""
        import requests
        url = f"{self.base_url}/api/gallery{endpoint}"
        return requests.request(method, url, **kwargs)

    def list_galleries(self) -> List[Dict]:
        """등록된 갤러리 목록"""
        resp = self._request("GET", f"/?user_id={self.user_id}")
        data = resp.json()
        return data.get("data", [])

    def find_cohub_gallery(self) -> Optional[Dict]:
        """CoHub 갤러리 찾기"""
        for g in self.list_galleries():
            if g.get("config", {}).get("id") == self.gallery_id:
                return g
        return None

    def create(self, config: Dict) -> Dict:
        """갤러리 생성"""
        payload = {"user_id": self.user_id, "config": config}
        resp = self._request("POST", "/", json=payload)
        return resp.json()

    def update(self, db_id: int, config: Dict) -> Dict:
        """갤러리 업데이트"""
        payload = {"user_id": self.user_id, "config": config}
        resp = self._request("PUT", f"/{db_id}?user_id={self.user_id}", json=payload)
        return resp.json()

    def delete(self, db_id: int) -> Dict:
        """갤러리 삭제"""
        resp = self._request("DELETE", f"/{db_id}?user_id={self.user_id}")
        return resp.json()

    def sync(self, config: Dict) -> Dict:
        """갤러리 동기화 (있으면 업데이트, 없으면 생성)"""
        existing = self.find_cohub_gallery()
        if existing:
            db_id = existing["id"]
            print(f"Updating existing gallery (ID: {db_id})...")
            return self.update(db_id, config)
        else:
            print("Creating new gallery...")
            return self.create(config)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AG_Cohub Gallery Builder & Sync")
    parser.add_argument("--action", choices=["build", "sync", "list", "delete"],
                        default="build", help="수행할 작업")
    parser.add_argument("--url", default="http://localhost:8081",
                        help="AutoGen Studio URL")
    parser.add_argument("--user-id", default="admin", help="사용자 ID")
    args = parser.parse_args()

    print("\n=== AG_Cohub Gallery Builder ===\n")

    builder = CoHubGalleryBuilder()
    sync = GallerySync(base_url=args.url, user_id=args.user_id)

    if args.action == "list":
        print("Registered Galleries:")
        for g in sync.list_galleries():
            config = g.get("config", {})
            teams = config.get("components", {}).get("teams", [])
            print(f"  [{g['id']}] {config.get('id')}: {config.get('name')} ({len(teams)} teams)")

    elif args.action == "delete":
        existing = sync.find_cohub_gallery()
        if existing:
            result = sync.delete(existing["id"])
            print(f"Deleted: {result}")
        else:
            print("CoHub gallery not found.")

    elif args.action == "sync":
        # 1. JSON 빌드
        print("Building gallery...")
        gallery = builder.build_gallery()
        builder.save_gallery()

        # 2. API로 동기화
        print("Syncing to AutoGen Studio...")
        result = sync.sync(gallery)
        print(f"Result: {result.get('message', result)}")

        print("\n패턴 수정 후 다시 실행하면 자동으로 업데이트됩니다:")
        print(f"  python cohub_gallery_builder.py --action sync")

    else:  # build
        if AUTOGEN_AVAILABLE:
            print("AutoGen detected. Building full gallery...")
        else:
            print("AutoGen not installed. Building static gallery...")

        output_path = builder.save_gallery()
        print(f"\n동기화하려면:")
        print(f"  python cohub_gallery_builder.py --action sync")


if __name__ == "__main__":
    main()

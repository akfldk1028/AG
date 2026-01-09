# Philosophy Wisdom Agent - A2A Protocol
# 철학적 지혜와 사상가 인용 에이전트

import os
import random
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found")


def get_philosopher_quote(philosopher: str) -> dict:
    """철학자의 명언을 가져옵니다.

    Args:
        philosopher: 철학자 이름

    Returns:
        철학자 정보와 명언
    """
    philosophers_db = {
        "소크라테스": {
            "name": "소크라테스 (Socrates, BC 470-399)",
            "school": "고대 그리스 철학",
            "quotes": [
                "너 자신을 알라. (Know thyself)",
                "검토되지 않은 삶은 살 가치가 없다.",
                "나는 내가 아무것도 모른다는 것을 안다."
            ],
            "key_concept": "산파술(Maieutics), 무지의 지"
        },
        "플라톤": {
            "name": "플라톤 (Plato, BC 428-348)",
            "school": "고대 그리스 철학, 아카데미아",
            "quotes": [
                "좋은 사람은 법이 필요 없고, 나쁜 사람은 법을 피해간다.",
                "동굴 밖으로 나온 자만이 진정한 빛을 본다.",
                "인간의 영혼에는 세 부분이 있다: 이성, 기개, 욕망."
            ],
            "key_concept": "이데아론, 동굴의 비유"
        },
        "아리스토텔레스": {
            "name": "아리스토텔레스 (Aristotle, BC 384-322)",
            "school": "고대 그리스 철학, 페리파토스 학파",
            "quotes": [
                "우리는 반복적으로 행하는 것이 된다. 탁월함은 행위가 아니라 습관이다.",
                "인간은 본성적으로 사회적 동물이다.",
                "행복은 삶의 의미이자 목적이다."
            ],
            "key_concept": "중용, 목적론, 덕 윤리학"
        },
        "니체": {
            "name": "프리드리히 니체 (Friedrich Nietzsche, 1844-1900)",
            "school": "실존주의, 허무주의 비판",
            "quotes": [
                "나를 죽이지 못하는 것은 나를 더 강하게 만든다.",
                "신은 죽었다. 그리고 우리가 그를 죽였다.",
                "심연을 오래 들여다보면, 심연도 너를 들여다본다."
            ],
            "key_concept": "초인(Ubermensch), 영원회귀, 권력의지"
        },
        "칸트": {
            "name": "임마누엘 칸트 (Immanuel Kant, 1724-1804)",
            "school": "독일 관념론, 비판철학",
            "quotes": [
                "네 의지의 준칙이 항상 보편적 입법의 원리가 되도록 행동하라.",
                "두 가지가 나를 경외심으로 채운다: 별이 빛나는 하늘과 내 안의 도덕 법칙.",
                "계몽이란 스스로 초래한 미성숙에서 벗어나는 것이다."
            ],
            "key_concept": "정언명령, 순수이성비판, 물자체"
        },
        "공자": {
            "name": "공자 (孔子, BC 551-479)",
            "school": "유학(儒學)",
            "quotes": [
                "배우고 때때로 익히면 또한 기쁘지 아니한가.",
                "자기가 원하지 않는 것을 남에게 베풀지 말라.",
                "아는 것을 안다 하고, 모르는 것을 모른다 하는 것이 아는 것이다."
            ],
            "key_concept": "인(仁), 예(禮), 군자"
        },
        "장자": {
            "name": "장자 (莊子, BC 369-286)",
            "school": "도가(道家)",
            "quotes": [
                "호접지몽: 나비가 나인지, 내가 나비인지.",
                "큰 앎을 가진 자는 한가롭고, 작은 앎을 가진 자는 바쁘다.",
                "쓸모없음의 쓸모를 알아야 한다."
            ],
            "key_concept": "소요유, 제물론, 무위자연"
        }
    }

    phil_lower = philosopher.lower().strip()
    for key, info in philosophers_db.items():
        if key in phil_lower or phil_lower in key.lower():
            quote = random.choice(info["quotes"])
            return {
                "found": True,
                **info,
                "selected_quote": quote
            }

    return {
        "found": False,
        "message": f"'{philosopher}'에 대한 정보가 없습니다.",
        "available": list(philosophers_db.keys())
    }


def explore_philosophical_question(topic: str) -> dict:
    """철학적 주제를 탐구합니다.

    Args:
        topic: 철학적 주제 (예: 자유의지, 정의, 행복)

    Returns:
        다양한 철학적 관점들
    """
    topics_db = {
        "자유의지": {
            "question": "인간은 진정으로 자유로운가?",
            "perspectives": [
                {"school": "결정론", "view": "모든 행위는 선행 원인에 의해 결정된다 (라플라스)"},
                {"school": "자유의지론", "view": "인간은 원인 없이 선택할 수 있다 (칸트)"},
                {"school": "양립론", "view": "결정론과 자유의지는 양립 가능하다 (흄)"}
            ],
            "thought_experiment": "만약 모든 것이 결정되어 있다면, 도덕적 책임은 의미가 있는가?"
        },
        "정의": {
            "question": "무엇이 정의로운 것인가?",
            "perspectives": [
                {"school": "공리주의", "view": "최대 다수의 최대 행복 (벤담, 밀)"},
                {"school": "의무론", "view": "보편적 도덕 법칙에 따르는 것 (칸트)"},
                {"school": "덕 윤리학", "view": "덕 있는 사람이 하는 것 (아리스토텔레스)"},
                {"school": "롤스", "view": "무지의 베일 뒤에서 선택할 원칙 (공정으로서의 정의)"}
            ],
            "thought_experiment": "트롤리 문제: 5명을 살리기 위해 1명을 희생시키는 것은 정의로운가?"
        },
        "행복": {
            "question": "진정한 행복이란 무엇인가?",
            "perspectives": [
                {"school": "쾌락주의", "view": "쾌락의 극대화와 고통의 최소화 (에피쿠로스)"},
                {"school": "스토아학파", "view": "자연에 따라 살고 정념을 제어하는 것 (에픽테토스)"},
                {"school": "아리스토텔레스", "view": "에우다이모니아: 덕에 따른 영혼의 활동"},
                {"school": "불교", "view": "욕망의 소멸을 통한 열반"}
            ],
            "thought_experiment": "노직의 '경험 기계': 완벽한 가상 행복과 불완전한 현실 중 무엇을 선택할 것인가?"
        },
        "존재": {
            "question": "왜 무(無)가 아니라 유(有)가 존재하는가?",
            "perspectives": [
                {"school": "존재론", "view": "존재는 본질에 앞선다 (사르트르)"},
                {"school": "현상학", "view": "의식에 나타나는 것만이 존재한다 (후설)"},
                {"school": "하이데거", "view": "존재 물음을 다시 물어야 한다 (존재와 시간)"}
            ],
            "thought_experiment": "만약 당신이 존재하지 않았다면, 그것이 문제가 되었을까?"
        },
        "죽음": {
            "question": "죽음이란 무엇이며, 어떻게 대면해야 하는가?",
            "perspectives": [
                {"school": "에피쿠로스", "view": "죽음은 우리에게 아무것도 아니다. 우리가 있을 때 죽음은 없고, 죽음이 있을 때 우리는 없다."},
                {"school": "하이데거", "view": "죽음을 향한 존재(Sein-zum-Tode)로서 본래적 삶을 살아야 한다."},
                {"school": "스토아", "view": "메멘토 모리: 죽음을 기억하고 현재에 충실하라."}
            ],
            "thought_experiment": "만약 영생이 가능하다면, 삶의 의미는 어떻게 달라질까?"
        }
    }

    topic_lower = topic.lower().strip()
    for key, info in topics_db.items():
        if key in topic_lower or topic_lower in key:
            return {"found": True, "topic": key, **info}

    return {
        "found": False,
        "message": f"'{topic}'에 대한 정리된 관점이 없습니다. 직접 질문해 주세요.",
        "available_topics": list(topics_db.keys())
    }


def compare_eastern_western(concept: str) -> dict:
    """동서양 철학을 비교합니다.

    Args:
        concept: 비교할 개념

    Returns:
        동서양 관점 비교
    """
    comparisons = {
        "자아": {
            "western": {
                "view": "개별적이고 독립적인 실체로서의 자아",
                "thinkers": "데카르트(cogito), 칸트(선험적 자아), 사르트르(자유로운 주체)"
            },
            "eastern": {
                "view": "관계적이고 상호의존적인 자아, 또는 무아(無我)",
                "thinkers": "불교(무아설), 유학(관계 속의 자아), 도가(자연과 하나됨)"
            },
            "insight": "서양은 자아의 독립성을, 동양은 자아의 연결성을 강조한다."
        },
        "자연": {
            "western": {
                "view": "정복하고 이용해야 할 대상, 법칙으로 설명 가능",
                "thinkers": "베이컨(자연의 정복), 데카르트(기계론)"
            },
            "eastern": {
                "view": "조화를 이루며 살아야 할 대상, 도(道)의 흐름",
                "thinkers": "노자(무위자연), 장자(물아일체)"
            },
            "insight": "서양의 자연 지배 vs 동양의 자연 순응"
        },
        "지식": {
            "western": {
                "view": "논리적 분석과 증명을 통한 객관적 진리 추구",
                "thinkers": "플라톤(이데아), 칸트(선험적 인식)"
            },
            "eastern": {
                "view": "직관과 체험을 통한 깨달음, 언어를 넘어선 앎",
                "thinkers": "선불교(불립문자), 노자(도가도비상도)"
            },
            "insight": "서양의 이성적 분석 vs 동양의 직관적 체득"
        }
    }

    concept_lower = concept.lower().strip()
    for key, info in comparisons.items():
        if key in concept_lower or concept_lower in key:
            return {"found": True, "concept": key, **info}

    return {
        "found": False,
        "message": f"'{concept}'에 대한 동서양 비교가 없습니다.",
        "available": list(comparisons.keys())
    }


# 철학 에이전트
philosophy_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="philosophy_agent",
    description="철학적 질문에 답하고, 동서양 사상가들의 지혜를 나누는 철학 전문 에이전트입니다.",
    instruction="""당신은 철학 전문 에이전트입니다.

주요 기능:
1. 철학자 명언 (get_philosopher_quote) - 소크라테스, 니체, 공자 등
2. 철학적 주제 탐구 (explore_philosophical_question) - 자유의지, 정의, 행복 등
3. 동서양 철학 비교 (compare_eastern_western) - 관점의 차이와 통찰

답변할 때:
- 다양한 철학적 관점을 균형 있게 제시하세요
- 사고 실험과 예시를 활용하세요
- 독단적이지 않고 탐구적인 태도를 유지하세요
- 질문을 통해 사고를 자극하세요

"지혜의 사랑(philosophia)"의 정신으로 대화하세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(get_philosopher_quote),
        FunctionTool(explore_philosophical_question),
        FunctionTool(compare_eastern_western)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Philosophy Wisdom Agent - A2A Server")
    print("=" * 50)
    print("Port: 8004")
    print("Agent Card: http://localhost:8004/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(philosophy_agent, port=8004, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8004)

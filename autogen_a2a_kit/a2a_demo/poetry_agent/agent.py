# Poetry Analysis Agent - A2A Protocol
# 시 분석 및 문학 해석 에이전트

import os
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


def analyze_poem_structure(text: str) -> dict:
    """시의 구조를 분석합니다.

    Args:
        text: 분석할 시 텍스트

    Returns:
        구조 분석 결과
    """
    lines = text.strip().split('\n')
    stanzas = text.strip().split('\n\n')

    # 간단한 운율 패턴 감지
    line_endings = [line.strip()[-1] if line.strip() else '' for line in lines]

    return {
        "total_lines": len(lines),
        "stanza_count": len(stanzas),
        "lines_per_stanza": [len(s.split('\n')) for s in stanzas],
        "line_endings": line_endings[:10],  # 처음 10개만
        "avg_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0
    }


def find_literary_devices(text: str) -> dict:
    """문학적 기법을 찾습니다.

    Args:
        text: 분석할 텍스트

    Returns:
        발견된 문학적 기법들
    """
    devices = {
        "반복(Repetition)": [],
        "의인화_힌트(Personification)": [],
        "비유_힌트(Metaphor/Simile)": []
    }

    lines = text.split('\n')
    words = text.lower().split()

    # 반복 찾기
    word_count = {}
    for word in words:
        clean_word = ''.join(c for c in word if c.isalnum())
        if len(clean_word) > 2:
            word_count[clean_word] = word_count.get(clean_word, 0) + 1

    repeated = [w for w, c in word_count.items() if c >= 3]
    devices["반복(Repetition)"] = repeated[:5]

    # 비유 힌트 (like, as, 처럼, 같이)
    simile_markers = ['like', 'as if', 'as though', '처럼', '같이', '듯이', '마치']
    for marker in simile_markers:
        if marker in text.lower():
            devices["비유_힌트(Metaphor/Simile)"].append(f"'{marker}' 발견")

    # 의인화 힌트
    personification_verbs = ['whispers', 'dances', 'sleeps', 'cries', '속삭이', '춤추', '웃']
    for verb in personification_verbs:
        if verb in text.lower():
            devices["의인화_힌트(Personification)"].append(f"'{verb}' 발견")

    return devices


def get_famous_poem(poet: str) -> dict:
    """유명 시인의 대표작 정보를 제공합니다.

    Args:
        poet: 시인 이름

    Returns:
        시인 정보와 대표작
    """
    poets_db = {
        "윤동주": {
            "name": "윤동주 (1917-1945)",
            "era": "일제강점기",
            "famous_work": "서시",
            "excerpt": "죽는 날까지 하늘을 우러러 한 점 부끄럼이 없기를...",
            "style": "저항시, 서정시"
        },
        "김소월": {
            "name": "김소월 (1902-1934)",
            "era": "일제강점기",
            "famous_work": "진달래꽃",
            "excerpt": "나 보기가 역겨워 가실 때에는 말없이 고이 보내드리우리다...",
            "style": "민요조 서정시"
        },
        "shakespeare": {
            "name": "William Shakespeare (1564-1616)",
            "era": "English Renaissance",
            "famous_work": "Sonnet 18",
            "excerpt": "Shall I compare thee to a summer's day?...",
            "style": "Sonnets, Plays"
        },
        "emily dickinson": {
            "name": "Emily Dickinson (1830-1886)",
            "era": "American Romanticism",
            "famous_work": "Hope is the thing with feathers",
            "excerpt": "Hope is the thing with feathers that perches in the soul...",
            "style": "Short lyrics, unconventional punctuation"
        },
        "백석": {
            "name": "백석 (1912-1996)",
            "era": "일제강점기/해방 후",
            "famous_work": "나와 나타샤와 흰 당나귀",
            "excerpt": "가난한 내가 아름다운 나타샤를 사랑해서...",
            "style": "향토적 서정시"
        }
    }

    poet_lower = poet.lower().strip()
    for key, info in poets_db.items():
        if key in poet_lower or poet_lower in key:
            return {"found": True, **info}

    return {
        "found": False,
        "message": f"'{poet}'에 대한 정보가 데이터베이스에 없습니다. 일반적인 질문으로 물어보세요.",
        "available_poets": list(poets_db.keys())
    }


# 시 분석 에이전트
poetry_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="poetry_agent",
    description="시와 문학 작품을 분석하고 해석하는 문학 전문 에이전트입니다. 시의 구조, 문학적 기법, 시인 정보를 제공합니다.",
    instruction="""당신은 문학과 시 전문 에이전트입니다.

주요 기능:
1. 시의 구조 분석 (analyze_poem_structure) - 연, 행, 운율 패턴 분석
2. 문학적 기법 찾기 (find_literary_devices) - 반복, 비유, 의인화 등
3. 유명 시인 정보 (get_famous_poem) - 시인의 대표작과 스타일

시를 분석할 때:
- 형식적 특징 (운율, 연 구조)을 먼저 파악하세요
- 주제와 정서를 해석해주세요
- 사용된 문학적 기법을 설명해주세요
- 역사적/문화적 맥락을 고려해주세요

항상 교육적이고 통찰력 있는 방식으로 설명해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(analyze_poem_structure),
        FunctionTool(find_literary_devices),
        FunctionTool(get_famous_poem)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Poetry Analysis Agent - A2A Server")
    print("=" * 50)
    print("Port: 8003")
    print("Agent Card: http://localhost:8003/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(poetry_agent, port=8003, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8003)

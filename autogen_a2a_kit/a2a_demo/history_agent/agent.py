# History Storyteller Agent - A2A Protocol
# 역사 이야기와 사건 해설 에이전트

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


def get_historical_event(event_name: str) -> dict:
    """역사적 사건의 정보를 가져옵니다.

    Args:
        event_name: 사건 이름 또는 키워드

    Returns:
        사건의 상세 정보
    """
    events_db = {
        "프랑스혁명": {
            "name": "프랑스 대혁명 (French Revolution)",
            "period": "1789-1799",
            "location": "프랑스",
            "key_dates": [
                "1789.7.14 - 바스티유 감옥 습격",
                "1789.8.26 - 인권선언 채택",
                "1793.1.21 - 루이 16세 처형",
                "1799.11.9 - 나폴레옹 쿠데타"
            ],
            "significance": "자유, 평등, 박애의 이념을 세계에 전파. 봉건제 종식과 근대 민주주의의 시작.",
            "key_figures": ["루이 16세", "마리 앙투아네트", "로베스피에르", "나폴레옹"]
        },
        "산업혁명": {
            "name": "산업혁명 (Industrial Revolution)",
            "period": "1760-1840 (1차)",
            "location": "영국에서 시작, 전 세계로 확산",
            "key_dates": [
                "1769 - 제임스 와트의 증기기관 개량",
                "1785 - 카트라이트의 역직기",
                "1825 - 최초의 공공 철도 개통"
            ],
            "significance": "농업 사회에서 산업 사회로의 대전환. 도시화, 노동계급 출현, 자본주의 발전.",
            "key_figures": ["제임스 와트", "애덤 스미스", "리처드 아크라이트"]
        },
        "세종대왕": {
            "name": "세종대왕 시대",
            "period": "1418-1450 (재위)",
            "location": "조선",
            "key_dates": [
                "1443 - 훈민정음 창제",
                "1446 - 훈민정음 반포",
                "1432 - 집현전 설치",
                "1442 - 측우기 발명"
            ],
            "significance": "한글 창제로 민족 문화의 기틀 마련. 과학, 음악, 국방 등 전 분야에서 혁신.",
            "key_figures": ["세종대왕", "장영실", "박연", "신숙주", "성삼문"]
        },
        "르네상스": {
            "name": "르네상스 (Renaissance)",
            "period": "14-17세기",
            "location": "이탈리아에서 시작, 유럽 전역",
            "key_dates": [
                "1450년경 - 구텐베르크 인쇄술",
                "1503-1506 - 모나리자 완성",
                "1508-1512 - 시스티나 성당 천장화",
                "1543 - 코페르니쿠스 지동설"
            ],
            "significance": "중세에서 근대로의 문화적 전환. 인간 중심 사상, 과학혁명의 기초.",
            "key_figures": ["레오나르도 다빈치", "미켈란젤로", "라파엘로", "에라스무스"]
        },
        "임진왜란": {
            "name": "임진왜란",
            "period": "1592-1598",
            "location": "조선",
            "key_dates": [
                "1592.4.13 - 일본군 부산 상륙",
                "1592.5.7 - 한산도 대첩",
                "1593.1 - 평양성 탈환",
                "1598.11 - 노량해전, 이순신 전사"
            ],
            "significance": "7년간의 전쟁으로 조선 인구 절반 감소. 동아시아 국제질서 재편.",
            "key_figures": ["이순신", "권율", "곽재우", "도요토미 히데요시"]
        },
        "세계대전": {
            "name": "제2차 세계대전",
            "period": "1939-1945",
            "location": "전 세계",
            "key_dates": [
                "1939.9.1 - 독일의 폴란드 침공",
                "1941.12.7 - 진주만 공습",
                "1944.6.6 - 노르망디 상륙작전",
                "1945.8.15 - 일본 항복"
            ],
            "significance": "인류 역사상 가장 큰 전쟁. 약 7천만 명 사망. UN 창설, 냉전 시작.",
            "key_figures": ["히틀러", "처칠", "루즈벨트", "스탈린"]
        }
    }

    event_lower = event_name.lower().strip()
    for key, info in events_db.items():
        if key in event_lower or event_lower in key.lower():
            return {"found": True, **info}

    return {
        "found": False,
        "message": f"'{event_name}'에 대한 정보가 없습니다.",
        "available_events": list(events_db.keys())
    }


def compare_eras(era1: str, era2: str) -> dict:
    """두 시대를 비교합니다.

    Args:
        era1: 첫 번째 시대
        era2: 두 번째 시대

    Returns:
        시대 비교 분석
    """
    eras_data = {
        "고대": {
            "period": "~500 AD",
            "characteristics": ["농경 사회", "도시국가/제국", "신화적 세계관", "노예제"],
            "achievements": ["민주주의(아테네)", "법전(로마법)", "철학", "건축"]
        },
        "중세": {
            "period": "500-1500 AD",
            "characteristics": ["봉건제", "종교 중심", "장원 경제", "기사 계급"],
            "achievements": ["고딕 건축", "대학 설립", "길드 제도", "십자군 원정"]
        },
        "근대": {
            "period": "1500-1900 AD",
            "characteristics": ["국민국가", "자본주의", "과학혁명", "계몽주의"],
            "achievements": ["산업혁명", "시민혁명", "인쇄술", "식민지 확장"]
        },
        "현대": {
            "period": "1900-현재",
            "characteristics": ["세계화", "정보화", "민주주의 확산", "기술 혁신"],
            "achievements": ["컴퓨터/인터넷", "우주 탐사", "인권 신장", "의학 발전"]
        }
    }

    era1_data = None
    era2_data = None

    for key, data in eras_data.items():
        if key in era1.lower() or era1.lower() in key.lower():
            era1_data = {"name": key, **data}
        if key in era2.lower() or era2.lower() in key.lower():
            era2_data = {"name": key, **data}

    if era1_data and era2_data:
        return {
            "found": True,
            "era1": era1_data,
            "era2": era2_data,
            "comparison": f"{era1_data['name']}과 {era2_data['name']}는 사회 구조, 경제 체제, 세계관에서 근본적인 차이를 보입니다."
        }

    return {
        "found": False,
        "available_eras": list(eras_data.keys())
    }


def get_historical_figure(person: str) -> dict:
    """역사적 인물의 정보를 가져옵니다.

    Args:
        person: 인물 이름

    Returns:
        인물의 상세 정보
    """
    figures_db = {
        "이순신": {
            "name": "이순신 (李舜臣)",
            "life": "1545-1598",
            "nationality": "조선",
            "role": "장군, 해군 제독",
            "achievements": [
                "거북선 건조 지휘",
                "23전 23승의 해전 기록",
                "한산도 대첩, 명량해전 승리",
                "난중일기 저술"
            ],
            "famous_quote": "죽고자 하면 살고, 살고자 하면 죽는다",
            "legacy": "세계 해전사에서 가장 위대한 제독 중 한 명으로 평가"
        },
        "링컨": {
            "name": "에이브러햄 링컨 (Abraham Lincoln)",
            "life": "1809-1865",
            "nationality": "미국",
            "role": "16대 대통령",
            "achievements": [
                "노예해방선언 (1863)",
                "남북전쟁 승리로 연방 유지",
                "게티즈버그 연설"
            ],
            "famous_quote": "국민의, 국민에 의한, 국민을 위한 정부",
            "legacy": "미국 역사상 가장 위대한 대통령으로 평가"
        },
        "간디": {
            "name": "마하트마 간디 (Mahatma Gandhi)",
            "life": "1869-1948",
            "nationality": "인도",
            "role": "독립운동가, 사상가",
            "achievements": [
                "비폭력 저항운동(사티아그라하)",
                "소금 행진 (1930)",
                "인도 독립 (1947)"
            ],
            "famous_quote": "당신이 세상에서 보고 싶은 변화가 되어라",
            "legacy": "비폭력 평화운동의 상징, 전 세계 인권운동에 영향"
        },
        "클레오파트라": {
            "name": "클레오파트라 7세",
            "life": "BC 69-30",
            "nationality": "프톨레마이오스 왕조 이집트",
            "role": "파라오, 여왕",
            "achievements": [
                "다국어 구사 (9개 언어)",
                "카이사르, 안토니우스와의 동맹",
                "이집트 경제 부흥"
            ],
            "famous_quote": "나는 여왕으로 살았고, 여왕으로 죽을 것이다",
            "legacy": "고대 세계 가장 강력한 여성 지도자 중 한 명"
        },
        "정약용": {
            "name": "정약용 (丁若鏞)",
            "life": "1762-1836",
            "nationality": "조선",
            "role": "실학자, 사상가",
            "achievements": [
                "목민심서 저술",
                "경세유표, 흠흠신서 저술",
                "거중기 설계",
                "500권 이상의 저서"
            ],
            "famous_quote": "목민관은 백성을 위해 존재하는 것이다",
            "legacy": "조선 실학의 집대성자, 근대적 사회개혁 사상의 선구자"
        }
    }

    person_lower = person.lower().strip()
    for key, info in figures_db.items():
        if key in person_lower or person_lower in key.lower():
            return {"found": True, **info}

    return {
        "found": False,
        "message": f"'{person}'에 대한 정보가 없습니다.",
        "available_figures": list(figures_db.keys())
    }


def this_day_in_history(month: int, day: int) -> dict:
    """오늘의 역사를 알려줍니다.

    Args:
        month: 월 (1-12)
        day: 일 (1-31)

    Returns:
        해당 날짜의 역사적 사건들
    """
    history_calendar = {
        (1, 1): ["1863 - 링컨의 노예해방선언 발효", "1959 - 쿠바 혁명 성공"],
        (3, 1): ["1919 - 3.1 독립운동", "1954 - 비키니 환초 수소폭탄 실험"],
        (4, 19): ["1960 - 4.19 혁명", "1775 - 미국 독립전쟁 시작"],
        (5, 18): ["1980 - 5.18 민주화운동", "1804 - 나폴레옹 황제 즉위"],
        (6, 25): ["1950 - 한국전쟁 발발", "1876 - 리틀빅혼 전투"],
        (7, 4): ["1776 - 미국 독립선언", "1865 - 이상한 나라의 앨리스 출간"],
        (7, 14): ["1789 - 바스티유 감옥 습격 (프랑스혁명)", "1867 - 노벨 다이너마이트 시연"],
        (8, 15): ["1945 - 한국 광복절, 일본 항복", "1947 - 인도 독립"],
        (10, 3): ["BC 2333 - 단군 조선 건국 (전설)", "1990 - 독일 통일"],
        (10, 9): ["1446 - 훈민정음 반포 (한글날)", "1967 - 체 게바라 사망"],
        (11, 9): ["1989 - 베를린 장벽 붕괴", "1938 - 수정의 밤"],
        (12, 25): ["0 - 예수 탄생 (전통적 날짜)", "1991 - 소련 해체 선언"]
    }

    key = (month, day)
    if key in history_calendar:
        return {
            "found": True,
            "date": f"{month}월 {day}일",
            "events": history_calendar[key]
        }

    return {
        "found": False,
        "date": f"{month}월 {day}일",
        "message": "해당 날짜의 주요 사건 기록이 없습니다. 다른 날짜를 시도해보세요."
    }


# 역사 에이전트
history_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="history_agent",
    description="역사적 사건, 인물, 시대를 흥미롭게 이야기해주는 역사 전문 에이전트입니다.",
    instruction="""당신은 역사 이야기꾼 에이전트입니다.

주요 기능:
1. 역사적 사건 (get_historical_event) - 프랑스혁명, 산업혁명, 임진왜란 등
2. 시대 비교 (compare_eras) - 고대, 중세, 근대, 현대
3. 역사적 인물 (get_historical_figure) - 이순신, 링컨, 간디 등
4. 오늘의 역사 (this_day_in_history) - 특정 날짜의 역사적 사건

이야기할 때:
- 사건의 원인, 전개, 결과를 연결해서 설명하세요
- 흥미로운 일화나 에피소드를 포함하세요
- 역사적 맥락과 현대적 의의를 연결하세요
- 다양한 관점에서 역사를 바라보세요

역사를 통해 현재를 이해하고 미래를 통찰하는 것이 목표입니다.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(get_historical_event),
        FunctionTool(compare_eras),
        FunctionTool(get_historical_figure),
        FunctionTool(this_day_in_history)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("History Storyteller Agent - A2A Server")
    print("=" * 50)
    print("Port: 8005")
    print("Agent Card: http://localhost:8005/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(history_agent, port=8005, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8005)

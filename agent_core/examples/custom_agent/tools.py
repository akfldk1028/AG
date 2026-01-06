"""
커스텀 도구 정의

여기에 프로젝트별 도구를 정의합니다.
각 함수는 docstring이 있어야 에이전트가 이해할 수 있습니다.
"""

from typing import Dict, Any
import requests


def search_wikipedia(query: str) -> Dict[str, Any]:
    """
    위키피디아에서 검색합니다.
    
    Args:
        query: 검색할 키워드
        
    Returns:
        검색 결과 요약
    """
    try:
        url = "https://ko.wikipedia.org/api/rest_v1/page/summary/" + query
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            }
        else:
            return {"error": f"검색 실패: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def translate_to_english(text: str) -> Dict[str, str]:
    """
    한국어 텍스트를 영어로 번역합니다. (예시 - 실제로는 번역 API 연동 필요)
    
    Args:
        text: 번역할 한국어 텍스트
        
    Returns:
        번역 결과
    """
    # 실제 구현에서는 Google Translate API 등을 사용
    return {
        "original": text,
        "translated": f"[Translation of: {text}]",
        "note": "실제 번역 API 연동 필요"
    }


def get_weather(city: str) -> Dict[str, Any]:
    """
    도시의 날씨를 조회합니다. (예시 - 실제로는 날씨 API 연동 필요)
    
    Args:
        city: 도시 이름
        
    Returns:
        날씨 정보
    """
    # 실제 구현에서는 OpenWeatherMap API 등을 사용
    return {
        "city": city,
        "temperature": "20°C",
        "condition": "맑음",
        "note": "실제 날씨 API 연동 필요"
    }


# 이 프로젝트의 모든 도구
MY_TOOLS = [search_wikipedia, translate_to_english, get_weather]

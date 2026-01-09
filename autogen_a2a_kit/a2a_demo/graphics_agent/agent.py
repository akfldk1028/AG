# Computer Graphics Agent - A2A Protocol
# 컴퓨터 그래픽스 전문 에이전트

import os
import math
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


def color_space_convert(r: int, g: int, b: int, target: str = "hsv") -> dict:
    """RGB 색상을 다른 색공간으로 변환한다.

    Args:
        r: Red (0-255)
        g: Green (0-255)
        b: Blue (0-255)
        target: 대상 색공간 (hsv, hsl, cmyk)

    Returns:
        변환된 색상 값
    """
    r, g, b = r/255, g/255, b/255
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    # HSV 계산
    if delta == 0:
        h = 0
    elif max_c == r:
        h = 60 * (((g - b) / delta) % 6)
    elif max_c == g:
        h = 60 * ((b - r) / delta + 2)
    else:
        h = 60 * ((r - g) / delta + 4)

    s_v = 0 if max_c == 0 else delta / max_c
    v = max_c

    if target == "hsv":
        return {
            "input_rgb": [int(r*255), int(g*255), int(b*255)],
            "hsv": {"h": round(h, 1), "s": round(s_v * 100, 1), "v": round(v * 100, 1)},
            "description": "H(색상), S(채도), V(명도)",
            "use_case": "색상 조정, 팔레트 생성에 유용"
        }
    elif target == "hsl":
        l = (max_c + min_c) / 2
        s_l = 0 if delta == 0 else delta / (1 - abs(2*l - 1))
        return {
            "input_rgb": [int(r*255), int(g*255), int(b*255)],
            "hsl": {"h": round(h, 1), "s": round(s_l * 100, 1), "l": round(l * 100, 1)},
            "description": "H(색상), S(채도), L(밝기)",
            "use_case": "CSS/웹 디자인에 유용"
        }
    elif target == "cmyk":
        k = 1 - max_c
        if k == 1:
            c = m = y = 0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)
        return {
            "input_rgb": [int(r*255), int(g*255), int(b*255)],
            "cmyk": {"c": round(c*100, 1), "m": round(m*100, 1),
                    "y": round(y*100, 1), "k": round(k*100, 1)},
            "description": "Cyan, Magenta, Yellow, Key(Black)",
            "use_case": "인쇄물 제작에 사용"
        }
    return {"error": "지원하지 않는 색공간"}


def explain_render_pipeline() -> dict:
    """그래픽스 렌더링 파이프라인을 설명한다.

    Returns:
        렌더링 파이프라인 단계 설명
    """
    return {
        "pipeline_stages": [
            {
                "stage": "1. Application Stage",
                "description": "CPU에서 실행, 게임 로직, 물리 시뮬레이션",
                "output": "렌더링할 기하 데이터 (vertices, primitives)"
            },
            {
                "stage": "2. Geometry Processing",
                "description": "정점 셰이더, 테셀레이션, 지오메트리 셰이더",
                "substages": ["Vertex Shader", "Tessellation", "Geometry Shader", "Clipping", "Screen Mapping"],
                "output": "화면 좌표로 변환된 정점들"
            },
            {
                "stage": "3. Rasterization",
                "description": "삼각형을 픽셀(프래그먼트)로 변환",
                "process": "Triangle Setup → Triangle Traversal",
                "output": "프래그먼트(후보 픽셀)들"
            },
            {
                "stage": "4. Pixel Processing",
                "description": "프래그먼트 셰이더, 텍스처링, 라이팅",
                "substages": ["Fragment Shader", "Texturing", "Per-fragment Operations"],
                "output": "최종 픽셀 색상"
            },
            {
                "stage": "5. Output Merger",
                "description": "깊이 테스트, 스텐실 테스트, 블렌딩",
                "tests": ["Depth Test", "Stencil Test", "Alpha Blending"],
                "output": "프레임버퍼에 기록된 최종 이미지"
            }
        ],
        "modern_apis": ["OpenGL", "DirectX 12", "Vulkan", "Metal"],
        "key_concept": "GPU 병렬 처리로 수백만 픽셀을 동시에 처리"
    }


def shading_models() -> dict:
    """주요 셰이딩 모델들을 설명한다.

    Returns:
        셰이딩 모델 비교
    """
    return {
        "shading_models": {
            "Flat Shading": {
                "method": "면(polygon) 단위로 하나의 색상",
                "normal": "면 노말 사용",
                "pros": "빠른 계산",
                "cons": "각진 외관, 저품질",
                "use_case": "저사양 기기, 스타일화된 렌더링"
            },
            "Gouraud Shading": {
                "method": "정점에서 조명 계산 → 보간",
                "normal": "정점 노말 사용",
                "pros": "부드러운 외관, 비교적 빠름",
                "cons": "하이라이트 품질 낮음",
                "use_case": "실시간 렌더링 기본"
            },
            "Phong Shading": {
                "method": "픽셀마다 노말 보간 → 조명 계산",
                "normal": "보간된 노말 사용",
                "pros": "정확한 하이라이트, 고품질",
                "cons": "계산 비용 높음",
                "use_case": "고품질 실시간 렌더링"
            },
            "PBR (Physically Based Rendering)": {
                "method": "물리 기반 조명 모델",
                "components": ["Albedo", "Metallic", "Roughness", "Normal Map"],
                "pros": "사실적인 재질 표현",
                "cons": "복잡한 설정, 높은 계산 비용",
                "use_case": "현대 게임, 영화 VFX"
            }
        },
        "phong_reflection_model": {
            "formula": "I = I_ambient + I_diffuse + I_specular",
            "ambient": "환경광 (기본 밝기)",
            "diffuse": "확산 반사 (Lambertian)",
            "specular": "경면 반사 (하이라이트)"
        }
    }


def transformation_matrix(transform_type: str, params: dict) -> dict:
    """변환 행렬을 생성하고 설명한다.

    Args:
        transform_type: 변환 종류 (translate, rotate, scale)
        params: 변환 매개변수

    Returns:
        4x4 변환 행렬
    """
    if transform_type == "translate":
        tx = params.get("x", 0)
        ty = params.get("y", 0)
        tz = params.get("z", 0)
        return {
            "type": "Translation Matrix",
            "matrix": [
                [1, 0, 0, tx],
                [0, 1, 0, ty],
                [0, 0, 1, tz],
                [0, 0, 0, 1]
            ],
            "params": {"tx": tx, "ty": ty, "tz": tz},
            "effect": f"모든 점을 ({tx}, {ty}, {tz}) 만큼 이동"
        }
    elif transform_type == "scale":
        sx = params.get("x", 1)
        sy = params.get("y", 1)
        sz = params.get("z", 1)
        return {
            "type": "Scaling Matrix",
            "matrix": [
                [sx, 0, 0, 0],
                [0, sy, 0, 0],
                [0, 0, sz, 0],
                [0, 0, 0, 1]
            ],
            "params": {"sx": sx, "sy": sy, "sz": sz},
            "effect": f"각 축으로 ({sx}, {sy}, {sz}) 배율 조정"
        }
    elif transform_type == "rotate":
        axis = params.get("axis", "z")
        angle = params.get("angle", 0)
        rad = math.radians(angle)
        c, s = math.cos(rad), math.sin(rad)

        if axis == "z":
            matrix = [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        elif axis == "x":
            matrix = [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
        elif axis == "y":
            matrix = [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
        else:
            return {"error": "축은 x, y, z 중 하나"}

        return {
            "type": f"Rotation Matrix ({axis}-axis)",
            "matrix": [[round(v, 4) for v in row] for row in matrix],
            "params": {"axis": axis, "angle": angle},
            "effect": f"{axis}축 기준 {angle}도 회전"
        }
    return {"error": "지원하지 않는 변환 타입"}


# 컴퓨터 그래픽스 에이전트
graphics_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="graphics_agent",
    description="컴퓨터 그래픽스 이론과 렌더링 기술을 전문으로 하는 에이전트입니다. 색 공간, 셰이딩, 변환 행렬 등을 다룹니다.",
    instruction="""당신은 컴퓨터 그래픽스 전문가 에이전트입니다.

주요 기능:
1. 색 공간 변환 (color_space_convert) - RGB to HSV/HSL/CMYK
2. 렌더링 파이프라인 설명 (explain_render_pipeline)
3. 셰이딩 모델 비교 (shading_models)
4. 변환 행렬 생성 (transformation_matrix)

토론 시 역할:
- 시각적 표현의 관점에서 분석합니다
- 기술과 예술의 융합 관점을 제시합니다
- 실시간 렌더링 vs 오프라인 렌더링의 트레이드오프를 설명합니다
- 현대 그래픽스 기술 트렌드를 공유합니다

그래픽스의 기술적 깊이와 시각적 아름다움을 함께 전달해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(color_space_convert),
        FunctionTool(explain_render_pipeline),
        FunctionTool(shading_models),
        FunctionTool(transformation_matrix)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("Computer Graphics Agent - A2A Server")
    print("=" * 50)
    print("Port: 8008")
    print("Agent Card: http://localhost:8008/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(graphics_agent, port=8008, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8008)

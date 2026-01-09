# GPU & Parallel Computing Agent - A2A Protocol
# GPU 및 병렬 컴퓨팅 전문 에이전트

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


def gpu_architecture_compare() -> dict:
    """주요 GPU 아키텍처를 비교한다.

    Returns:
        NVIDIA vs AMD GPU 아키텍처 비교
    """
    return {
        "nvidia_cuda_cores": {
            "concept": "CUDA Core = 1개의 스레드를 실행하는 단위",
            "hierarchy": {
                "GPU": "여러 개의 SM (Streaming Multiprocessor)",
                "SM": "여러 개의 CUDA Core (32-128개)",
                "Warp": "32개 스레드가 동시 실행되는 단위"
            },
            "recent_architectures": {
                "Ampere (RTX 30xx)": "개선된 RT Core, Tensor Core 3세대",
                "Ada Lovelace (RTX 40xx)": "Shader Execution Reordering, DLSS 3",
                "Blackwell (RTX 50xx)": "5세대 Tensor Core, 향상된 레이트레이싱"
            }
        },
        "amd_compute_units": {
            "concept": "Compute Unit (CU) = NVIDIA SM과 유사",
            "hierarchy": {
                "GPU": "여러 개의 CU",
                "CU": "64개 Stream Processor",
                "Wavefront": "64개 스레드 (NVIDIA Warp = 32)"
            },
            "recent_architectures": {
                "RDNA 2 (RX 6xxx)": "레이트레이싱 도입, Infinity Cache",
                "RDNA 3 (RX 7xxx)": "칩렛 설계, 향상된 효율",
                "RDNA 4 (RX 8xxx)": "AI 가속 향상"
            }
        },
        "comparison": {
            "NVIDIA 장점": ["CUDA 생태계", "텐서 코어 (AI)", "레이트레이싱 성능"],
            "AMD 장점": ["가격 대비 성능", "전력 효율", "오픈 소스 드라이버"]
        }
    }


def parallel_speedup_analysis(serial_fraction: float, processors: int) -> dict:
    """암달의 법칙으로 병렬화 속도 향상을 분석한다.

    Args:
        serial_fraction: 직렬 실행 비율 (0-1, 예: 0.1 = 10%)
        processors: 프로세서 수

    Returns:
        속도 향상 분석 결과
    """
    if not 0 <= serial_fraction <= 1:
        return {"error": "serial_fraction은 0-1 사이여야 합니다"}

    parallel_fraction = 1 - serial_fraction

    # 암달의 법칙: S = 1 / (s + p/N)
    speedup = 1 / (serial_fraction + parallel_fraction / processors)

    # 최대 속도 향상 (프로세서 무한대)
    max_speedup = 1 / serial_fraction if serial_fraction > 0 else float('inf')

    # 다양한 프로세서 수에 대한 속도 향상
    speedups = {}
    for n in [2, 4, 8, 16, 32, 64, 128, 256, 1024]:
        speedups[n] = round(1 / (serial_fraction + parallel_fraction / n), 2)

    # 효율성 계산
    efficiency = speedup / processors * 100

    return {
        "amdahl_law": "S = 1 / (s + (1-s)/N)",
        "input": {
            "serial_fraction": f"{serial_fraction * 100}%",
            "parallel_fraction": f"{parallel_fraction * 100}%",
            "processors": processors
        },
        "result": {
            "speedup": round(speedup, 2),
            "max_speedup_limit": round(max_speedup, 2) if max_speedup != float('inf') else "∞",
            "efficiency": f"{round(efficiency, 1)}%"
        },
        "speedup_by_processors": speedups,
        "insight": f"직렬 부분이 {serial_fraction*100}%이므로, 프로세서를 아무리 늘려도 최대 {round(max_speedup, 1)}배까지만 빨라집니다."
    }


def memory_bandwidth_calc(memory_clock: float, bus_width: int,
                          memory_type: str = "GDDR6") -> dict:
    """GPU 메모리 대역폭을 계산한다.

    Args:
        memory_clock: 메모리 클럭 (MHz)
        bus_width: 메모리 버스 폭 (bits)
        memory_type: 메모리 타입 (GDDR5, GDDR6, GDDR6X, HBM2)

    Returns:
        메모리 대역폭 계산 결과
    """
    # 데이터 전송률 배수 (DDR = Double Data Rate)
    transfer_multiplier = {
        "GDDR5": 4,    # QDR (Quad Data Rate)
        "GDDR6": 16,   # 16n prefetch
        "GDDR6X": 16,  # PAM4 encoding
        "HBM2": 2,     # DDR
        "HBM3": 2      # DDR with higher clock
    }

    multiplier = transfer_multiplier.get(memory_type, 2)

    # 대역폭 = 클럭 × 배수 × 버스폭 / 8 (bytes)
    bandwidth_gbps = (memory_clock * multiplier * bus_width) / 8 / 1000

    return {
        "formula": "Bandwidth = Clock × Transfer Rate × Bus Width / 8",
        "input": {
            "memory_clock": f"{memory_clock} MHz",
            "bus_width": f"{bus_width} bits",
            "memory_type": memory_type,
            "transfer_multiplier": f"{multiplier}x"
        },
        "result": {
            "bandwidth": f"{round(bandwidth_gbps, 1)} GB/s",
            "effective_clock": f"{memory_clock * multiplier / 1000:.1f} Gbps per pin"
        },
        "comparison": {
            "RTX 4090 (GDDR6X)": "~1008 GB/s",
            "RX 7900 XTX (GDDR6)": "~960 GB/s",
            "H100 (HBM3)": "~3350 GB/s"
        }
    }


def cuda_programming_basics() -> dict:
    """CUDA 프로그래밍 기초 개념을 설명한다.

    Returns:
        CUDA 프로그래밍 핵심 개념
    """
    return {
        "execution_model": {
            "grid": "커널 실행 단위, 여러 블록으로 구성",
            "block": "스레드의 그룹, SM에서 실행",
            "thread": "실행의 기본 단위",
            "warp": "32개 스레드가 SIMT로 실행"
        },
        "memory_hierarchy": {
            "register": "가장 빠름, 스레드 전용",
            "shared_memory": "블록 내 스레드 공유, ~100x 레지스터보다 느림",
            "L1_cache": "자동 캐시, SM당 128KB",
            "L2_cache": "모든 SM 공유",
            "global_memory": "가장 느림, GPU VRAM"
        },
        "key_concepts": {
            "coalesced_access": "연속 메모리 접근으로 대역폭 최적화",
            "occupancy": "SM 활용률, 높을수록 좋음",
            "bank_conflict": "공유 메모리 뱅크 충돌 회피 필요",
            "warp_divergence": "분기문이 성능 저하 유발"
        },
        "optimization_tips": [
            "공유 메모리를 활용해 전역 메모리 접근 최소화",
            "코얼레스드 메모리 접근 패턴 사용",
            "점유율(Occupancy)을 높게 유지",
            "워프 다이버전스 최소화"
        ],
        "example_code": """
__global__ void vectorAdd(float *a, float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        c[i] = a[i] + b[i];
    }
}
// Launch: vectorAdd<<<numBlocks, blockSize>>>(a, b, c, n);
"""
    }


# GPU 및 병렬 컴퓨팅 에이전트
gpu_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="gpu_agent",
    description="GPU 아키텍처와 병렬 컴퓨팅을 전문으로 하는 에이전트입니다. CUDA, 메모리 대역폭, 암달의 법칙 등을 다룹니다.",
    instruction="""당신은 GPU 및 병렬 컴퓨팅 전문가 에이전트입니다.

주요 기능:
1. GPU 아키텍처 비교 (gpu_architecture_compare) - NVIDIA vs AMD
2. 병렬 속도 향상 분석 (parallel_speedup_analysis) - 암달의 법칙
3. 메모리 대역폭 계산 (memory_bandwidth_calc)
4. CUDA 프로그래밍 기초 (cuda_programming_basics)

토론 시 역할:
- 하드웨어-소프트웨어 최적화 관점을 제시합니다
- 병렬화의 한계와 가능성을 분석합니다
- 실제 성능 병목점을 식별합니다
- AI/ML 워크로드에서의 GPU 활용을 설명합니다

실용적이고 성능 중심적인 관점을 제공해주세요.
한국어로 응답해주세요.""",
    tools=[
        FunctionTool(gpu_architecture_compare),
        FunctionTool(parallel_speedup_analysis),
        FunctionTool(memory_bandwidth_calc),
        FunctionTool(cuda_programming_basics)
    ]
)


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    print("=" * 50)
    print("GPU & Parallel Computing Agent - A2A Server")
    print("=" * 50)
    print("Port: 8009")
    print("Agent Card: http://localhost:8009/.well-known/agent-card.json")
    print("=" * 50)

    a2a_app = to_a2a(gpu_agent, port=8009, host="127.0.0.1")
    uvicorn.run(a2a_app, host="127.0.0.1", port=8009)

# -*- coding: utf-8 -*-
"""
Multi-Agent Handoffs Web UI 실행
autogen_source/python/samples/core_streaming_handoffs_fastapi 사용
"""

import os
import sys

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] OPENAI_API_KEY 필요!")
    print("  .env 파일에 OPENAI_API_KEY=sk-... 추가")
    sys.exit(1)

# sample 폴더로 이동
sample_dir = os.path.join(
    os.path.dirname(__file__),
    "autogen_source", "python", "samples", "core_streaming_handoffs_fastapi"
)

if not os.path.exists(sample_dir):
    print(f"[ERROR] Sample 폴더 없음: {sample_dir}")
    sys.exit(1)

os.chdir(sample_dir)

# model_config.yaml 생성
config_content = f"""provider: autogen_ext.models.openai.OpenAIChatCompletionClient
config:
  model: gpt-4o-mini
  api_key: {api_key}
"""

with open("model_config.yaml", "w") as f:
    f.write(config_content)

print("=" * 60)
print("  Multi-Agent Handoffs Web UI")
print("  http://localhost:8501")
print("=" * 60)
print()
print("Agents:")
print("  - Triage Agent: 문의 분류")
print("  - Sales Agent: 판매 담당")
print("  - Issues & Repairs Agent: 환불/수리 담당")
print()
print("Starting server...")
print()

# sys.path에 추가하고 uvicorn 실행
sys.path.insert(0, sample_dir)
import uvicorn
uvicorn.run("app:app", host="0.0.0.0", port=8501, reload=False)

"""
PyAutoGUI MCP Server Configuration
===================================

AG_action primitives 경로 및 서버 설정.
"""

import sys
from pathlib import Path

# AG_action 경로 설정
# 이 파일 기준 상위로 탐색하여 AG_action 찾기
_current_dir = Path(__file__).resolve().parent
_search_dir = _current_dir

AG_ACTION_PATH = None

# 방법 1: 상위 디렉토리 탐색
for _ in range(10):
    _search_dir = _search_dir.parent
    _candidate = _search_dir / "AG_action"
    if _candidate.exists() and (_candidate / "primitives").exists():
        AG_ACTION_PATH = _search_dir
        break

# 방법 2: 하드코딩 fallback (개발용)
if not AG_ACTION_PATH:
    _hardcoded = Path("D:/Data/22_AG/autogen_a2a_kit")
    if (_hardcoded / "AG_action" / "primitives").exists():
        AG_ACTION_PATH = _hardcoded

# sys.path에 추가
if AG_ACTION_PATH and str(AG_ACTION_PATH) not in sys.path:
    sys.path.insert(0, str(AG_ACTION_PATH))

# 서버 설정
SERVER_NAME = "pyautogui-mcp"
SERVER_VERSION = "0.1.0"

# PyAutoGUI 설정
PYAUTOGUI_FAILSAFE = True  # 코너로 마우스 이동시 중지
PYAUTOGUI_PAUSE = 0.1      # 액션 간 딜레이 (초)

# 스크린샷 설정
DEFAULT_SCALE_TARGET = "XGA"  # XGA (1024x768) or WXGA (1280x800)
SCREENSHOT_FORMAT = "PNG"

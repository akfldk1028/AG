@echo off
chcp 65001 >nul
cd /d %~dp0
echo.
echo ============================================================
echo   AutoGen + A2A Kit - Developer Setup
echo   (AutoGen 소스 수정 가능한 개발자용)
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Install Git first.
    pause
    exit /b 1
)
echo [OK] Git found

REM Create venv
echo.
echo [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo       Created: venv/
) else (
    echo       Already exists: venv/
)

REM Activate venv
call venv\Scripts\activate.bat

REM Clone AutoGen source
echo.
echo [2/5] Cloning AutoGen source (for development)...
if not exist "autogen_source" (
    git clone https://github.com/microsoft/autogen.git autogen_source
    echo       Cloned: autogen_source/
) else (
    echo       Already exists: autogen_source/
    echo       Updating...
    cd autogen_source
    git pull
    cd ..
)

REM Install AutoGen in editable mode
echo.
echo [3/5] Installing AutoGen (editable mode)...
pip install --upgrade pip -q
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"

REM Install other dependencies
echo.
echo [4/5] Installing other dependencies...
pip install -r requirements.txt

REM Verify
echo.
echo [5/5] Verifying installation...
python -c "from a2a_client import create_a2a_tool; print('       a2a_client: OK')"
python -c "from agents import quick_agent; print('       agents: OK')"
python -c "from autogen_agentchat.agents import AssistantAgent; print('       autogen-agentchat: OK (editable)')"
python -c "import autogen_agentchat; print('       Source:', autogen_agentchat.__file__)"

echo.
echo ============================================================
echo   Setup Complete! (Developer Mode)
echo ============================================================
echo.
echo   AutoGen source: autogen_source/
echo   Edit AutoGen:   autogen_source\python\packages\...
echo.
echo   Next steps:
echo   1. Set API key:  set OPENAI_API_KEY=sk-...
echo   2. Activate:     venv\Scripts\activate
echo   3. Start A2A:    python a2a_demo\remote_agent\agent.py
echo   4. Run example:  python example.py
echo.
pause

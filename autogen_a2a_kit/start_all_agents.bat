@echo off
chcp 65001 > nul
echo ============================================
echo   A2A Agents Launcher (All)
echo ============================================
echo.

cd /d D:\Data\22_AG\autogen_a2a_kit

REM .env 파일에서 OPENAI_API_KEY 로드
if exist .env (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if "%%a"=="OPENAI_API_KEY" set OPENAI_API_KEY=%%b
    )
)

if "%OPENAI_API_KEY%"=="" (
    echo [ERROR] OPENAI_API_KEY not found!
    echo Please create .env file first.
    pause
    exit /b 1
)

echo [OK] OPENAI_API_KEY loaded
echo.
echo Starting A2A Agents...
echo.

REM Poetry Agent (8003)
echo [1/8] Starting poetry_agent on port 8003...
start "poetry_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\poetry_agent && python agent.py"

REM Philosophy Agent (8004)
echo [2/8] Starting philosophy_agent on port 8004...
start "philosophy_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\philosophy_agent && python agent.py"

REM History Agent (8005)
echo [3/8] Starting history_agent on port 8005...
start "history_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\history_agent && python agent.py"

REM Calculator Agent (8006)
echo [4/8] Starting calculator_agent on port 8006...
start "calculator_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\calculator_agent && python agent.py"

REM Math Agent (8007)
echo [5/8] Starting math_agent on port 8007...
start "math_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\math_agent && python agent.py"

REM Graphics Agent (8008)
echo [6/8] Starting graphics_agent on port 8008...
start "graphics_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\graphics_agent && python agent.py"

REM GPU Agent (8009)
echo [7/8] Starting gpu_agent on port 8009...
start "gpu_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\gpu_agent && python agent.py"

REM GUI Test Agent (8120)
echo [8/8] Starting gui_test_agent on port 8120...
start "gui_test_agent" cmd /k "cd /d D:\Data\22_AG\autogen_a2a_kit\a2a_demo\gui_test_agent && python agent.py"

echo.
echo ============================================
echo   All 8 agents started!
echo ============================================
echo.
echo Ports:
echo   poetry_agent     : 8003
echo   philosophy_agent : 8004
echo   history_agent    : 8005
echo   calculator_agent : 8006
echo   math_agent       : 8007
echo   graphics_agent   : 8008
echo   gpu_agent        : 8009
echo   gui_test_agent   : 8120
echo.
echo Next: Run start_studio.bat to start AutoGen Studio
echo.
pause

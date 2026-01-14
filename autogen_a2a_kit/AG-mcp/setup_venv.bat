@echo off
REM ============================================
REM PyAutoGUI MCP Server - Virtual Environment Setup
REM ============================================
REM 가상환경 생성 및 패키지 설치
REM 최초 1회만 실행하면 됩니다.
REM ============================================

echo [SETUP] PyAutoGUI MCP Server - Virtual Environment Setup
echo.

cd /d "%~dp0pyautogui_mcp"

REM 기존 가상환경 확인
if exist "venv" (
    echo [INFO] Virtual environment already exists.
    echo [INFO] Delete venv folder if you want to recreate.
    echo.
    set /p RECREATE="Recreate venv? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo [INFO] Removing existing venv...
        rmdir /s /q venv
    ) else (
        echo [INFO] Skipping venv creation.
        goto :install_packages
    )
)

REM 가상환경 생성
echo [SETUP] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv. Make sure Python is installed.
    pause
    exit /b 1
)

:install_packages
echo.
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [SETUP] Installing packages from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b 1
)

echo.
echo ============================================
echo [SUCCESS] Setup complete!
echo ============================================
echo.
echo To start the MCP server, run:
echo   start_mcp.bat
echo.
echo To add to Claude Code:
echo   claude mcp add pyautogui-mcp "%~dp0start_mcp.bat"
echo.

pause

@echo off
REM ============================================
REM PyAutoGUI MCP Server - Start Script
REM ============================================
REM MCP 서버를 가상환경에서 실행합니다.
REM Claude Code/Desktop에서 호출됩니다.
REM ============================================

cd /d "%~dp0pyautogui_mcp"

REM 가상환경 확인
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo [ERROR] Run setup_venv.bat first.
    exit /b 1
)

REM 가상환경에서 서버 실행 (stdio transport)
venv\Scripts\python.exe server.py

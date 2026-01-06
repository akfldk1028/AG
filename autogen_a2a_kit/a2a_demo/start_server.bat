@echo off
chcp 65001 >nul
echo ============================================
echo Starting A2A Server (Prime Checker)
echo ============================================
echo.

cd /d %~dp0..
call venv\Scripts\activate.bat

echo Starting A2A server on port 8001...
echo.

python a2a_demo\remote_agent\agent.py

pause

@echo off
echo ========================================
echo Philosophy Wisdom Agent - Port 8004
echo ========================================
cd /d "%~dp0"
call ..\..\autogen_a2a_kit\venv\Scripts\activate.bat
python agent.py
pause

@echo off
echo ========================================
echo History Storyteller Agent - Port 8005
echo ========================================
cd /d "%~dp0"
call ..\..\autogen_a2a_kit\venv\Scripts\activate.bat
python agent.py
pause

@echo off
echo ========================================
echo Poetry Analysis Agent - Port 8003
echo ========================================
cd /d "%~dp0"
call ..\..\autogen_a2a_kit\venv\Scripts\activate.bat
python agent.py
pause

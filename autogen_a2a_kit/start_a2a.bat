@echo off
chcp 65001 >nul
cd /d D:\Data\22_AG\autogen_a2a_kit
for /f "tokens=2 delims==" %%a in ('findstr "OPENAI_API_KEY" .env') do set OPENAI_API_KEY=%%a
echo Starting A2A Server on port 8001...
venv\Scripts\python a2a_demo\remote_agent\agent.py

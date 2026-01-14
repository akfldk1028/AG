# ============================================
# PyAutoGUI MCP Server - Start Script (PowerShell)
# ============================================
# MCP 서버를 가상환경에서 실행합니다.
# ============================================

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$mcpDir = Join-Path $scriptDir "pyautogui_mcp"
$venvPython = Join-Path $mcpDir "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "[ERROR] Virtual environment not found. Run setup_venv.bat first."
    exit 1
}

Set-Location $mcpDir
& $venvPython server.py

# AutoGen Studio + A2A Agents 실행 스크립트
# Usage: .\run_all.ps1

Write-Host "=== AutoGen + A2A Integration Kit ===" -ForegroundColor Cyan

# 1. .env 파일에서 환경변수 로드
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Write-Host "[OK] Loading .env file..." -ForegroundColor Green
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "Create .env from .env.example and set OPENAI_API_KEY" -ForegroundColor Yellow
    exit 1
}

# 2. OPENAI_API_KEY 확인
if (-not $env:OPENAI_API_KEY) {
    Write-Host "[ERROR] OPENAI_API_KEY not set in .env!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] OPENAI_API_KEY loaded" -ForegroundColor Green

# 3. 포트 8081 확인
$port8081 = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($port8081) {
    Write-Host "[WARN] Port 8081 already in use (PID: $($port8081.OwningProcess))" -ForegroundColor Yellow
    Write-Host "       AutoGen Studio may already be running at http://127.0.0.1:8081" -ForegroundColor Yellow
} else {
    # 4. AutoGen Studio 시작
    Write-Host "[START] Starting AutoGen Studio on port 8081..." -ForegroundColor Cyan
    $pythonCode = "from autogenstudio.web.app import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8081)"
    Start-Process -FilePath "python" -ArgumentList "-c", "`"$pythonCode`"" -NoNewWindow
    Start-Sleep -Seconds 3
}

# 5. A2A 에이전트 시작 (옵션)
$a2aPath = Join-Path $PSScriptRoot "a2a_demo"
if (Test-Path $a2aPath) {
    Write-Host ""
    Write-Host "A2A agents available in: $a2aPath" -ForegroundColor Gray
    Write-Host "To start individual A2A agents:" -ForegroundColor Gray
    Write-Host "  cd a2a_demo/calculator_agent && python agent.py" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== AutoGen Studio Ready ===" -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:8081" -ForegroundColor Cyan

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

# 5. A2A 에이전트 시작 (7개 에이전트)
$a2aPath = Join-Path $PSScriptRoot "a2a_demo"
$agents = @(
    @{Name="poetry_agent"; Port=8003},
    @{Name="philosophy_agent"; Port=8004},
    @{Name="history_agent"; Port=8005},
    @{Name="calculator_agent"; Port=8006},
    @{Name="math_agent"; Port=8007},
    @{Name="graphics_agent"; Port=8008},
    @{Name="gpu_agent"; Port=8009}
)

if (Test-Path $a2aPath) {
    Write-Host ""
    Write-Host "[START] Starting A2A Agents..." -ForegroundColor Cyan
    foreach ($agent in $agents) {
        $agentPath = Join-Path $a2aPath $agent.Name
        if (Test-Path $agentPath) {
            $portInUse = Get-NetTCPConnection -LocalPort $agent.Port -ErrorAction SilentlyContinue
            if (-not $portInUse) {
                Write-Host "  Starting $($agent.Name) on port $($agent.Port)..." -ForegroundColor Gray
                Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$agentPath'; python agent.py"
            } else {
                Write-Host "  $($agent.Name) already running on port $($agent.Port)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "=== AutoGen Studio Ready ===" -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:8081" -ForegroundColor Cyan

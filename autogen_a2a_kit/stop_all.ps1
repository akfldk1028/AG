# AutoGen Studio + A2A Agents 종료 스크립트
# Usage: .\stop_all.ps1

Write-Host "=== Stopping AutoGen Services ===" -ForegroundColor Cyan

# 포트 8081 (AutoGen Studio)
$port8081 = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($port8081) {
    Write-Host "[STOP] Stopping AutoGen Studio (PID: $($port8081.OwningProcess))..." -ForegroundColor Yellow
    Stop-Process -Id $port8081.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] AutoGen Studio stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] AutoGen Studio not running" -ForegroundColor Gray
}

# A2A 에이전트 포트들 (8002-8010)
$a2aPorts = 8002..8010
foreach ($port in $a2aPorts) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "[STOP] Stopping A2A agent on port $port (PID: $($conn.OwningProcess))..." -ForegroundColor Yellow
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "=== All Services Stopped ===" -ForegroundColor Green

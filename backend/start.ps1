# 潮汕文化宣传平台 — 后端启动脚本
# 自动清理端口占用，防止 WinError 10013

$port = 8000

Write-Host "=== 潮汕文化宣传平台 后端启动 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 清理占用端口 8000 的旧进程
$pidOnPort = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($pidOnPort) {
    foreach ($p in $pidOnPort) {
        $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "[清理] 终止旧进程: PID=$p ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    Write-Host "[清理] 端口 $port 已释放" -ForegroundColor Green
}
else {
    Write-Host "[检查] 端口 $port 空闲" -ForegroundColor Green
}

# 2. 清理 Python 缓存
Get-ChildItem -Path $PSScriptRoot -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 3. 启动服务
Write-Host ""
Write-Host "[启动] uvicorn main:app --reload --host 0.0.0.0 --port $port" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port $port

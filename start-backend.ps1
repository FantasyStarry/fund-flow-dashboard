#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fund Flow Dashboard 后端启动脚本
.DESCRIPTION
    使用 Uvicorn 启动 FastAPI 后端服务
.EXAMPLE
    .\start-backend.ps1
    .\start-backend.ps1 -Port 8080
    .\start-backend.ps1 -Production
#>

param(
    [int]$Port = 8000,
    [switch]$Production,
    [int]$Workers = 4,
    [string]$Host = "0.0.0.0"
)

$ErrorActionPreference = "Stop"

# 颜色定义
$Green = "`e[32m"
$Blue = "`e[34m"
$Yellow = "`e[33m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Fund Flow Dashboard 后端服务启动器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 获取项目根目录
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPath = Join-Path $ProjectRoot "backend"

# 检查 backend 目录
if (-not (Test-Path $BackendPath)) {
    Write-Host "[错误] 找不到 backend 目录: $BackendPath" -ForegroundColor Red
    exit 1
}

Set-Location $BackendPath

# 检查虚拟环境
$VenvPath = Join-Path $BackendPath "venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "[信息] 使用虚拟环境: venv" -ForegroundColor Blue
    $PythonCmd = $VenvPython
} else {
    Write-Host "[警告] 未找到虚拟环境，使用系统 Python" -ForegroundColor Yellow
    $PythonCmd = "python"
}

# 检查 uvicorn 是否安装
Write-Host "[信息] 检查 uvicorn..." -ForegroundColor Blue
$uvicornCheck = & $PythonCmd -c "import uvicorn; print('ok')" 2>&1
if ($uvicornCheck -ne "ok") {
    Write-Host "[错误] uvicorn 未安装，请先运行: pip install uvicorn[standard]" -ForegroundColor Red
    exit 1
}

# 构建启动命令
if ($Production) {
    Write-Host "[信息] 生产模式启动" -ForegroundColor Yellow
    Write-Host "  工作进程: $Workers" -ForegroundColor Gray
    $uvicornArgs = @(
        "-m", "uvicorn",
        "app.main:app",
        "--host", $Host,
        "--port", $Port,
        "--workers", $Workers,
        "--log-level", "info"
    )
} else {
    Write-Host "[信息] 开发模式启动 (热重载已启用)" -ForegroundColor Green
    $uvicornArgs = @(
        "-m", "uvicorn",
        "app.main:app",
        "--host", $Host,
        "--port", $Port,
        "--reload",
        "--log-level", "info"
    )
}

Write-Host "`n[配置]" -ForegroundColor Cyan
Write-Host "  主机: $Host" -ForegroundColor White
Write-Host "  端口: $Port" -ForegroundColor White
Write-Host "  路径: $BackendPath" -ForegroundColor White
Write-Host "  命令: $PythonCmd $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# 启动服务
try {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  正在启动服务..." -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    & $PythonCmd @uvicornArgs
} catch {
    Write-Host "`n[错误] 启动失败: $_" -ForegroundColor Red
    exit 1
}

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fund Flow Dashboard 开发环境启动脚本
.DESCRIPTION
    同时启动后端 (Uvicorn) 和前端 (Next.js) 开发服务器
.EXAMPLE
    .\start-dev.ps1
#>

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

# 颜色定义
$Green = "`e[32m"
$Blue = "`e[34m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

function Write-Info($msg) { Write-Host "${Blue}[INFO]${Reset} $msg" }
function Write-Success($msg) { Write-Host "${Green}[SUCCESS]${Reset} $msg" }
function Write-Warning($msg) { Write-Host "${Yellow}[WARNING]${Reset} $msg" }
function Write-Error($msg) { Write-Host "${Red}[ERROR]${Reset} $msg" }

# 获取项目根目录
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Fund Flow Dashboard 开发环境启动器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 存储进程ID用于后续清理
$global:BackendJob = $null
$global:FrontendJob = $null

# 清理函数
function Cleanup {
    Write-Host "`n" -NoNewline
    Write-Warning "正在关闭服务..."
    
    if ($global:BackendJob) {
        Stop-Job -Job $global:BackendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $global:BackendJob -ErrorAction SilentlyContinue
        Write-Info "后端服务已停止"
    }
    
    if ($global:FrontendJob) {
        Stop-Job -Job $global:FrontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $global:FrontendJob -ErrorAction SilentlyContinue
        Write-Info "前端服务已停止"
    }
    
    # 清理端口占用
    Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | 
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    
    Write-Success "清理完成"
    exit
}

# 注册清理事件
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup } | Out-Null
$null = [Console]::TreatControlCAsInput = $true

# 启动后端
function Start-Backend {
    Write-Info "正在启动后端服务..."
    Write-Host "  路径: backend/" -ForegroundColor Gray
    Write-Host "  端口: $BackendPort" -ForegroundColor Gray
    Write-Host "  命令: uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --reload`n" -ForegroundColor Gray
    
    $backendScript = {
        param($root, $port)
        Set-Location "$root\backend"
        & uvicorn app.main:app --host 0.0.0.0 --port $port --reload --log-level info
    }
    
    $global:BackendJob = Start-Job -ScriptBlock $backendScript -ArgumentList $ProjectRoot, $BackendPort
    
    # 等待后端启动
    $retries = 0
    $maxRetries = 30
    $started = $false
    
    while ($retries -lt $maxRetries -and -not $started) {
        Start-Sleep -Milliseconds 500
        $retries++
        
        # 检查端口是否被监听
        $connection = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | 
                      Where-Object { $_.State -eq 'Listen' }
        
        if ($connection) {
            $started = $true
        }
        
        # 检查是否有错误输出
        $jobOutput = Receive-Job -Job $global:BackendJob -ErrorAction SilentlyContinue
        if ($jobOutput -match "error|Error|ERROR") {
            Write-Error "后端启动失败: $jobOutput"
            Cleanup
        }
    }
    
    if ($started) {
        Write-Success "后端服务已启动!"
        Write-Host "  API文档: http://localhost:$BackendPort/docs`n" -ForegroundColor Green
    } else {
        Write-Error "后端服务启动超时"
        Cleanup
    }
}

# 启动前端
function Start-Frontend {
    Write-Info "正在启动前端服务..."
    Write-Host "  路径: frontend/" -ForegroundColor Gray
    Write-Host "  端口: $FrontendPort" -ForegroundColor Gray
    Write-Host "  命令: npm run dev`n" -ForegroundColor Gray
    
    $frontendScript = {
        param($root, $port)
        Set-Location "$root\frontend"
        $env:PORT = $port
        & npm run dev
    }
    
    $global:FrontendJob = Start-Job -ScriptBlock $frontendScript -ArgumentList $ProjectRoot, $FrontendPort
    
    # 等待前端启动
    $retries = 0
    $maxRetries = 60
    $started = $false
    
    while ($retries -lt $maxRetries -and -not $started) {
        Start-Sleep -Milliseconds 500
        $retries++
        
        # 检查端口是否被监听
        $connection = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | 
                      Where-Object { $_.State -eq 'Listen' }
        
        if ($connection) {
            $started = $true
        }
        
        # 输出前端日志
        $jobOutput = Receive-Job -Job $global:FrontendJob -ErrorAction SilentlyContinue
        if ($jobOutput) {
            Write-Host $jobOutput -ForegroundColor DarkGray
        }
    }
    
    if ($started) {
        Write-Success "前端服务已启动!"
        Write-Host "  访问地址: http://localhost:$FrontendPort`n" -ForegroundColor Green
    } else {
        Write-Warning "前端服务启动可能较慢，请稍候..."
    }
}

# 主逻辑
try {
    if (-not $FrontendOnly) {
        Start-Backend
    }
    
    if (-not $BackendOnly) {
        Start-Frontend
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  所有服务已启动!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    
    if (-not $FrontendOnly) {
        Write-Host "  后端 API: http://localhost:$BackendPort" -ForegroundColor White
        Write-Host "  API文档: http://localhost:$BackendPort/docs" -ForegroundColor White
    }
    if (-not $BackendOnly) {
        Write-Host "  前端页面: http://localhost:$FrontendPort" -ForegroundColor White
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`n按 Ctrl+C 停止所有服务`n" -ForegroundColor Yellow
    
    # 持续监控输出
    while ($true) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq "C" -and $key.Modifiers -eq "Control") {
                Cleanup
            }
        }
        
        if ($global:BackendJob) {
            $output = Receive-Job -Job $global:BackendJob -ErrorAction SilentlyContinue
            if ($output) { Write-Host "[后端] $output" -ForegroundColor Blue }
        }
        
        if ($global:FrontendJob) {
            $output = Receive-Job -Job $global:FrontendJob -ErrorAction SilentlyContinue
            if ($output) { Write-Host "[前端] $output" -ForegroundColor Magenta }
        }
        
        Start-Sleep -Milliseconds 100
    }
} catch {
    Write-Error "发生错误: $_"
    Cleanup
}

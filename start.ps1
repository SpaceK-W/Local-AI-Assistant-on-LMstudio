$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# 强制控制台使用 UTF-8 输出
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Pause-And-Exit {
    param(
        [string]$Message,
        [int]$Code = 1
    )
    Write-Host $Message -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit $Code
}

$PythonCommand = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = 'python'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = 'py'
} else {
    Pause-And-Exit 'Python environment not found. Please install Python 3.x.'
}

Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'WebProject1 Launcher' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Python Executable: $PythonCommand" -ForegroundColor Gray

if (-not (Test-Path '.venv')) {
    Write-Host 'Creating virtual environment (.venv)...' -ForegroundColor Yellow
    & $PythonCommand -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Pause-And-Exit 'Failed to create virtual environment.'
    }
}

$ActivateScript = Join-Path $ProjectRoot '.venv\Scripts\Activate.ps1'
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Pause-And-Exit 'Virtual environment python.exe missing.'
}

Write-Host 'Activating virtual environment...' -ForegroundColor Yellow
. $ActivateScript

if (-not (Test-Path 'requirements.txt')) {
    Pause-And-Exit 'requirements.txt not found.'
}

if (-not (Test-Path '.env') -and (Test-Path '.env.example')) {
    Write-Host 'Copying .env.example to .env...' -ForegroundColor Yellow
    Copy-Item '.env.example' '.env' -Force
}

Write-Host 'Installing dependencies...' -ForegroundColor Yellow
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Pause-And-Exit 'pip install failed. Check network or package requirements.'
}

$Url = 'http://127.0.0.1:5000/'
Write-Host "Starting app, launching browser at: $Url" -ForegroundColor Green

Start-Job -ScriptBlock {
    param($TargetUrl)
    for ($i = 0; $i -lt 90; $i++) {
        try {
            Invoke-WebRequest -Uri $TargetUrl -UseBasicParsing -TimeoutSec 2 | Out-Null
            Start-Process $TargetUrl | Out-Null
            return
        } catch {
            Start-Sleep -Seconds 1
        }
    }
} -ArgumentList $Url | Out-Null

& $VenvPython app.py
$ExitCode = $LASTEXITCODE

Get-Job | Stop-Job -Force -ErrorAction SilentlyContinue | Out-Null
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue | Out-Null

if ($ExitCode -ne 0) {
    Pause-And-Exit "Application exited with code: $ExitCode"
}

Write-Host 'Application stopped normally.' -ForegroundColor Green
Read-Host 'Press Enter to exit'
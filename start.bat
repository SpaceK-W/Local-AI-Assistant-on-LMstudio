@echo off
setlocal
cd /d "%~dp0"
echo 正在启动，请查看下方错误信息... 
powershell -NoExit -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
endlocal

@echo off
setlocal
cd /d "%~dp0"
title AI Assistant - Setup

echo ==========================================
echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python NOT found. Trying to install via winget...
    winget install -e --id Python.Python.3.11 --scope machine
    echo Please RESTART this script after Python install is done.
    pause
    exit
)

echo [2/3] Creating Virtual Environment (venv)...
if not exist venv (
    python -m venv venv
)

echo [3/3] Installing components...
venv\Scripts\python.exe -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ==========================================
echo SETUP DONE! Please run Start.bat now.
echo ==========================================
pause
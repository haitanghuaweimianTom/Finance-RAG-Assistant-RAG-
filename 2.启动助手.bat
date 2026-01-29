@echo off
setlocal
cd /d "%~dp0"
title AI Assistant - Running

if not exist venv (
    echo ERROR: venv not found. Run Install.bat first.
    pause
    exit
)

echo Starting web interface...
venv\Scripts\python.exe -m streamlit run frontend.py
pause
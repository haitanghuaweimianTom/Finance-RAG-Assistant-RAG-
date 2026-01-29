@echo off
setlocal
cd /d "%~dp0"
title AI Assistant - Updating Database

:: 1. Check if environment exists
if not exist venv (
    echo ERROR: venv not found. Run Install.bat first.
    pause
    exit
)

:: 2. Check if PDF folder exists
if not exist "data-rawpdf" (
    echo ERROR: Folder [data-rawpdf] not found.
    echo Please create it and put your PDFs inside.
    pause
    exit
)

echo ==========================================
echo [1/2] Extracting text from PDFs...
venv\Scripts\python.exe data_process.py

echo.
echo [2/2] Generating embeddings and saving to DB...
venv\Scripts\python.exe build_vector_db.py

echo ==========================================
echo UPDATE SUCCESSFUL!
echo Your database is now ready for questions.
echo ==========================================
pause
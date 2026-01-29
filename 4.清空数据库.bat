@echo off
setlocal
cd /d "%~dp0"
title AI Assistant - Reset Database

echo ==========================================
echo WARNING: This will PERMANENTLY delete:
echo 1. Vector Database (chroma_db)
echo 2. Processed Chunks (chunks)
echo 3. Cleaned Texts (clean_texts)
echo ==========================================
set /p confirm="Are you sure you want to reset? (Y/N): "

if /i "%confirm%" neq "Y" (
    echo Reset cancelled.
    pause
    exit
)

echo Cleaning up folders...

if exist chroma_db (
    echo Deleting chroma_db...
    rd /s /q chroma_db
)

if exist chunks (
    echo Deleting chunks...
    rd /s /q chunks
)

if exist clean_texts (
    echo Deleting clean_texts...
    rd /s /q clean_texts
)

echo.
echo ==========================================
echo RESET COMPLETE! 
echo All processed data has been removed.
echo Please run [Update.bat] to re-import your PDFs.
echo ==========================================
pause
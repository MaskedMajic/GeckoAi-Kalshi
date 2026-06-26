@echo off
title GeckoAI Kalshi

cd /d "%~dp0"

echo ==========================
echo Starting GeckoAI...
echo ==========================

if exist venv\Scripts\activate.bat (
call venv\Scripts\activate.bat
)

python start.py

echo.
echo Bot exited.
pause

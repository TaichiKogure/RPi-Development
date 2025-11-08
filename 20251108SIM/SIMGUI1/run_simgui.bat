@echo off
setlocal

REM Change to script directory
cd /d "%~dp0"

if not exist venv (
  echo [SETUP] Creating virtual environment...
  python -m venv venv
)

echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo [SETUP] Installing requirements...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

REM Launch GUI
python -u gui\main.py

endlocal

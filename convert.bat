@echo off
REM Wrapper script for running the CLI tool on Windows

cd /d %~dp0\backend

REM Check if Python virtual environment exists
if not exist venv (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the CLI tool with all arguments
python cli.py %*

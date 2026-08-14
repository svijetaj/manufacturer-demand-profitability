@echo off
REM Double-click launcher for Windows Desktop App

cd /d "%~dp0"

IF NOT EXIST ".venv" (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

IF NOT EXIST "finance.duckdb" (
    python scripts\ingest_to_duckdb.py
)

python desktop_app.py

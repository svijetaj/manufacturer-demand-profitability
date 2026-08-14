@echo off
REM One-Click Desktop Dashboard Launcher for Windows

cd /d "%~dp0"

IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

IF NOT EXIST "finance.duckdb" (
    echo Initializing DuckDB database...
    python scripts\ingest_to_duckdb.py
)

echo Launching Finance & Demand Desktop Dashboard...
streamlit run app.py

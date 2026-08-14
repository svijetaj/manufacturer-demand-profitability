#!/bin/bash
# One-Click Desktop Dashboard Launcher for macOS / Linux

cd "$(dirname "$0")"

# Check if .venv exists, otherwise create it and install requirements
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Ensure database is populated
if [ ! -f "finance.duckdb" ]; then
    echo "Initializing DuckDB database..."
    python scripts/ingest_to_duckdb.py
fi

echo "Launching Finance & Demand Desktop Dashboard..."
streamlit run app.py

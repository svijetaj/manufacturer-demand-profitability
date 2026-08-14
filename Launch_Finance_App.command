#!/bin/bash
# Double-click launcher for macOS Desktop App

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Ensure virtual environment is ready
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Ensure database exists
if [ ! -f "finance.duckdb" ]; then
    python scripts/ingest_to_duckdb.py
fi

# Launch native desktop app window
python desktop_app.py

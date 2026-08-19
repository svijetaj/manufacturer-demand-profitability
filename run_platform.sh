#!/usr/bin/env bash
# ==============================================================================
# Meridian Corp — Demand & Profitability Intelligence Platform Launcher
# Starts FastAPI backend (port 8000) and Next.js frontend (port 3000)
# ==============================================================================

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🚀 Launching Meridian Corp Intelligence Platform (v2.0)"
echo "   Backend: FastAPI REST on http://localhost:8000"
echo "   Frontend: Next.js 15 on http://localhost:3000"
echo "============================================================"

# Ensure virtual environment exists
if [ -d ".venv" ]; then
    PYTHON_EXEC="./.venv/bin/python"
    UVICORN_EXEC="./.venv/bin/uvicorn"
else
    PYTHON_EXEC="python3"
    UVICORN_EXEC="uvicorn"
fi

# Process flags
if [ "$1" = "--clean" ]; then
    echo "🧹 Cleaning Next.js build cache (.next)..."
    rm -rf "$PROJECT_ROOT/frontend/.next"
fi

# Cleanup on exit
trap 'kill 0' SIGINT SIGTERM EXIT

# Start FastAPI Backend in background
echo "⚡ Starting FastAPI Backend..."
PYTHONPATH=. $UVICORN_EXEC backend.main:app --port 8000 --host 127.0.0.1 &
BACKEND_PID=$!

# Wait briefly for backend to warm up
sleep 2

# Start Next.js Frontend
echo "🌐 Starting Next.js Frontend..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Open browser to Next.js
sleep 2
if command -v open >/dev/null 2>&1; then
    open "http://localhost:3000"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:3000"
fi

echo "✅ Services are live! Press Ctrl+C to terminate all servers."
wait

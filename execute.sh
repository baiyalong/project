#!/bin/bash

# Function to kill child processes on exit
trap 'kill $(jobs -p)' SIGINT SIGTERM EXIT

echo "🚀 Starting Heritage Project..."

# 1. Activate Virtual Environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
else
    echo "⚠️  Warning: Virtual environment not found. Using system python."
fi

# 2. Check Redis match
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  redis-cli not found, cannot verify Redis status."
else
    if ! redis-cli ping &> /dev/null; then
        echo "❌ Redis is NOT running. Please run './deploy.sh' first."
        exit 1
    fi
fi

# 3. Start Crawler Worker
echo "🕷️  Starting Crawler Worker..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python heritage_pipeline/run_worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo "   Worker started with PID: $WORKER_PID (Logs: worker.log)"

# 4. Start Django Server
echo "🌐 Starting Web Server..."
cd heritage_display
python manage.py runserver 0.0.0.0:8000

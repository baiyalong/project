#!/bin/bash

# Ensure we are in the project root or heritage_insights dir
# Correctly set environment variables for local execution connecting to Docker containers

export DATABASE_URL="postgresql://heritage_user:heritage_password@localhost:5432/heritage"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8002"  # Mapped port in docker-compose
export OLLAMA_BASE_URL="http://localhost:11434"

echo "Starting Heritage Insights..."
echo "Ensure you are using Python 3.10 or 3.11 for best compatibility."

# Use the virtual environment python if available, otherwise system python
if [ -f ".venv/bin/streamlit" ]; then
    .venv/bin/streamlit run heritage_insights/app.py --server.port 8501
else
    echo "Streamlit not found in .venv. Attempting system streamlit..."
    streamlit run heritage_insights/app.py --server.port 8501
fi

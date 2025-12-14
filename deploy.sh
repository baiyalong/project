#!/bin/bash
set -e

# Detect container runtime
if command -v podman-compose &> /dev/null; then
    CMD="podman-compose"
    RUNTIME="podman"
elif command -v docker-compose &> /dev/null; then
    CMD="docker-compose"
    RUNTIME="docker"
else
    echo "Error: Neither podman-compose nor docker-compose found."
    exit 1
fi

echo "🚀 Starting services using $CMD..."
$CMD up -d

echo "⏳ Waiting for Ollama service to be ready..."
# Loop until Ollama API is responsive
MAX_RETRIES=30
for ((i=1;i<=MAX_RETRIES;i++)); do
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   [$i/$MAX_RETRIES] Waiting for Ollama..."
    sleep 5
done

MODEL="llama3.2"
echo "⬇️  Pulling model: $MODEL (This may take a while)..."

# Exec into container to pull model
# We use the container name 'heritage_ollama' defined in docker-compose.yml
if [ "$RUNTIME" == "podman" ]; then
    podman exec heritage_ollama ollama pull $MODEL
else
    docker exec heritage_ollama ollama pull $MODEL
fi

echo "🎉 Deployment Complete!"
echo "   App is ready at: http://localhost:8501 (Run 'streamlit run app.py' in heritage_insights/ if running locally)"

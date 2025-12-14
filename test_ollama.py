
from heritage_insights.llm import OllamaLLM
from heritage_insights.config import settings
import sys

print(f"Testing Ollama connection to {settings.OLLAMA_BASE_URL} model {settings.OLLAMA_MODEL}...")
try:
    llm = OllamaLLM()
    print("Generating response...")
    # Test non-streaming
    resp = llm.generate("Hello, are you there?")
    print(f"Response: {resp}")
    
    print("-" * 20)
    print("Testing streaming...")
    # Test streaming
    for chunk in llm.stream_generate("Count to 3"):
        print(chunk, end="", flush=True)
    print("\nDone.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

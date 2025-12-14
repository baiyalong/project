"""Lightweight LLM adapter interfaces for heritage_insights.

Provides an abstract `BaseLLM`, `MockLLM`, and `OllamaLLM`.
"""
from typing import Dict, Any, Optional
import requests
import json
import os

class BaseLLM:
    """Abstract LLM interface.

    Implementations should provide `generate(prompt, **kwargs)` returning a string.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError()


class MockLLM(BaseLLM):
    """A deterministic mock LLM used for development and tests."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        context_docs = kwargs.get('context_docs') or []
        sources = []
        for d in context_docs[:5]:
            meta = d.get('metadata') or {}
            if isinstance(meta, dict) and meta.get('source'):
                sources.append(str(meta.get('source')))
            else:
                sources.append(str(d.get('id')))

        sources_part = ', '.join(sources) if sources else 'no sources'
        return f"MOCK_ANSWER based on: {sources_part}\n---\n{prompt[:100]}"


class OllamaLLM(BaseLLM):
    """Adapter for running LLMs via Ollama."""

    def __init__(self, model: str = "llama3.2", base_url: Optional[str] = None):
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Ollama API."""
        url = f"{self.base_url}/api/generate"
        
        # System prompt instructions can be embedded here or passed in prompt
        # We'll assume the prompt passed in is the full prompt
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error calling Ollama: {e}"
    
    def stream_generate(self, prompt: str, **kwargs: Any):
        """Generator for streaming responses."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.1
            }
        }
        
        try:
            with requests.post(url, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        body = json.loads(line)
                        token = body.get("response", "")
                        yield token
                        if body.get("done", False):
                            break
        except Exception as e:
            yield f"Error calling Ollama: {e}"

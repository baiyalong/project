"""Lightweight LLM adapter interfaces for heritage_insights.

Provides an abstract `BaseLLM` and a `MockLLM` for local development/testing
when no real LLM is available.
"""
from typing import Dict, Any


class BaseLLM:
    """Abstract LLM interface.

    Implementations should provide `generate(prompt, **kwargs)` returning a string.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError()


class MockLLM(BaseLLM):
    """A deterministic mock LLM used for development and tests.

    It echoes the user query and lists provided context snippet titles.
    Expected `kwargs`:
      - `context_docs`: a list of dicts with keys `id`, `text`, `metadata`
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        # Try to extract useful info from kwargs to make responses deterministic
        context_docs = kwargs.get('context_docs') or []
        sources = []
        for d in context_docs[:5]:
            meta = d.get('metadata') or {}
            if isinstance(meta, dict) and meta.get('source'):
                sources.append(str(meta.get('source')))
            else:
                sources.append(d.get('id'))

        sources_part = ', '.join(sources) if sources else 'no sources'
        return f"MOCK_ANSWER based on: {sources_part}\n---\n{prompt[:1000]}"

"""Retrieval-Augmented Generation (RAG) pipeline implementation.

This module implements `RAGPipeline` which coordinates embedding the query,
retrieving top documents from the `VectorStore`, and calling a pluggable LLM
to synthesize an answer.
"""
from typing import List, Dict, Any, Optional

from .services import EmbeddingService, VectorStore
from .llm import BaseLLM


class RAGPipeline:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore, llm: BaseLLM):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm = llm

    def _build_prompt(self, query: str, docs: List[Dict[str, Any]]) -> str:
        # Build a concise prompt that includes the top documents and the user query.
        parts = ["You are an assistant that answers questions using the supplied documents."]
        parts.append("=== Documents ===")
        for i, d in enumerate(docs, start=1):
            title = d.get('metadata', {}).get('source') or d.get('id')
            body = (d.get('documents') or d.get('document') or d.get('text') or '')
            # Keep a short preview to avoid overly large prompts
            preview = body[:200].replace('\n', ' ')
            parts.append(f"[{i}] {title}: {preview}")

        parts.append("=== End Documents ===")
        parts.append(f"Question: {query}")
        parts.append("Answer concisely and cite sources.")
        return "\n".join(parts)

    def answer(self, query: str, k: int = 3, return_docs: bool = False) -> Dict[str, Any]:
        # 1. embed query
        q_emb = self.embedding_service.embed_query(query)

        # 2. retrieve from vector store
        raw = self.vector_store.query(q_emb, n_results=k)

        # Chroma's query format: dict with keys like 'ids', 'documents', 'metadatas', 'distances'
        docs = []
        ids = raw.get('ids', [[]])[0] if isinstance(raw.get('ids'), list) else raw.get('ids')
        documents = raw.get('documents', [[]])[0] if isinstance(raw.get('documents'), list) else raw.get('documents')
        metadatas = raw.get('metadatas', [[]])[0] if isinstance(raw.get('metadatas'), list) else raw.get('metadatas')
        distances = raw.get('distances', [[]])[0] if isinstance(raw.get('distances'), list) else raw.get('distances')

        for i in range(len(ids or [])):
            docs.append({
                'id': ids[i],
                'text': documents[i] if documents else '',
                'metadata': metadatas[i] if metadatas else {},
                'distance': distances[i] if distances else None,
            })

        # 3. build prompt
        prompt = self._build_prompt(query, docs)

        # 4. call LLM
        answer = self.llm.generate(prompt, context_docs=docs)

        out = {'answer': answer, 'docs': docs}
        if return_docs:
            return out
        return {'answer': answer}

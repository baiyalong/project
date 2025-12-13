"""
Embedding and VectorStore helpers for heritage_insights.

This is a minimal implementation intended as a starting point.
"""
from typing import List, Dict, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None

try:
    import chromadb
    from chromadb.config import Settings
except Exception:  # pragma: no cover
    chromadb = None


class EmbeddingService:
    """Wraps a sentence-transformers model to produce embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required. Install with pip install sentence-transformers")
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return a list of vector embeddings for the input texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        # ensure python lists
        return [emb.tolist() if hasattr(emb, 'tolist') else list(np.array(emb)) for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class VectorStore:
    """A small wrapper around ChromaDB for add/query operations."""

    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "heritage_knowledge_base"):
        if chromadb is None:
            raise ImportError("chromadb is required. Install with pip install chromadb")
        # For local simple usage, use default settings. In production supply Settings(...)
        self.client = chromadb.Client(Settings()) if hasattr(chromadb, 'Client') else chromadb.Client()
        # create or get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)

    def add_documents(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None):
        """Add documents to the collection. All lists must be same length."""
        if metadatas is None:
            metadatas = [{} for _ in ids]
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def query(self, query_embedding: List[float], n_results: int = 3):
        res = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
        # chroma returns dict with ids, distances, documents, metadatas
        return res

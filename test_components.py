
from heritage_insights.services import EmbeddingService, VectorStore
from heritage_insights.config import settings
import time
import sys

def test():
    print("Test 1: Config Check")
    print(f"Values: CHROMA_HOST={settings.CHROMA_HOST}, CHROMA_PORT={settings.CHROMA_PORT}, DB_DIR={settings.CHROMA_DB_DIR}")
    
    print("\nTest 2: EmbeddingService Init")
    start = time.time()
    try:
        emb = EmbeddingService()
        print(f"EmbeddingService initialized in {time.time() - start:.2f}s")
        vec = emb.embed_query("test")
        print(f"Embedding check passed (len={len(vec)})")
    except Exception as e:
        print(f"Embedding check failed: {e}")
        return

    print("\nTest 3: VectorStore Init")
    start = time.time()
    try:
        vs = VectorStore()
        print(f"VectorStore initialized in {time.time() - start:.2f}s")
        
        # Test query
        res = vs.query(vec, n_results=1)
        print(f"Query result keys: {res.keys()}")
    except Exception as e:
        print(f"VectorStore check failed: {e}")
        return

    print("\nAll checks passed.")

if __name__ == "__main__":
    test()

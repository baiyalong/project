"""Basic unit tests for the RAG pipeline using mocks.

These tests avoid real dependencies (Chroma, heavy models) by using
small mock classes to simulate embeddings, vector retrieval and LLM.
"""
from heritage_insights.pipeline import RAGPipeline


class MockEmbedding:
    def embed_query(self, text):
        # return a fixed-dimension dummy vector
        return [0.0] * 384


class MockVectorStore:
    def __init__(self):
        # prepare deterministic mock results
        self._docs = [
            {
                'id': 'doc1',
                'text': 'This is about the Great Wall. It is long.',
                'metadata': {'source': 'doc1.txt'},
            },
            {
                'id': 'doc2',
                'text': 'This doc mentions China and history.',
                'metadata': {'source': 'doc2.txt'},
            },
        ]

    def query(self, query_embeddings, n_results=3):
        # Return Chroma-like structure
        docs = [d['text'] for d in self._docs][:n_results]
        ids = [d['id'] for d in self._docs][:n_results]
        metadatas = [d['metadata'] for d in self._docs][:n_results]
        distances = [0.1, 0.2][:n_results]
        return {'ids': [ids], 'documents': [docs], 'metadatas': [metadatas], 'distances': [distances]}


class MockLLM:
    def generate(self, prompt: str, **kwargs):
        # return a short deterministic answer
        return f"MOCK_RESPONSE for prompt length {len(prompt)}"


def test_pipeline_answer_returns_answer_and_docs():
    emb = MockEmbedding()
    vs = MockVectorStore()
    llm = MockLLM()
    from heritage_insights.pipeline import RAGPipeline

    pipe = RAGPipeline(emb, vs, llm)
    out = pipe.answer('What is the Great Wall?', k=2, return_docs=True)
    assert 'answer' in out
    assert 'docs' in out
    assert len(out['docs']) == 2
    assert out['answer'].startswith('MOCK_RESPONSE')

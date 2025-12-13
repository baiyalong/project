"""
Direct DB indexer: read rows from `heritage_site` table and index into Chroma via `VectorStore`.

Usage:
    from heritage_insights.db_index import index_from_db
    index_from_db(database_url="postgresql://user:pass@host:port/dbname")

Environment:
    Pass `DATABASE_URL` or provide `database_url` argument.
"""
from typing import List, Optional, Dict
import math
import os
from sqlalchemy import create_engine, text

from .services import EmbeddingService, VectorStore


def fetch_sites(db_url: str):
    """Yield site rows from `heritage_site` table as dicts.

    Fields returned: id, name, description_en, description_zh, content, metadata
    """
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # fetch primary key and text fields
        q = text(
            "SELECT id, name, description_en, description_zh, content, metadata FROM heritage_site"
        )
        result = conn.execute(q)
        for row in result:
            yield {
                'id': str(row['id']),
                'name': row['name'] if row['name'] is not None else '',
                'description_en': row['description_en'] or '',
                'description_zh': row['description_zh'] or '',
                'content': row['content'] or '',
                'metadata': row['metadata'] or {},
            }


def _build_doc_text(site: Dict) -> str:
    # Choose the richest text to index: prefer content, then english desc, then chinese desc
    parts = []
    if site.get('name'):
        parts.append(site['name'])
    if site.get('content'):
        parts.append(site['content'])
    if site.get('description_en'):
        parts.append(site['description_en'])
    if site.get('description_zh'):
        parts.append(site['description_zh'])
    return "\n\n".join(parts).strip()


def index_from_db(database_url: Optional[str] = None, batch_size: int = 64, collection_name: str = "heritage_knowledge_base"):
    """Index all rows from DB into vector store.

    Args:
        database_url: SQLAlchemy DB URL. If not provided, will read `DATABASE_URL` env var.
        batch_size: how many documents to embed per batch.
    """
    db_url = database_url or os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError('database_url is required or set DATABASE_URL env var')

    emb = EmbeddingService()
    vs = VectorStore(collection_name=collection_name)

    docs = list(fetch_sites(db_url))
    total = len(docs)
    if total == 0:
        print('No documents found in heritage_site')
        return

    print(f'Indexing {total} documents (batch_size={batch_size})...')

    for i in range(0, total, batch_size):
        batch = docs[i : i + batch_size]
        ids = [d['id'] for d in batch]
        texts = [_build_doc_text(d) for d in batch]
        metadatas = [d.get('metadata', {}) for d in batch]

        embeddings = emb.embed_documents(texts)
        vs.add_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
        print(f'Indexed batch {i // batch_size + 1}/{math.ceil(total / batch_size)}')

    print('Indexing completed.')

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

from services import EmbeddingService, VectorStore
from config import settings


def fetch_sites(db_url: str):
    """Yield site rows from `heritage_site` table as dicts.

    Fields returned: id, name, country, category, description_en, description_zh, content, metadata
    """
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # fetch primary key and text fields
        q = text(
            "SELECT id, name, country, category, description_en, description_zh, content, metadata FROM heritage_site"
        )
        result = conn.execute(q).mappings()
        for row in result:
            yield {
                'id': str(row['id']),
                'name': row['name'] if row['name'] is not None else '',
                'country': row['country'] or '',
                'category': row['category'] or '',
                'description_en': row['description_en'] or '',
                'description_zh': row['description_zh'] or '',
                'content': row['content'] or '',
                'metadata': row['metadata'] or {},
            }


import json

def _build_doc_text(site: Dict) -> str:
    # Serialize metadata to string if it exists
    meta_str = ""
    if site.get('metadata'):
        try:
             # Ensure dict, then dump to string
             meta_val = site['metadata']
             if isinstance(meta_val, str):
                 meta_val = json.loads(meta_val)
             meta_str = json.dumps(meta_val, ensure_ascii=False)
        except:
             meta_str = str(site.get('metadata', ''))

    # Key-Value format helps the embedding model understand the structure
    parts = [
        f"Name: {site.get('name', '')}",
        f"Country: {site.get('country', '')}",
        f"Category: {site.get('category', '')}",
        f"Description (EN): {site.get('description_en', '')}",
        f"Description (ZH): {site.get('description_zh', '')}",
        f"Content: {site.get('content', '')}",
        f"Metadata: {meta_str}"
    ]
    return "\n".join(part for part in parts if part).strip()


def index_from_db(database_url: Optional[str] = None, batch_size: int = 64, collection_name: str = settings.COLLECTION_NAME):
    """Index all rows from DB into vector store.

    Args:
        database_url: SQLAlchemy DB URL. If not provided, will read `DATABASE_URL` env var.
        batch_size: how many documents to embed per batch.
    """
    db_url = database_url or settings.DATABASE_URL
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
        
        # Sanitize metadata: ChromaDB does not support None values
        metadatas = []
        for d in batch:
            raw_meta = d.get('metadata', {})
            if not isinstance(raw_meta, dict):
                raw_meta = {}
            # Filter out None values and ensure types are supported
            clean_meta = {k: v for k, v in raw_meta.items() if v is not None}
            # Ensure 'source' exists if possible, or fallback
            if 'source' not in clean_meta:
                 clean_meta['source'] = d.get('name', str(d.get('id', '')))
            metadatas.append(clean_meta)

        embeddings = emb.embed_documents(texts)
        vs.add_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
        print(f'Indexed batch {i // batch_size + 1}/{math.ceil(total / batch_size)}')

    print('Indexing completed.')

"""
Simple CLI to index plain text files and run a query against the local Chroma collection.
"""
import argparse
import os
from pathlib import Path
from typing import List

from heritage_insights.services import EmbeddingService, VectorStore


def load_text_files(data_dir: str) -> List[dict]:
    docs = []
    p = Path(data_dir)
    for f in sorted(p.glob('**/*.txt')):
        text = f.read_text(encoding='utf-8')
        docs.append({'id': str(f), 'text': text, 'meta': {'source': str(f)}})
    return docs


def cmd_index(args):
    docs = load_text_files(args.data_dir)
    ids = [d['id'] for d in docs]
    texts = [d['text'] for d in docs]
    metadatas = [d['meta'] for d in docs]

    emb = EmbeddingService()
    embeddings = emb.embed_documents(texts)

    vs = VectorStore()
    vs.add_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
    print(f"Indexed {len(ids)} documents into collection.")


def cmd_query(args):
    emb = EmbeddingService()
    vs = VectorStore()
    q_emb = emb.embed_query(args.q)
    res = vs.query(q_emb, n_results=args.k)
    print(res)


def main():
    parser = argparse.ArgumentParser(description="heritage_insights simple CLI")
    sub = parser.add_subparsers(dest='cmd')

    p_index = sub.add_parser('index')
    p_index.add_argument('--data-dir', required=True)

    p_index_db = sub.add_parser('index-db')
    p_index_db.add_argument('--database-url', required=False, help='SQLAlchemy database URL. If omitted will read DATABASE_URL env var.')
    p_index_db.add_argument('--batch-size', required=False, type=int, default=64)

    p_query = sub.add_parser('query')
    p_query.add_argument('--q', required=True)
    p_query.add_argument('--k', type=int, default=3)

    args = parser.parse_args()
    if args.cmd == 'index':
        cmd_index(args)
    elif args.cmd == 'index-db':
        # index from database directly
        from heritage_insights.db_index import index_from_db
        index_from_db(database_url=getattr(args, 'database_url', None), batch_size=getattr(args, 'batch_size', 64))
    elif args.cmd == 'query':
        cmd_query(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

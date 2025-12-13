# heritage_insights

This package implements a minimal skeleton for the `heritage_insights` module described in the project docs.

Goals:
- Provide an Embedding service using `sentence-transformers`.
- Provide a simple `chromadb`-backed vector store wrapper.
- Include a small CLI example to index local text files and run a query.

Quick start

1. Create/activate your virtualenv (project uses `.venv`).
2. Install dependencies:

```bash
/your/venv/bin/python -m pip install -r heritage_insights/requirements.txt
```

3. Index a folder of text files:

```bash
/your/venv/bin/python heritage_insights/cli.py index --data-dir ./samples
```

4. Query:

```bash
/your/venv/bin/python heritage_insights/cli.py query --q "What is the Great Wall?" --k 3
```

Notes

- This is a starting point; production deployments should secure the vector DB, choose appropriate embedding/model resources, and integrate with the main app's data store.

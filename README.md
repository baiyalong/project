# Heritage — World Heritage Display & Processing Platform

NOTICE: For research and learning only — NOT FOR COMMERCIAL USE.

Overview
This repository is a multi-module project for scraping, processing, and displaying world heritage site information. It is intended for academic, research, and educational use only. Do not use for commercial or for‑profit purposes. Users must verify licenses and copyrights for any sourced data.

Main modules
- heritage_display — Django app and admin for displaying and managing data.
- heritage_pipeline — Scrapy spiders and pipelines for data collection.
- heritage_insights — Data processing, indexing, CLI and LLM utilities.
- doc/ — design and requirements documents.
- docker-compose.yml and init.sql at repository root for service orchestration and DB initialization.

Quick Start (local)
Prerequisites: Python 3.8+, pip, virtualenv (recommended). Docker & Docker Compose optional.

Example setup:
python3 -m venv .venv
source .venv/bin/activate
pip install -r heritage_display/requirements.txt
pip install -r heritage_pipeline/requirements.txt
pip install -r heritage_insights/requirements.txt

Run Django (development):
cd heritage_display
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver
# Visit http://127.0.0.1:8000/

Run Scrapy spider:
cd heritage_pipeline
scrapy crawl heritage_spider
# Export example: scrapy crawl heritage_spider -o output.json

Run insights CLI/pipeline:
cd heritage_insights
python -m cli
# or python heritage_insights/cli.py

Docker (optional)
docker-compose up --build

Configuration
- Django settings: heritage_display/heritage_display/settings.py
- Use .env or docker-compose to provide SECRET_KEY, DB credentials, etc.

Testing
- Django tests:
cd heritage_display
python manage.py test

- Other tests (may use pytest):
pytest heritage_insights/tests

Contributing
- Read docs in doc/ (SRS, LLD, HLD).
- Run tests and linters before submitting PRs.
- All contributions must respect the "research and learning only — not for commercial use" restriction.

Legal & Usage Notice
This project and its data/examples are provided for research, learning and educational purposes only. Do NOT use for commercial purposes or for-profit products. Verify license and copyright of any external data before use.

Commands (git)

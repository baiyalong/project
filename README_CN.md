# 项目名：Heritage（文化遗产展示与处理平台）

注意：仅用于学习与研究 — 严禁用于商业用途。

简介
本仓库为一个多模块项目，包含用于抓取、处理与展示世界文化遗产信息的组件。用途仅限学术、研究与教育，禁止用于商业或营利性用途。使用者需自行核实所用数据的版权与许可。

主要模块
- heritage_display — Django 网站与管理后台，用于展示与管理数据。
- heritage_pipeline — Scrapy 爬虫与数据采集管道。
- heritage_insights — 数据处理、索引、CLI 与 LLM 辅助功能。
- doc/ — 设计与需求文档集合。
- 根目录包含 docker-compose.yml 与 init.sql（数据库初始化脚本）。

快速开始（本地）
先决条件：Python 3.8+、pip、virtualenv（推荐）。Docker 与 Docker Compose 可选。

示例安装：
python3 -m venv .venv
source .venv/bin/activate
pip install -r heritage_display/requirements.txt
pip install -r heritage_pipeline/requirements.txt
pip install -r heritage_insights/requirements.txt

运行 Django（开发）：
cd heritage_display
python manage.py migrate
python manage.py createsuperuser  # 如需管理员
python manage.py runserver
# 访问 http://127.0.0.1:8000/

运行爬虫：
cd heritage_pipeline
scrapy crawl heritage_spider
# 导出示例：scrapy crawl heritage_spider -o output.json

运行 insights CLI / 管道：
cd heritage_insights
python -m cli
# 或 python heritage_insights/cli.py

Docker（可选）
docker-compose up --build

配置
- Django 配置位于 heritage_display/heritage_display/settings.py
- 建议使用 .env 或在 docker-compose 中注入环境变量（SECRET_KEY、数据库凭证等）。

测试
- Django 测试：
cd heritage_display
python manage.py test

- 其他单元测试（可能使用 pytest）：
pytest heritage_insights/tests

贡献
- 请先阅读 doc/ 中的设计文档（SRS、LLD、HLD 等）。
- 提交 PR 前请运行对应模块测试并确保格式化与静态检查通过。
- 注意：所有贡献须遵守“仅用于学习与研究，禁止商业用途”的约定。

法律与使用限制
本项目及其示例与工具仅供学习、研究与教育用途，严禁用于任何商业或盈利性用途。使用者需自行核实外部数据来源的版权与许可。

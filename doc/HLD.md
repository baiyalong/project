# 系统概要设计说明书 (High-Level Design)

## 1. 引言
### 1.1 目的
本文档描述了“世界遗产数据系统”的整体架构和技术方案，旨在为详细设计和开发提供指导。

### 1.2 范围
系统采用模块化设计，包含数据采集 (`heritage_pipeline`)、数据展示 (`heritage_display`) 和智能分析 (`heritage_insights`) 三个核心部分。

## 2. 系统架构 (System Architecture)

### 2.1 架构图 (Architecture Diagram)
```mermaid
graph TD
    User[User] --> |HTTP| Web[heritage_display (Django)]
    Web --> |Read/Write| DB[(PostgreSQL)]
    Web --> |Query| VectorDB[(Chroma)]
    Web --> |RPC/Internal| Insights[heritage_insights (Local LLM)]
    
    Crawler[heritage_pipeline (Crawler)] --> |Write| DB
    Crawler --> |Cache/Queue| Redis[(Redis)]
    
    Insights --> |Retrieve| VectorDB
    Insights --> |Generate| LLM[Local LLM]
```

### 2.2 模块划分
- **heritage_pipeline**: 基于 Python 的爬虫模块，负责从 UNESCO 等源站点定期抓取数据，处理后存入数据库。
- **heritage_display**: Web 应用服务端，负责响应用户请求，渲染页面或返回数据，处理查询逻辑。
- **heritage_insights**: AI 分析模块，负责将文本数据向量化，并构建 RAG 流程以回答用户问题。

## 3. 技术栈选型 (Technology Stack)

| 领域 | 技术选型 | 理由 |
| :--- | :--- | :--- |
| **编程语言** | Python 3.10+ | 生态丰富，适合爬虫、Web 和 AI 开发。 |
| **Web 框架** | Django | 开发效率高，社区支持强，自带 ORM。 |
| **数据库** | PostgreSQL 15+ | 关系型数据存储，支持 JSONB。 |
| **缓存/队列** | Redis | 爬虫去重队列，页面缓存。 |
| **爬虫框架** | Scrapy | 成熟、高性能的异步爬虫框架。 |
| **AI/LLM** | Local LLM | 用于生成自然语言回答，保障数据隐私。 |
| **向量工具** | Chroma | 专用的向量数据库，用于高效的相似度检索。 |

## 4. 关键数据流 (Data Flow)

### 4.1 数据采集流
1. 调度器触发爬虫任务。
2. 爬虫请求目标网页。
3. 解析器提取结构化数据（名称、国家、类型、描述、详细内容）。
4. 清洗器处理数据格式。
5. 存储器将数据写入 PostgreSQL `heritage_data` 表。

### 4.2 用户查询流
1. 用户在 Web 界面设定筛选条件（国家=中国）。
2. 后端使用 ORM 查询。
3. 数据库返回结果集。
4. Web 界面渲染列表展示。

### 4.3 AI 分析流
1. 用户输入问题。
2. `heritage_insights` 将问题转化为向量。
3. 在 Vector Store 中检索 Top-K 相关文本片段。
4. 拼接 Prompt (Context + Question) 提交给 LLM。
5. LLM 返回答案，后端展示给用户。

## 5. 部署架构 (Deployment Architecture)
- **容器化**: 所有服务通过 Docker 容器部署。
- **编排**: 使用 Docker Compose 进行单机编排或 K8s 集群部署。
- **数据持久化**: 数据库和 Redis 挂载外部卷 (Volume)。

### 5.1 本地开发环境 (Local Development)
项目中并在根目录提供了 `docker-compose.yml` 文件，推荐使用 **Podman** 进行容器管理。

**前置要求**:
- 安装 `podman`
- 安装 `podman-compose`

**启动服务**:
```bash
podman-compose up -d
```

**服务清单**:
| 服务 | 容器名 | 端口 | 默认凭证/说明 |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `heritage_postgres` | 5432 | User: `heritage_user` <br> Pass: `heritage_password` <br> DB: `heritage` |
| **Redis** | `heritage_redis` | 6379 | 无密码 |
| **Chroma** | `heritage_chroma` | 8000 | 向量数据库 |

**停止服务**:
```bash
podman-compose down
```

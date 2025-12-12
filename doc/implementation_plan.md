# 软件工程文档生成计划 (Implementation Plan)

## 目标 (Goal)
为“世界遗产数据系统 (World Heritage Data System)”生成一套符合专业软件工程标准的文档集合。
涵盖三个子系统：
1.  `heritage_pipeline` (数据采集)
2.  `heritage_display` (Web 展示)
3.  `heritage_insights` (智能分析)

## 拟定生成的文档列表 (Proposed Documents)

### 1. 用户需求说明书 (User Requirements Specification - URS)
**面向对象：** 客户、产品经理。
**核心内容：** 业务目标、用户角色、业务流程、用户故事。

### 2. 软件需求规格说明书 (Software Requirements Specification - SRS)
**面向对象：** 开发人员、测试人员。
**核心内容：** 功能需求（采集、展示、分析）、非功能需求（性能、可靠性、安全）、接口需求。

### 3. 系统概要设计说明书 (High-Level Design - HLD)
**面向对象：** 架构师。
**核心内容：** 系统架构图、技术栈选型、模块划分、关键数据流。

### 4. 数据库设计说明书 (Database Design Document - DBDD)
**面向对象：** DBA、后端开发。
**核心内容：** ER 图、`heritage_data` 表定义、Redis 键设计、向量索引设计。

### 5. 系统详细设计说明书 (Low-Level Design - LLD)
**面向对象：** 开发人员。
**核心内容：** 类图/时序图、核心算法（爬虫调度、向量检索）、API 定义。
*特别补充：包含 AI 模块的 Embedding 策略和 Prompt 设计。*

### 6. 软件测试用例 (Test Cases)
**面向对象：** 测试人员。
**核心内容：** 测试项、步骤、预期结果（覆盖功能、数据、AI 效果）。

### 7. 部署与运维手册 (Deployment & Operations Manual)
**面向对象：** 运维人员 (DevOps)。
**目的：** 确保系统能跑起来，且能长期稳定运行。由于本项目包含后台任务（爬虫），此文档尤为重要。
**核心内容：**
*   **环境依赖**：Docker, Python, PostgreSQL, Redis 配置。
*   **部署步骤**：安装、初始化 DB、启动 Web 服务。
*   **任务调度**：如何配置 Crontab 或 Celery Beat 运行爬虫。
*   **故障排查**：常见日志查看与报错处理。

## 执行计划
我将按照 1-7 的顺序依次生成文档。

#!/usr/bin/env python
"""
Scrapy 爬虫调用工具
支持全量和单条爬取模式，并更新任务进度
"""
import sys
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_spider(task_id=None, url=None):
    """
    运行爬虫
    
    Args:
        task_id: CrawlTask 的 ID，用于更新进度
        url: 单条爬取的目标 URL（可选）
    """
    # 获取 Scrapy 项目设置
    settings = get_project_settings()
    
    # 配置参数
    spider_kwargs = {}
    if task_id:
        spider_kwargs['task_id'] = task_id
    if url:
        spider_kwargs['url'] = url
    
    # 创建爬虫进程
    process = CrawlerProcess(settings)
    
    # 启动爬虫
    process.crawl('heritage_spider', **spider_kwargs)
    process.start()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='运行世界遗产爬虫')
    parser.add_argument('--task-id', type=int, help='任务ID')
    parser.add_argument('--url', type=str, help='单条爬取的URL')
    
    args = parser.parse_args()
    
    run_spider(task_id=args.task_id, url=args.url)

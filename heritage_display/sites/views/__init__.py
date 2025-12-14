"""
Views package for heritage sites app

This package organizes views into focused modules:
- list_views: Heritage site listing and filtering
- detail_views: Individual site detail pages  
- crawler_views: Crawler control and monitoring
"""

# Import all views for backward compatibility
from .list_views import site_list
from .detail_views import site_detail
from .crawler_views import (
    start_full_crawl,
    start_single_crawl,
    crawl_status,
    get_active_full_crawl,
    stop_all_crawls,
)

__all__ = [
    'site_list',
    'site_detail',
    'start_full_crawl',
    'start_single_crawl',
    'crawl_status',
    'get_active_full_crawl',
    'stop_all_crawls',
]

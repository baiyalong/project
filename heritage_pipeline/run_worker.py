import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_worker():
    # Add project directory to sys.path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_dir)
    
    # Set settings module
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'heritage_pipeline.settings'
    
    settings = get_project_settings()
    
    # Enable Redis Scheduler explicitly in case it's not default
    settings.set('SCHEDULER', "scrapy_redis.scheduler.Scheduler")
    settings.set('DUPEFILTER_CLASS', "scrapy_redis.dupefilter.RFPDupeFilter")
    settings.set('SCHEDULER_PERSIST', True)
    
    # IMPORTANT: Keep worker alive waiting for new tasks
    settings.set('SCHEDULER_IDLE_BEFORE_CLOSE', 0) # 0 means wait forever
    
    process = CrawlerProcess(settings)
    process.crawl('heritage_spider')
    
    print("Starting Redis Worker... Waiting for tasks...")
    process.start()

if __name__ == "__main__":
    run_worker()

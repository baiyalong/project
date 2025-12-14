import re
import json
from itemadapter import ItemAdapter
from w3lib.html import remove_tags
from datetime import datetime, timedelta

class CleanPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for field in adapter.field_names():
            value = adapter.get(field)
            if isinstance(value, str) and field not in ['metadata']:
                # Remove HTML tags using w3lib
                clean_text = remove_tags(value)
                # Normalize whitespace
                clean_text = ' '.join(clean_text.split())
                adapter[field] = clean_text
                
        return item


class TaskStatusPipeline:
    """Updates crawl task status and progress in the database (Stateless)"""
    
    def __init__(self, postgres_uri):
        self.postgres_uri = postgres_uri
        self.engine = None
        self.Session = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            postgres_uri=crawler.settings.get('POSTGRES_URI', 'postgresql://heritage_user:heritage_password@localhost:5432/heritage')
        )

    def open_spider(self, spider):
        try:
            self.engine = create_engine(self.postgres_uri)
            self.Session = sessionmaker(bind=self.engine)
            spider.logger.info("TaskStatusPipeline: Connected to DB")
        except Exception as e:
            spider.logger.error(f"Failed to connect to DB: {e}")

    def close_spider(self, spider):
        if self.engine:
            self.engine.dispose()

    def process_item(self, item, spider):
        if not self.Session:
            return item

        # Get task_id from item metadata (injected by spider from Redis payload)
        metadata = item.get('metadata', {}) or {}
        task_id = metadata.get('task_id')
        task_type = metadata.get('task_type')
        
        if not task_id:
            # Maybe it's a legacy item or manual run? Skip stats update.
            return item

        session = self.Session()
        try:
            task = session.query(CrawlTaskModel).get(task_id)
            if task:
                # Update status to running if pending
                if task.status == 'pending':
                    task.status = 'running'
                
                # Increment progress
                task.processed_items += 1
                task.current_item = item.get('name', '')[:255]
                
                # For SINGLE task, we complete it immediately after one item
                if task_type == 'single':
                    task.status = 'completed'
                    task.completed_at = datetime.utcnow()
                    spider.logger.info(f"Completed single task {task_id}")

                session.commit()
        except Exception as e:
            spider.logger.error(f"Failed to update task progress: {e}")
        finally:
            session.close()
            
        return item


from sqlalchemy.orm import sessionmaker
from .models import HeritageSiteModel, CrawlTaskModel, Base
from sqlalchemy import create_engine

class PostgresPipeline:
    def __init__(self, postgres_uri):
        self.postgres_uri = postgres_uri
        self.engine = None
        self.Session = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            postgres_uri=crawler.settings.get('POSTGRES_URI', 'postgresql://heritage_user:heritage_password@localhost:5432/heritage')
        )

    def open_spider(self, spider):
        try:
            self.engine = create_engine(self.postgres_uri)
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            spider.logger.info("Connected to PostgreSQL via SQLAlchemy.")
        except Exception as e:
            spider.logger.error(f"Failed to connect to DB: {e}")

    def close_spider(self, spider):
        if self.engine:
            self.engine.dispose()

    def process_item(self, item, spider):
        if not self.Session:
            return item
        
        session = self.Session()
        try:
            # Check if exists
            site = session.query(HeritageSiteModel).filter_by(name=item.get('name')).first()
            
            if site:
                # Incremental crawling: only update if data changed or older than 30 days
                should_update = False
                
                # Check if content has changed
                if (site.description_en != item.get('description_en') or
                    site.description_zh != item.get('description_zh') or
                    site.content != item.get('content')):
                    should_update = True
                    spider.logger.info(f"Content changed for: {item.get('name')}")
                
                # Or if last update was more than 30 days ago
                if site.updated_at and (datetime.utcnow() - site.updated_at).days > 30:
                    should_update = True
                    spider.logger.info(f"Updating stale record (>30 days): {item.get('name')}")

                # Force update for manual single tasks
                task_type = item.get('metadata', {}).get('task_type')
                if task_type == 'single':
                    should_update = True
                    spider.logger.info(f"Force updating single task: {item.get('name')}")
                
                if should_update:
                    # Update
                    site.country = item.get('country')
                    site.description_en = item.get('description_en')
                    site.description_zh = item.get('description_zh')
                    site.content = item.get('content')
                    site.category = item.get('category')
                    site.metadata_ = item.get('metadata')
                    site.updated_at = datetime.utcnow() # Force update timestamp
                    spider.logger.info(f"Updated: {item.get('name')}")
                else:
                    spider.logger.debug(f"Skipped (no changes): {item.get('name')}")
            else:
                # Insert new record
                site = HeritageSiteModel(
                    name=item.get('name'),
                    country=item.get('country'),
                    description_en=item.get('description_en'),
                    description_zh=item.get('description_zh'),
                    content=item.get('content'),
                    category=item.get('category'),
                    metadata_=item.get('metadata')
                )
                session.add(site)
                spider.logger.info(f"Inserted new: {item.get('name')}")
                
            session.commit()
        except Exception as e:
            session.rollback()
            spider.logger.error(f"DB Error: {e}")
        finally:
            session.close()
            
        return item

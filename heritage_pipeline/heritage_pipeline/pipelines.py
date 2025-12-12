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

from sqlalchemy.orm import sessionmaker
from .models import HeritageSiteModel, Base
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
                
                if should_update:
                    # Update
                    site.country = item.get('country')
                    site.description_en = item.get('description_en')
                    site.description_zh = item.get('description_zh')
                    site.content = item.get('content')
                    site.category = item.get('category')
                    site.metadata_ = item.get('metadata')
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

import scrapy
from scrapy_redis.spiders import RedisSpider
import re
from heritage_pipeline.items import HeritageItem
import json
import html2text

class HeritageSpider(RedisSpider):
    name = "heritage_spider"
    allowed_domains = ["whc.unesco.org"]
    # Redis key to read tasks from
    redis_key = "heritage_spider:start_urls"

    def make_request_from_data(self, data):
        """
        Custom method to parse JSON task from Redis
        data: bytes
        """
        try:
            task_data = json.loads(data)
            url = task_data.get('url')
            task_id = task_data.get('task_id')
            task_type = task_data.get('task_type')
            
            if url:
                self.logger.info(f"Received task {task_id} ({task_type}) for {url}")
                # Pass task info in meta so pipelines can use it
                meta = {
                    'playwright': True,
                    'task_id': task_id,
                    'task_type': task_type
                }
                # Route to correct callback based on task type
                callback = self.parse_detail_auto
                if task_type == 'full':
                    callback = self.parse
                
                # IMPORTANT: Set dont_filter=True to ensure user-triggered updates always run
                return scrapy.Request(url, callback=callback, meta=meta, dont_filter=True)
            else:
                self.logger.error("Received task without URL")
                return None
        except Exception as e:
            self.logger.error(f"Failed to process task data: {e}")
            return None

    def parse(self, response):
        """
        Parse the main list page.
        Extract links to detail pages and pass 'category' via metadata.
        """
        # ... (rest is same logic but we need to ensure response is handled correctly)
        
        # Count total items first
        sites = response.xpath('//div[@class="list_site"]/ul/li')
        total_count = len(sites)
        task_id = response.meta.get('task_id')
        self.logger.info(f"Found {total_count} sites in the list for task {task_id}")
        self.update_total_items(total_count, task_id)

        # Iterate over all list items in the main list containers
        for li in sites:
            url = li.xpath('a/@href').get()
            if not url:
                continue
                
            # Extract category from class attribute (e.g., "cultural", "natural", "mixed")
            classes = li.xpath('@class').get('').lower().split()
            category = "Cultural" # Default
            if 'natural' in classes or 'natural_danger' in classes:
                category = "Natural"
            elif 'mixed' in classes or 'mixed_danger' in classes:
                category = "Mixed"
            elif 'cultural' in classes or 'cultural_danger' in classes:
                category = "Cultural"
            
            # Prepare meta, propagating existing meta (task_id, etc)
            meta = response.meta.copy() if response.meta else {}
            meta['playwright'] = True
            
            yield response.follow(url, callback=self.parse_detail, cb_kwargs={'category': category}, meta=meta)

    def update_total_items(self, count, task_id):
        """Update total_items in database for progress calculation"""
        if not task_id:
            return
            
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from heritage_pipeline.models import CrawlTaskModel
        
        db_uri = self.settings.get('POSTGRES_URI', 'postgresql://heritage_user:heritage_password@localhost:5432/heritage')
        try:
            engine = create_engine(db_uri)
            Session = sessionmaker(bind=engine)
            session = Session()
            task = session.query(CrawlTaskModel).get(task_id)
            if task:
                task.total_items = count
                session.commit()
                self.logger.info(f"Updated total_items to {count} for task {task_id}")
            session.close()
            engine.dispose()
        except Exception as e:
            self.logger.error(f"Failed to update total_items: {e}")

    def parse_detail(self, response, category):
        item = HeritageItem()
        
        # Initialize html2text converter with custom settings
        h = html2text.HTML2Text()
        h.body_width = 0  # Disable automatic line wrapping
        h.ignore_images = True  # Ignore images
        h.ignore_links = True  # Ignore links
        
        # 1. Name
        item['name'] = response.xpath('//h1/text()').get(default='').strip()
        
        # 2. Country
        # Found as: <a href="/en/statesparties/af" class="d-block"><strong>Afghanistan</strong></a>
        # OR sometimes just text.
        item['country'] = response.xpath('//a[contains(@href, "/statesparties/")]/strong/text()').get()
        if not item['country']:
            item['country'] = response.xpath('//a[contains(@href, "/statesparties/")]/text()').get()
        if item['country']:
            item['country'] = item['country'].strip()

        # 3. Description (English)
        # Extract HTML content and convert to Markdown using html2text
        desc_en_html = response.xpath('''
            //*[@id="contentdes_en"]/*[
                not(self::p[
                    contains(., "source: UNESCO/CPE") or 
                    contains(., "CC-BY-SA IGO 3.0")
                ])
            ] | 
            //*[@id="contentdes_en"]
        ''').getall()
        
        desc_en_html_str = "".join(desc_en_html).strip()
        item['description_en'] = h.handle(desc_en_html_str).strip() if desc_en_html_str else ""
        
        # 4. Description (Chinese)
        # Extract HTML content and convert to Markdown using html2text
        desc_zh_html = response.xpath('''
            //*[@id="contentdes_zh"]/*[
                not(self::p[
                    contains(., "source: UNESCO/CPE") or 
                    contains(., "CC-BY-SA IGO 3.0")
                ])
            ] | 
            //*[@id="contentdes_zh"]
        ''').getall()
        
        desc_zh_html_str = "".join(desc_zh_html).strip()
        item['description_zh'] = h.handle(desc_zh_html_str).strip() if desc_zh_html_str else ""
        
        # 5. Content (Detailed content from the page)
        # Extract HTML content and convert to Markdown using html2text
        content_html = response.xpath('//*[@id="content"]/div/div[3]/div/div[1]/div[3]').getall()
        content_html_str = "".join(content_html).strip()
        item['content'] = h.handle(content_html_str).strip() if content_html_str else ""
        
        # 6. Category
        item['category'] = category
        
        # 7. Metadata (URL)
        item['metadata'] = {
            'url': response.url,
            'task_id': response.meta.get('task_id'),
            'task_type': response.meta.get('task_type')
        }

        yield item

    def parse_detail_auto(self, response):
        """
        自动检测类别的详情页解析方法（用于单URL模式）
        """
        # 尝试从页面中提取类别信息
        # 通常在页面的某个位置会标注类别
        category = "Cultural"  # 默认值
        
        # 尝试从页面元素中提取类别
        category_text = response.xpath('//div[contains(@class, "category")]//text()').get()
        if category_text:
            category_lower = category_text.lower()
            if 'natural' in category_lower:
                category = "Natural"
            elif 'mixed' in category_lower:
                category = "Mixed"
        
        # 调用原有的详情页解析逻辑
        yield from self.parse_detail(response, category)

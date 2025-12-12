import scrapy
import re
from heritage_pipeline.items import HeritageItem
import json

class HeritageSpider(scrapy.Spider):
    name = "heritage"
    allowed_domains = ["whc.unesco.org"]
    start_urls = ["https://whc.unesco.org/en/list/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, meta={'playwright': True})

    def parse(self, response):
        """
        Parse the main list page.
        Extract links to detail pages and pass 'category' via metadata.
        """
        # ... (rest is same logic but we need to ensure response is handled correctly)
        
        # Iterate over all list items in the main list containers
        for li in response.xpath('//div[@class="list_site"]/ul/li'):
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
            
            # Use Playwright for detail pages too? Maybe not needed if detail pages are less protected,
            # but safer to consistency.
            yield response.follow(url, callback=self.parse_detail, cb_kwargs={'category': category}, meta={'playwright': True})

    def parse_detail(self, response, category):
        item = HeritageItem()
        
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
        # Strategy: Select all text from descendants, BUT exclude the specific <p> tags that contain copyright info.
        # We look for <p> tags containing "UNESCO/CPE" or "CC-BY-SA IGO 3.0" and ignore them.
        # Implementation: Select children of container, filter out bad <p> tags, then get their descendant text.
        # XPath: *[not(self::p[contains(., "source: UNESCO/CPE") or contains(., "CC-BY-SA IGO 3.0")])]
        
        desc_en_nodes = response.xpath('''
            //*[@id="contentdes_en"]/*[
                not(self::p[
                    contains(., "source: UNESCO/CPE") or 
                    contains(., "CC-BY-SA IGO 3.0")
                ])
            ]//text() | 
            //*[@id="contentdes_en"]/text()
        ''').getall()
        
        # Clean and join
        clean_desc_en = [d.strip() for d in desc_en_nodes if d.strip()]
        item['description_en'] = "\n\n".join(clean_desc_en)
        
        # 4. Description (Chinese)
        desc_zh_nodes = response.xpath('''
            //*[@id="contentdes_zh"]/*[
                not(self::p[
                    contains(., "source: UNESCO/CPE") or 
                    contains(., "CC-BY-SA IGO 3.0")
                ])
            ]//text() | 
            //*[@id="contentdes_zh"]/text()
        ''').getall()

        clean_desc_zh = [d.strip() for d in desc_zh_nodes if d.strip()]
        item['description_zh'] = "\n\n".join(clean_desc_zh)
        
        # 5. Content (Detailed content from the page)
        # Extract from //*[@id="content"]/div/div[3]/div/div[1]/div[3]
        content_parts = response.xpath('//*[@id="content"]/div/div[3]/div/div[1]/div[3]//text()').getall()
        item['content'] = "\n\n".join([c.strip() for c in content_parts if c.strip()])




 

        # 6. Category
        item['category'] = category
        
        # 7. Metadata (URL)
        item['metadata'] = {'url': response.url}

        yield item

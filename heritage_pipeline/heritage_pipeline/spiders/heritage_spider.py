import scrapy
import re
from heritage_pipeline.items import HeritageItem
import json
import html2text

class HeritageSpider(scrapy.Spider):
    name = "heritage_spider"
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
        item['metadata'] = {'url': response.url}

        yield item

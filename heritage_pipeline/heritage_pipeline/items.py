import scrapy

class HeritageItem(scrapy.Item):
    name = scrapy.Field()
    country = scrapy.Field()
    description_en = scrapy.Field()
    description_zh = scrapy.Field()
    content = scrapy.Field()
    category = scrapy.Field()
    metadata = scrapy.Field()  # For extra info

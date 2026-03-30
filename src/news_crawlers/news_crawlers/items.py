import scrapy


class NewsArticleItem(scrapy.Item):
    """Item for storing scraped news articles"""
    title = scrapy.Field()
    author = scrapy.Field()
    date_text = scrapy.Field()  # Maps to published_date in database
    url = scrapy.Field()
    content = scrapy.Field()
    word_count = scrapy.Field()
    source = scrapy.Field()

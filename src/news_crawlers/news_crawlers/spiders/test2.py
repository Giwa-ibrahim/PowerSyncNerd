import scrapy
from datetime import datetime, timedelta
from urllib.parse import urljoin


class IcirNigeriaSpider(scrapy.Spider):
    """Scrapy spider for ICIR Nigeria Energy & Power news articles"""
    
    name = 'icir'
    allowed_domains = ['www.icirnigeria.org']
    start_urls = ['https://www.icirnigeria.org/category/business-and-economy/energy-and-power/']

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_urls)

    def parse_urls(self, response):
        articles = response.css('div.td-module-meta-info')[:6]
        for article in articles:
            yield scrapy.Request(
                url=article.css('h3 a::attr(href)').get(),
                callback=self.parse_articles,
                meta={
                    'title': article.css('h3 a::text').get(),
                    'author': article.css('div.td-editor-date span.td-post-author-name a::text').get(),
                    'date': article.css('div.td-editor-date time.entry-date::text').get(),
                }
            )

        # Next page crawler
        next_page = response.css('a[aria-label="next-page"]::attr(href)').get()
        if next_page:
            yield response.follow(url=next_page, callback=self.parse_urls)

    def parse_articles(self, response):
        pass
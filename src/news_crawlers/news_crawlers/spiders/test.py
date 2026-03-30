import scrapy
from datetime import datetime, timedelta
from news_crawlers.items import NewsArticleItem


class IcirNigeriaSpider(scrapy.Spider):
    """Scrapy spider for ICIR Nigeria Energy & Power news articles"""
    
    name = 'icir'
    allowed_domains = ['www.icirnigeria.org']
    start_urls = ['https://www.icirnigeria.org/category/business-and-economy/energy-and-power/']
    
    # Force sequential crawling to respect page limits
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 2,
    }

    def __init__(self, days_back=30, max_pages=5, *args, **kwargs):
        super(IcirNigeriaSpider, self).__init__(*args, **kwargs)
        self.days_back = int(days_back)
        self.max_pages = int(max_pages)
        self.cutoff_date = datetime.now() - timedelta(days=self.days_back)
        self.pages_crawled = 0
        self.logger.info(f"🔍 Scraping articles from last {self.days_back} days (since {self.cutoff_date.strftime('%B %d, %Y')})")
        self.logger.info(f"📄 Max pages to crawl: {self.max_pages}")

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_urls)

    def is_recent(self, date_text):
        """Check if article date is within days_back"""
        if not date_text:
            return True
        try:
            article_date = datetime.strptime(date_text.strip(), '%B %d, %Y')
            is_recent = article_date >= self.cutoff_date
            if not is_recent:
                self.logger.info(f"⏰ Skipping old article from {date_text}")
            return is_recent
        except Exception as e:
            self.logger.warning(f"⚠️ Could not parse date '{date_text}': {e}")
            return True

    def parse_urls(self, response):
        # Track page number
        self.pages_crawled += 1
        current_page = self.pages_crawled
        
        self.logger.info(f"📂 Page {current_page}/{self.max_pages}")
        
        # HARD STOP if reached max pages
        if current_page > self.max_pages:
            self.logger.info(f"🛑 Reached max pages limit ({self.max_pages}) - CLOSING SPIDER")
            raise scrapy.exceptions.CloseSpider(f'Reached max_pages limit: {self.max_pages}')
        
        # Get only first 6 articles (last 6 are not energy/power news)
        articles = response.css('div.td-module-meta-info')[:6]
        
        found_recent = False
        
        for article in articles:
            date = article.css('div.td-editor-date time.entry-date::text').get()
            
            # Skip if too old
            if not self.is_recent(date):
                continue
            
            found_recent = True
            title = article.css('h3 a::text').get()
            self.logger.info(f"✅ Scraping: {title[:60]}...")
            
            yield scrapy.Request(
                url=article.css('h3 a::attr(href)').get(),
                callback=self.parse_articles,
                meta={
                    'title': title,
                    'author': article.css('div.td-editor-date span.td-post-author-name a::text').get(),
                    'date': date,
                }
            )
        
        # HARD STOP if no recent articles found
        if not found_recent:
            self.logger.info(f"🛑 No recent articles on page {current_page} - CLOSING SPIDER")
            raise scrapy.exceptions.CloseSpider(f'No recent articles found on page {current_page}')

        # Next page crawler (only if haven't reached max pages)
        if current_page < self.max_pages:
            next_page = response.css('a[aria-label="next-page"]::attr(href)').get()
            if next_page:
                self.logger.info(f"➡️ Moving to page {current_page + 1}...")
                yield response.follow(next_page, callback=self.parse_urls)
        else:
            self.logger.info(f"🛑 Reached max pages ({self.max_pages}) - stopping pagination")

    def parse_articles(self, response):
        content = response.css('div.td-post-content p::text').getall()
        
        # Exclude the last p tag (author bio)
        if content:
            content = content[:-1]
        
        # Create and populate item
        item = NewsArticleItem()
        item['title'] = response.meta.get('title')
        item['author'] = response.meta.get('author')
        item['date_text'] = response.meta.get('date') 
        item['url'] = response.url
        item['content'] = '\n\n'.join([p.strip() for p in content if p.strip()])
        item['word_count'] = len(' '.join(content).split())
        item['source'] = 'ICIR Nigeria'
        
        yield item

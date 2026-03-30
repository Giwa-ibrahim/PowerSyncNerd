import scrapy
from datetime import datetime, timedelta
from urllib.parse import urljoin


class IcirnigeriaSp(scrapy.Spider):
    """Scrapy spider for ICIR Nigeria Energy & Power news articles"""
    
    name = 'icirnigeria'
    allowed_domains = ['www.icirnigeria.org']
    
    
    def __init__(self, days_back=7, max_pages=3, *args, **kwargs):
        super(IcirnigeriaSp, self).__init__(*args, **kwargs)
        self.days_back = int(days_back)
        self.max_pages = int(max_pages)
        self.cutoff_date = datetime.now() - timedelta(days=self.days_back)
        self.base_url = "https://www.icirnigeria.org"
        self.category_url = "https://www.icirnigeria.org/category/business-and-economy/energy-and-power/"
        
        # Generate start URLs for pagination
        self.start_urls = [self.category_url]
        for page_num in range(2, self.max_pages + 1):
            self.start_urls.append(f"{self.category_url}page/{page_num}/")
    
    def parse(self, response):
        """Parse category page and extract article URLs"""
        
        self.logger.info(f"📂 Parsing page: {response.url}")
        
        # Use the correct XPath: //*[@id="tdi_156"]
        article_container = response.css('#tdi_156')
        
        if article_container:
            self.logger.info("✅ Found container using CSS Selector: #tdi_156")
            
            # Find all article modules within the container
            # Each article is in a div with class containing 'td_module_wrap'
            article_modules = article_container.xpath('.//div[contains(@class, "td_module_wrap")]')
            self.logger.info(f"📰 Found {len(article_modules)} article modules in container")
        else:
            self.logger.warning("⚠️ Container not found with XPath //*[@id='tdi_156'], trying fallback...")
            # Fallback: try to find article modules directly
            article_modules = response.xpath('//div[contains(@class, "td_module_wrap")]')
            self.logger.info(f"📰 Found {len(article_modules)} article modules with fallback")
        
        if not article_modules:
            self.logger.error(f"❌ No article modules found on {response.url}")
            return
        
        for idx, module in enumerate(article_modules, 1):
            # Extract title and URL from h3.entry-title.td-module-title > a
            title_element = module.css('.h3.entry-title.td-module-title > a')
            
            if not title_element:
                # Try without specific class
                title_element = module.css('.entry-title.td-module-title > a')
            
            if title_element:
                article_url = title_element.xpath('@href').get()
                title = title_element.xpath('text()').get()
                
                if not article_url:
                    self.logger.warning(f"⚠️ Article {idx}: No URL found, skipping")
                    continue
                
                article_url = urljoin(self.base_url, article_url)
                title = title.strip() if title else "No title"
                
                # Extract date from td-editor-date div
                # Structure: div.td-editor-date > span.td-post-date > time
                date_text = module.xpath('.//div[@class="td-editor-date"]/span[@class="td-post-date"]/time/@datetime').get()
                
                if not date_text:
                    # Try alternative date selectors
                    date_text = module.xpath('.//time/@datetime').get()
                
                # Check if article is recent enough
                if date_text:
                    try:
                        # Handle different date formats
                        if 'T' in date_text:
                            article_date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                        else:
                            article_date = datetime.strptime(date_text, '%Y-%m-%d')
                        
                        if article_date < self.cutoff_date:
                            self.logger.info(f"⏰ Article {idx}: Skipping old article - {title[:40]}... ({article_date.date()})")
                            continue
                        else:
                            self.logger.info(f"✅ Article {idx}: Recent article - {title[:40]}... ({article_date.date()})")
                    except (ValueError, AttributeError) as e:
                        self.logger.debug(f"⚠️ Article {idx}: Could not parse date '{date_text}': {e}")
                        # If date parsing fails, scrape anyway
                
                # Follow the article URL to scrape full content
                self.logger.info(f"🔗 Article {idx}: Following URL - {article_url}")
                yield scrapy.Request(
                    url=article_url,
                    callback=self.parse_article,
                    meta={'article_url': article_url, 'title_preview': title}
                )
            else:
                self.logger.warning(f"⚠️ Article {idx}: No title element found, skipping")
    
    def parse_article(self, response):
        """Parse individual article page and extract data"""
        
        url = response.meta.get('article_url', response.url)
        self.logger.info(f"📄 Scraping article: {url}")
        
        # Extract title
        title = response.xpath('//h1[@class="entry-title"]/text()').get()
        if not title:
            title = response.xpath('//h1/text()').get()
        title = title.strip() if title else "No title found"
        
        # Extract date
        date_text = response.xpath('//time[@class="entry-date updated td-module-date"]/@datetime').get()
        if not date_text:
            date_text = response.xpath('//time/@datetime | //span[@class="td-post-date"]/time/@datetime').get()
        
        # Parse and format date
        published_date = None
        if date_text:
            try:
                published_date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                date_text = published_date.strftime('%B %d, %Y')
            except (ValueError, AttributeError):
                date_text = date_text
        
        # Extract author
        author = response.xpath('//div[@class="td-post-author-name"]/div/a/text() | //a[@rel="author"]/text()').get()
        if not author:
            author = response.xpath('//span[@class="author vcard"]/a/text()').get()
        author = author.strip() if author else "No author found"
        
        # Extract content from entry-content div
        content_paragraphs = response.xpath('//div[@class="entry-content"]//p/text()').getall()
        
        if not content_paragraphs:
            # Fallback: get all paragraphs
            content_paragraphs = response.xpath('//p/text()').getall()
        
        # Clean and filter paragraphs
        cleaned_paragraphs = []
        for para in content_paragraphs:
            para_text = para.strip()
            if para_text and len(para_text) > 15:
                cleaned_paragraphs.append(para_text)
        
        content_text = "\n\n".join(cleaned_paragraphs)
        
        # Calculate word count
        word_count = len(content_text.split()) if content_text else 0
        
        # Yield the scraped data
        yield {
            'url': url,
            'title': title,
            'content': content_text,
            'author': author,
            'date_text': date_text,
            'published_date': published_date.isoformat() if published_date else None,
            'word_count': word_count,
            'paragraph_count': len(cleaned_paragraphs),
            'scraped_at': datetime.now().isoformat(),
            'source': 'ICIR Nigeria'
        }
        
        self.logger.info(f"✅ Successfully scraped: {title[:50]}... ({word_count} words)")

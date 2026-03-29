from bs4 import BeautifulSoup
import json, os, sys
from datetime import datetime, timedelta
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
from functools import partial
from itertools import islice, takewhile, chain
import operator
from .ehub_crawler import ElectricityHubScraper

import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger("icirniger")

from src.database_store.database_client import DatabaseClient

class ICIRNigeriaScraper(ElectricityHubScraper):
    """ICIR Nigeria Energy & Power News Scraper"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.driver = None
        self.base_url = "https://www.icirnigeria.org"
        
    
    def parse_date(self, date_text):
        """Parse date - simplified"""
        if not date_text:
            return None
        
        try:
            return datetime.strptime(date_text.strip(), '%B %d, %Y')
        except:
            return None
    
    def is_article_recent(self, date_text, days_back=7):
        """Check if article is recent"""
        article_date = self.parse_date(date_text)
        if not article_date:
            return False
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        return article_date >= cutoff_date
    
    def extract_article_from_element(self, article):
        """Extract article data from single element"""
        title_element = article.find(['h1', 'h2', 'h3'])
        if not title_element:
            return None
        
        link_element = title_element.find('a', href=True)
        if not link_element:
            return None
        
        article_url = urljoin(self.base_url, link_element['href'])
        title = title_element.get_text(strip=True)
        
        if not title:
            return None
            
        return {'url': article_url, 'title': title}
    
    def scrape_single_page(self, page_num, category_url):
        """Scrape a single page and return articles"""
        # Build page URL
        page_url = category_url if page_num == 1 else f"{category_url}page/{page_num}/"
        
        print(f"\n📂 Scraping page {page_num}: {page_url}")
        
        try:
            self.driver.get(page_url)
            time.sleep(4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            articles = soup.find_all('article') or soup.find_all('div', class_=lambda x: x and 'post' in str(x).lower())
            
            # Use map and filter instead of for loop
            extracted_articles = map(self.extract_article_from_element, articles)
            valid_articles = list(filter(None, extracted_articles))
            
            # Print articles using map
            list(map(lambda art: print(f"   ✅ Found article: {art['title'][:50]}..."), valid_articles))
            
            logger.info(f"📰 Page {page_num}: Found {len(valid_articles)} articles")
            return valid_articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping page {page_num}: {e}")
            return []
    
    def get_article_links_from_category(self, category_url, max_pages=2, max_articles=10):
        """Get article links from category pages using built-in functions"""
        
        if not self.driver:
            ElectricityHubScraper.setup_driver(self)
        
        # Create page numbers
        page_numbers = range(1, max_pages + 1)
        
        # Create partial function for scraping with category_url
        scrape_page = partial(self.scrape_single_page, category_url=category_url)
        
        # Map scraping function to page numbers
        page_results = map(scrape_page, page_numbers)
        
        # Filter out empty results and flatten
        non_empty_results = filter(None, page_results)
        all_articles = list(chain.from_iterable(non_empty_results))
        
        # Remove duplicates using dict.fromkeys (preserves order)
        seen = set()
        unique_articles = list(filter(
            lambda x: x['url'] not in seen and not seen.add(x['url']),
            all_articles
        ))
        
        logger.info(f"\n📊 Total unique articles found: {len(unique_articles)}")
        return list(islice(unique_articles, max_articles)) if max_articles else unique_articles
    
    def extract_date_and_author(self, soup):
        """Extract date and author using built-in functions"""
        
        date_text = "No date found"
        author = "No author found"
        
        # Find time element
        time_element = soup.find('time', class_='entry-date updated td-module-date')
        if time_element:
            datetime_attr = time_element.get('datetime')
            if datetime_attr:
                parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                date_text = parsed_date.strftime('%B %d, %Y')
                #logger.info(f"📅 Date from datetime attr: {date_text}")
            else:
                date_text = time_element.get_text(strip=True)
                #logger.info(f"📅 Date from time text: {date_text}")

        # Find author
        author_wrap = soup.find('div', class_='tdb-author-name-wrap')
        if author_wrap:
            author = author_wrap.get_text(strip=True)
            if author and len(author) > 2:
                logger.info(f"👤 Author found in wrap text: {author}")
        
        return date_text, author
    
    def is_valid_paragraph(self, para):
        """Check if paragraph is valid"""
        para_text = para.get_text(strip=True)
        skip_terms = ['related-post', 'adsbygoogle', 'save my name',
                    'comment', 'akismet', 'support us', 'journalism', 'democracy',
                    'related-post', 'leave a reply', 'email', 'website in this browser']
        return (para_text and 
                len(para_text) > 30 and 
                not any(skip in para_text.lower() for skip in skip_terms))
    
    def extract_article_data(self, soup, url):
        """Extract article data using built-in functions"""
        
        # Title extraction
        title_element = soup.find('h1', class_='tdb-title-text')
        article_title = title_element.get_text(strip=True) if title_element else "No title found"
        
        # Date and Author
        date_text, author = self.extract_date_and_author(soup)
        
        # Content extraction using filter and map
        article_content = soup.find('div', class_='td-post-content')
        content_paragraphs = []
        
        if article_content:
            paragraphs = article_content.find_all('p')
            # Use filter and map instead of for loop
            valid_paras = filter(self.is_valid_paragraph, paragraphs)
            content_paragraphs = list(map(operator.methodcaller('get_text', strip=True), valid_paras))
        
        content_text = "\n\n".join(content_paragraphs)
        word_count = len(content_text.split()) if content_text else 0
        
        logger.info(f"📝 Final: {len(content_paragraphs)} paragraphs ({word_count} words)")
        
        return {
            'url': url,
            'title': article_title,
            'content': content_text,
            'author': author,
            'date_text': date_text,
            'word_count': word_count,
            'scraped_at': datetime.now().isoformat(),
            'source': 'ICIR Nigeria'
        }
    
    def scrape_article(self, url):
        """Scrape a single article"""
        
        if not self.driver:
            self.setup_driver()
        
        try:
            logger.info(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            article_data = self.extract_article_data(soup, url)
            
            logger.info(f"📰 Title: {article_data['title']}")
            logger.info(f"📝 Words: {article_data['word_count']}")
            logger.info(f"📅 Date: {article_data['date_text']}")
            logger.info(f"👤 Author: {article_data['author']}")
            
            return article_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            return None

    def process_article_link(self, indexed_link, days_back, max_articles, current_count):
        """Process a single article link"""
        i, link_info = indexed_link
        
        # Stop if we've reached max articles
        if current_count[0] >= max_articles:
            return None
        
        logger.info(f"\n📄 Article {i}: {link_info['title'][:50]}...")
        
        article_data = self.scrape_article(link_info['url'])
        if not article_data:
            return None
            
        if self.is_article_recent(article_data['date_text'], days_back):
            current_count[0] += 1  # Increment counter
            logger.info("✅ Recent article - added!")
            time.sleep(2)
            return article_data
        else:
            logger.info("⏰ Article too old - skipped")
            time.sleep(2)
            return None

    def scrape_recent_articles(self, days_back=7, category_url="https://www.icirnigeria.org/category/business-and-economy/energy-and-power/", max_pages=2, max_articles=5):
        """Main function: Get recent articles using built-in functions"""
        
        logger.info(f"🚀 Starting ICIR Nigeria scrape for articles from last {days_back} days")
        logger.info(f"📂 Category: {category_url}")
        logger.info(f"📄 Max pages: {max_pages}")
        logger.info(f"📰 Max articles: {max_articles}")
        logger.info("=" * 60)
        
        # Get article links
        article_links = self.get_article_links_from_category(category_url, max_pages, max_articles * 2)
        
        if not article_links:
            logger.error("❌ No articles found")
            return []
        
        # Create indexed links
        indexed_links = enumerate(article_links, 1)
        
        # Use a mutable counter to track articles
        current_count = [0]
        
        # Create partial function with fixed parameters
        process_func = partial(
            self.process_article_link, 
            days_back=days_back, 
            max_articles=max_articles, 
            current_count=current_count
        )
        
        # Map processing function and filter results
        processed_results = map(process_func, indexed_links)
        valid_articles = filter(None, processed_results)
        
        # Take only the required number of articles
        scraped_articles = list(islice(valid_articles, max_articles))
        
        logger.info(f"\n🎉 Scraped {len(scraped_articles)} recent articles")
        return scraped_articles
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            logger.info("🔴 Browser closed")

# Simple usage
def scrape_icir_news(days_back=7, max_articles=5, max_pages=2, headless=True):
    """Scrape ICIR Nigeria energy news"""
    
    # Initialise database client
    db_client = DatabaseClient()
    
    #Initialize scraper
    scraper = ICIRNigeriaScraper(headless=headless)
    category_url = "https://www.icirnigeria.org/category/business-and-economy/energy-and-power/"
    try:
        articles= scraper.scrape_recent_articles(
            days_back=days_back,
            category_url=category_url,
            max_pages=max_pages,
            max_articles=max_articles)
        
        # Save to database
        if articles:
            saved_count, duplicate_count = db_client.save_articles(articles, source_name="ICIR Nigeria")
            logger.info(f"\n💾 Database: {saved_count} new articles saved, {duplicate_count} duplicates skipped")
        
        
        return articles
    finally:
        scraper.close()
        db_client.close()

# Test
if __name__ == "__main__":
    logger.info("⚡ ICIR Nigeria Energy Scraper")
    logger.info("=" * 40)
    
    articles = scrape_icir_news(
        days_back=60, 
        max_articles=2,
        max_pages=3,
        headless=True
    )

    if articles:
        with open('icir_nigeria_articles.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ SUCCESS! Scraped {len(articles)} articles")
        logger.info("💾 Data saved to: icir_nigeria_articles.json")

        # Use enumerate and map for output instead of for loop
        article_info = enumerate(articles, 1)
        output_func = lambda x: logger.info(f"\n{x[0]}. {x[1]['title']}\n"
                                     f"   📅 {x[1]['date_text']} | 👤 {x[1]['author']}\n"
                                     f"   📝 {x[1]['word_count']} words\n"
                                     f"   🔗 {x[1]['url']}")
        list(map(output_func, article_info))
    else:
        logger.info("❌ No recent articles found")
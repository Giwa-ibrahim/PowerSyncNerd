import requests
from bs4 import BeautifulSoup
import json, os, sys
from datetime import datetime, timedelta
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin

# Add database path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_store.database_client import DatabaseClient


class ElectricityHubScraper:
    """Fixed scraper with proper article detection"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://theelectricityhub.com"
        
    def setup_driver(self):
        """Setup Chrome driver with WebDriver Manager"""
        print("🔧 Setting up Chrome driver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome driver initialized!")
    
    def parse_date(self, date_text):
        """Parse date from format: 'October 31, 2025'"""
        if not date_text:
            return None
        
        try:
            # Clean the date text and parse
            date_clean = date_text.strip()
            return datetime.strptime(date_clean, '%B %d, %Y')
        except ValueError:
            # Try alternative parsing
            try:
                # Handle format like "Monday, November 3, 2025"
                if ',' in date_clean:
                    parts = date_clean.split(',')
                    if len(parts) >= 2:
                        date_part = ','.join(parts[-2:]).strip()  # Take last two parts
                        return datetime.strptime(date_part, '%B %d, %Y')
            except ValueError:
                pass
        
        return None
    
    def is_article_recent(self, date_text, days_back=7):
        """Check if article is within the last N days"""
        article_date = self.parse_date(date_text)
        #print(f"🗓️ Parsed date: {article_date}")
        if not article_date:
            return False  
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        return article_date >= cutoff_date
    
    
    def extract_date_and_author(self, soup):
        """Extract date and author from entry-meta based on HTML structure"""
        date_text = "No date found"
        author = "No author found"
        
       # Find ALL entry-meta divs
        entry_metas = soup.find_all('div', class_='entry-meta')
        
        # Look through each entry-meta to find the one with date/author
        for entry_meta in entry_metas:
            # Skip the category-meta div
            if 'category-meta' in str(entry_meta.get('class', [])):
                continue
            
            # Look for date in this entry-meta
            date_div = entry_meta.find('div', class_='date')
            author_div = entry_meta.find('div', class_='by-author vcard author')
        
            # If this entry-meta has date or author, use it
            if date_div or author_div:
                # Extract date
                if date_div:
                    date_link = date_div.find('a')
                    if date_link:
                        date_text = date_link.get_text(strip=True)
                        print(f"   📅 Date from link: {date_text}")
                
                # Extract author
                if author_div:
                    author_link = author_div.find('a')
                    if author_link:
                        author = author_link.get_text(strip=True)
                        print(f"   👤 Author from link: {author}")
                
                break  # Found the right entry-meta, stop looking
            else:
                print(f"   ❌ Entry-meta {i+1} has no date/author")
    
            
        return date_text, author
    
    def get_article_links_from_category(self, category_url, max_pages=5, days_back=7):
        """Get unique article links from category pages with better detection"""
        
        if not self.driver:
            self.setup_driver()
        
        all_article_links = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        for page_num in range(1, max_pages + 1):
            # Construct page URL
            if page_num == 1:
                page_url = category_url
            else:
                page_url = f"{category_url}page/{page_num}/"
            
            print(f"\n📂 Scraping page {page_num}: {page_url}")
            
            try:
                self.driver.get(page_url)
                time.sleep(3)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Better article detection - look for actual article elements
                articles = soup.find_all('article')  # Most likely to be actual articles
                
                if not articles:
                    # Fallback: look for divs with post-related classes
                    articles = soup.find_all('div', class_=lambda x: x and any(word in str(x).lower() for word in ['post-', 'article-', 'entry-']))
                
                page_articles = []
                
                for article in articles:
                    try:
                        # Get the main article link (usually the title link)
                        title_element = article.find(['h1', 'h2', 'h3'], class_=lambda x: x and 'title' in str(x).lower())
                        
                        if not title_element:
                            # Fallback: any heading with a link
                            title_element = article.find(['h1', 'h2', 'h3'])
                        
                        if not title_element:
                            continue
                        
                        # Get the link from title
                        link_element = title_element.find('a', href=True)
                        if not link_element:
                            # Sometimes the whole title is wrapped in a link
                            link_element = title_element.find_parent('a', href=True)
                        
                        if not link_element:
                            continue
                        
                        article_url = urljoin(self.base_url, link_element['href'])
                        
                        # Skip duplicates
                        if article_url in seen_urls:
                            continue
                        seen_urls.add(article_url)
                        
                        # Get title text
                        title = title_element.get_text(strip=True)
                        if not title or title.lower() in ['no title', '']:
                            continue
                        
                        date_text, _ = self.extract_date_and_author(article)
                        # Filter by date if we have it
                        if date_text and not self.is_article_recent(date_text, days_back):
                            print(f"   ⏰ Skipping old article: {title[:40]}... ({date_text})")
                            continue
                        
                        page_articles.append({
                            'url': article_url,
                            'title': title,
                            'date_text': date_text
                        })
                        
                        print(f"   ✅ Found recent article: {title[:50]}...")
                        
                    except Exception as e:
                        print(f"   ❌ Error processing article: {e}")
                        continue
                
                all_article_links.extend(page_articles)
                print(f"📰 Page {page_num}: Found {len(page_articles)} unique recent articles")
                
                # If no articles found on this page, stop pagination
                if len(page_articles) == 0:
                    print(f"🛑 No more recent articles found, stopping at page {page_num}")
                    break
                
            except Exception as e:
                print(f"❌ Error scraping page {page_num}: {e}")
                break
        
        print(f"\n🎯 Total unique recent articles found: {len(all_article_links)}")
        return all_article_links
    
    def extract_article_data(self, soup, url):
        """Extract article data using correct HTML structure"""
        
        # Title from entry-header
        entry_header = soup.find('header', class_='entry-header')
        if entry_header:
            title_element = entry_header.find('h1', class_='entry-title')
            article_title = title_element.get_text(strip=True) if title_element else "No title found"
        else:
            # Fallback
            print("Now using Fallback title extraction...")
            title_element = soup.find('h1', class_='entry-title') or soup.find('h1')
            article_title = title_element.get_text(strip=True) if title_element else "No title found"
        
        # Date and Author from entry-meta (inside entry-header)
        date_text, author = self.extract_date_and_author(soup)
        
        # Content from entry-content div
        content_element = soup.find('div', class_='entry-content')
        content_paragraphs = []
        
        if content_element:
            paragraphs = content_element.find_all('p')
            for para in paragraphs:
                para_text = para.get_text(strip=True)
                if para_text and len(para_text) > 15:
                    content_paragraphs.append(para_text)
        else:
            print("Now using Fallback paragraph extraction...")
            all_paragraphs = soup.find_all('p')
            for para in all_paragraphs:
                para_text = para.get_text(strip=True)
                if para_text and len(para_text) > 20:
                    content_paragraphs.append(para_text)
        
        content_text = "\n\n".join(content_paragraphs)
        
        return {
            'url': url,
            'title': article_title,
            'content': content_text,
            'author': author,
            'date_text': date_text,
            'word_count': len(content_text.split()) if content_text else 0,
            'paragraph_count': len(content_paragraphs),
            'scraped_at': datetime.now().isoformat(),
            'source': 'ElectricityHub'
        }
    
    def scrape_article(self, url):
        """Scrape a single article"""
        
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            page_source = self.driver.page_source
            
            if any(block_text in page_source.lower() for block_text in ['incapsula', 'blocked', 'access denied']):
                print("❌ Blocked by protection system")
                return None
            
            soup = BeautifulSoup(page_source, 'html.parser')
            article_data = self.extract_article_data(soup, url)
            
            print(f"📰 Title: {article_data['title']}")
            print(f"📝 Words: {article_data['word_count']}")
            print(f"📅 Date: {article_data['date_text']}")
            print(f"👤 Author: {article_data['author']}")
            
            return article_data
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def scrape_recent_articles(self, category_url="https://theelectricityhub.com/category/west-africa/", days_back=7, max_pages=3, max_articles=10):
        """Main function: Get recent articles and scrape them"""
        
        print(f"🚀 Starting scrape for articles from last {days_back} days")
        print(f"📂 Category: {category_url}")
        print(f"📄 Max pages: {max_pages}")
        print(f"📰 Max articles: {max_articles}")
        print("=" * 60)
        
        # Step 1: Get unique article links with date filtering
        article_links = self.get_article_links_from_category(category_url, max_pages, days_back)
        
        if not article_links:
            print("❌ No recent articles found")
            return []
        
        # Limit to max_articles
        if len(article_links) > max_articles:
            article_links = article_links[:max_articles]
            print(f"📊 Limited to {max_articles} articles")
        
        # Step 2: Scrape each unique article
        scraped_articles = []
        
        print(f"\n📝 Scraping {len(article_links)} unique articles...")
        print("=" * 40)
        
        for i, link_info in enumerate(article_links, 1):
            print(f"\n📄 Article {i}/{len(article_links)}: {link_info['title'][:50]}...")
            
            article_data = self.scrape_article(link_info['url'])
            if article_data:
                scraped_articles.append(article_data)
                print("✅ Successfully scraped!")
            else:
                print("❌ Failed to scrape")
            
            # Small delay between articles
            if i < len(article_links):
                time.sleep(2)
        
        print(f"\n🎉 Scraping complete! Successfully scraped {len(scraped_articles)} unique articles")
        return scraped_articles
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔴 Browser closed")

# Simple usage function
def scrape_ehub_news(days_back=7, max_articles=5, max_pages=2, headless=True):
    """Scrape recent West Africa power news"""
    # Initialise database client
    db_client = DatabaseClient()
    
    # Initialize scraper
    scraper = ElectricityHubScraper(headless=headless)
    try:
        articles = scraper.scrape_recent_articles(
            category_url="https://theelectricityhub.com/category/west-africa/",
            days_back=days_back,
            max_pages=max_pages,
            max_articles=max_articles
        )
        
        # Save to database
        if articles:
            saved_count, duplicate_count = db_client.save_articles(articles, source_name= "ElectricityHub")
            print(f"\n💾 Database: {saved_count} new articles saved, {duplicate_count} duplicates skipped")
    finally:
        scraper.close()
        db_client.close()

# Test the fixed scraper
# if __name__ == "__main__":
#     print("⚡ ElectricityHub Scraper")
#     print("=" * 60)
    
#     # Test: Get recent unique articles
#     articles = scrape_ehub_news(
#         days_back=7,       # Last 7 days
#         max_articles=5,    # Limit to 5 unique articles
#         max_pages=2,       # Check first 2 pages
#         headless=True      # Run in background
#     )
    
#     if articles:
#         # Save results
#         with open('electricity_hub_data.json', 'w', encoding='utf-8') as f:
#             json.dump(articles, f, indent=2, ensure_ascii=False)
        
#         print(f"\n✅ SUCCESS! Scraped {len(articles)} unique articles")
#         print("💾 Data saved to: electricity_hub_data.json")

#         print(f"\n📊 Summary:")
#         for i, article in enumerate(articles, 1):
#             print(f"   {i}. {article['title'][:60]}...")
#             print(f"      📅 {article['date_text']} | 📝 {article['word_count']} words")
#             print(f"      🔗 {article['url']}")
#             print()
#     else:
#         print("❌ No recent articles found")
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sys
import os

# Add parent directory to path to import database_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.database_store.database_client import DatabaseClient


class NewsCrawlersPipeline:
    def process_item(self, item, spider):
        return item


class DatabasePipeline:
    """Pipeline to save scraped articles to database"""
    
    def __init__(self):
        self.db_client = None
        self.articles = []
    
    def open_spider(self, spider):
        """Initialize database connection when spider opens"""
        spider.logger.info("💾 Opening database connection...")
        self.db_client = DatabaseClient()
        self.articles = []
    
    def close_spider(self, spider):
        """Save all articles and close database connection when spider closes"""
        if self.articles:
            spider.logger.info(f"💾 Saving {len(self.articles)} articles to database...")
            try:
                saved_count, duplicate_count = self.db_client.save_articles(
                    self.articles, 
                    source_name="ICIR Nigeria"
                )
                spider.logger.info(f"✅ Saved {saved_count} new articles, {duplicate_count} duplicates skipped")
            except Exception as e:
                spider.logger.error(f"❌ Error saving to database: {e}")
        
        if self.db_client:
            self.db_client.close()
            spider.logger.info("💾 Database connection closed")
    
    def process_item(self, item, spider):
        """Collect items to save in batch"""
        self.articles.append(dict(item))
        return item

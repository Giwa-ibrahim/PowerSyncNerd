import os
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv
from .create_table import PowerElectricNews, Base

logger = logging.getLogger("database_client")

# Load environment variables
load_dotenv()

class DatabaseClient:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None
    
    def setup_engine(self):
        """Create PostgreSQL database engine"""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=False,
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"PostgreSQL engine created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating database engine: {e}")
            raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            if not self.engine:
                self.setup_engine()
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
            
    def create_table(self):
        """Create power_electric_news table"""
        try:
            if not self.engine:
                self.setup_engine()
        
            # Create the table using SQLAlchemy
            Base.metadata.create_all(self.engine)
            logger.info("Table 'power_electric_news' created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating table: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            self.setup_engine()
        return self.SessionLocal()
    
    def save_articles(self, articles_data, source_name):
        """Save articles directly to database"""
        session = self.get_session()
        saved_count = 0
        duplicate_count = 0
        
        try:
            for article_data in articles_data:
                try:
                    # Create PowerElectricNews object directly
                    article = PowerElectricNews(
                        title=article_data.get('title', ''),
                        content=article_data.get('content', ''),
                        url=article_data.get('url', ''),
                        published_date=article_data.get('date_text', ''),
                        source=source_name,
                        author=article_data.get('author', 'Unknown')
                    )
                    
                    session.add(article)
                    session.commit()
                    saved_count += 1
                    print(f"💾 Saved: {article.title[:50]}...")
                    
                except IntegrityError:
                    session.rollback()
                    duplicate_count += 1
                    print(f"🔄 Duplicate URL: {article_data.get('url', '')}")
                    
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving article: {e}")
            
        finally:
            session.close()
        
        print(f"\n📊 Database Summary: {saved_count} saved, {duplicate_count} duplicates")
        return saved_count, duplicate_count
    
    def get_articles(self, source=None, limit=50):
        """Get articles from database"""
        session = self.get_session()
        
        try:
            query = session.query(PowerElectricNews)
            
            if source:
                query = query.filter(PowerElectricNews.source == source)
            
            articles = query.order_by(PowerElectricNews.scraped_at.desc()).limit(limit).all()
            return articles
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching articles: {e}")
            return []
            
        finally:
            session.close()
    
    def get_stats(self):
        """Get database statistics"""
        session = self.get_session()
        
        try:
            total_articles = session.query(PowerElectricNews).count()
            
            # Articles by source
            sources_stats = {}
            sources = session.query(PowerElectricNews.source).distinct().all()
            for (source,) in sources:
                count = session.query(PowerElectricNews).filter(PowerElectricNews.source == source).count()
                sources_stats[source] = count
            
            return {
                'total_articles': total_articles,
                'articles_by_source': sources_stats,
                'database_url': self.db_url.split('://', 1)[0] + '://***'
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}
            
        finally:
            session.close()
        
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

# Initialize database client and create table
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    db_client = DatabaseClient()
    
    try:
        # Test connection
        if db_client.test_connection():
            print("✅ Database connection successful")
            
            # Create table
            db_client.create_table()
            print("✅ Table created successfully")
            
            # Get stats
            stats = db_client.get_stats()
            print(f"📊 Database stats: {json.dumps(stats, indent=2)}")
            
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        db_client.close()
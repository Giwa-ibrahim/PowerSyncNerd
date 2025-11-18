from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class PowerElectricNews(Base):
    """Power electric news table model"""
    __tablename__ = 'power_electric_news'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    url = Column(Text, unique=True)
    published_date = Column(Text)
    source = Column(Text)
    author = Column(Text)
    scraped_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<PowerElectricNews(title='{self.title[:50]}...', source='{self.source}')>"
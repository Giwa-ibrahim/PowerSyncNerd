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

class Subscriber(Base):
    """Newsletter subscriber table model"""
    __tablename__ = 'subscribers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    preferred_time = Column(String, nullable=False, default='both')  # '8am', '6pm', 'both'
    occupation = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Subscriber(email='{self.email}', occupation='{self.occupation}')>"
"""
AI-powered news summarization using Llama 3.2
Core summarization logic only - Modern LangChain implementation
"""
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import time
import json
import re
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.ai.llm import get_llm_client
from database_store.database_client import DatabaseClient
from database_store.create_table import PowerElectricNews

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("summarizer")

# =============================================================================
# PROMPT TEMPLATE
# =============================================================================

ANALYSIS_PROMPT = """You are an expert analyst for Nigeria's power sector.
Analyze this news article and provide a concise summary AND an impact assessment.

TITLE: {title}
SOURCE: {source}
CONTENT: {content}

YOUR TASK:
1. Write a brief, clear summary in 2-3 sentences (50-100 words).
2. Assess the impact level (HIGH, MEDIUM, or LOW).
   - HIGH: Major infrastructure project, significant policy change, large investment (>$100M).
   - MEDIUM: Regional development, moderate investment ($10M-$100M).
   - LOW: Minor updates, routine operations (<$10M).

CRITICAL RULE: You MUST return your response in the following JSON format:
{{
  "summary": "your summary here",
  "impact": "HIGH/MEDIUM/LOW"
}}

Do not include any other text in your response. Just the JSON.
"""


# =============================================================================
# CORE FUNCTIONS 
# =============================================================================

def summarize_article(llm, article: PowerElectricNews) -> Dict:
    """
    Summarize and assess impact in a single API call
    """
    logger.info(f"🔍 Analyzing: {article.title[:50]}...")
    
    try:
        title = article.title or 'No title'
        content = article.content or ''
        source = article.source or 'Unknown'
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=['title', 'content', 'source'],
            template=ANALYSIS_PROMPT
        )
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Invoke chain (Combined call)
        response = chain.invoke({
            'title': title,
            'content': content[:3000],
            'source': source
        })
        
        # Clean response if LLM added markdown backticks
        clean_response = re.sub(r'^```json\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
        
        try:
            data = json.loads(clean_response)
            summary = data.get('summary', 'Summary unavailable.')
            impact = data.get('impact', 'MEDIUM').strip().upper()
            if impact not in ['HIGH', 'MEDIUM', 'LOW']:
                impact = 'MEDIUM'
        except Exception:
            # Fallback for non-JSON response
            logger.warning("⚠️ LLM didn't return valid JSON, attempting simple parse")
            summary = response[:300].strip()
            impact = 'HIGH' if 'HIGH' in response.upper() else 'LOW' if 'LOW' in response.upper() else 'MEDIUM'

        logger.info(f"✅ Complete: {impact} impact")
        
        return {
            'title': title,
            'summary': summary,
            'impact': impact,
            'published_date': str(article.published_date) if article.published_date else 'Unknown',
            'source': source,
            'url': article.url or '',
            'author': article.author or 'Unknown'
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {
            'title': article.title or 'No title',
            'summary': f"Error: {str(e)}",
            'impact': 'LOW',
            'published_date': str(article.published_date) if article.published_date else 'Unknown',
            'source': article.source or 'Unknown',
            'url': article.url or '',
            'author': article.author or 'Unknown'
        }


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def fetch_recent_articles(
    days_back: int = 7,
    max_articles: int = 20,
    source: Optional[str] = None
) -> List[PowerElectricNews]:
    """
    Fetch recent articles from database
    
    Args:
        days_back: Number of days to look back
        max_articles: Maximum articles to fetch
        source: Optional source filter
    
    Returns:
        List of PowerElectricNews objects
    """
    logger.info(f"📰 Fetching articles from last {days_back} days...")
    
    db_client = DatabaseClient()
    cutoff_date = datetime.now() - timedelta(days=days_back)
    session = db_client.get_session()
    
    try:
        query = session.query(PowerElectricNews).filter(
            PowerElectricNews.scraped_at >= cutoff_date
        )
        
        if source:
            query = query.filter(PowerElectricNews.source == source)
        
        articles = query.order_by(
            PowerElectricNews.scraped_at.desc()
        ).limit(max_articles).all()
        
        logger.info(f"📊 Found {len(articles)} articles")
        return articles
        
    finally:
        session.close()
        db_client.close()


def summarize_recent_articles(
    days_back: int = 7,
    max_articles: int = 20,
    source: Optional[str] = None,
    model_name: str = 'llama-3.3-70b-versatile'
) -> List[Dict]:
    """
    Main function: Summarize recent articles from database
    
    Args:
        days_back: Number of days to look back
        max_articles: Maximum articles to process
        source: Optional source filter
        model_name: Ollama model name
    
    Returns:
        List of article summaries with metadata
    """
    logger.info("⚡ POWERSYNCNERD AI SUMMARIZER")
    logger.info("=" * 60)
    
    # Initialize LLM
    llm = get_llm_client()
    
    # Fetch articles
    articles = fetch_recent_articles(days_back, max_articles, source)
    
    if not articles:
        logger.warning("⚠️ No articles found")
        return []
    
    # Process each article
    summaries = []
    for i, article in enumerate(articles, 1):
        if i > 1:
            logger.info("⏳ Rate Limit Guard: Waiting 3 seconds...")
            time.sleep(3)
            
        logger.info(f"\nProcessing {i}/{len(articles)}")
        summary = summarize_article(llm, article)
        summaries.append(summary)
    
    logger.info(f"\n✅ Summarized {len(summaries)} articles")
    return summaries


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Test the summarizer"""
    import json
    
    print("\n⚡ PowerSyncNerd AI Summarizer")
    print("=" * 60)
    
    # Summarize recent articles
    summaries = summarize_recent_articles(
        days_back=30,
        max_articles=10
    )
    
    if not summaries:
        print("❌ No articles to summarize")
        return
    
    # Save to JSON
    with open('tests/summaries.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Summaries saved to: tests/summaries.json")
    print(f"✅ Summarized {len(summaries)} articles")
    
    # Show breakdown
    high = len([s for s in summaries if s['impact'] == 'HIGH'])
    medium = len([s for s in summaries if s['impact'] == 'MEDIUM'])
    low = len([s for s in summaries if s['impact'] == 'LOW'])
    
    print(f"\nImpact Breakdown:")
    print(f"  🔴 High: {high}")
    print(f"  🟠 Medium: {medium}")
    print(f"  🔵 Low: {low}")


if __name__ == "__main__":
    main()


"""
Main crawler orchestrator - aggregates all crawler operations
"""
import logging
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crawlers.ehub_crawler import scrape_ehub_news
from crawlers.icirniger_crawler import scrape_icir_news
from database_store.database_client import DatabaseClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main_crawler")


def all_crawlers(
    days_back: int = 7,
    max_articles_per_source: int = 10,
    max_pages: int = 3,
    headless: bool = True,
    sources: Optional[List[str]] = None
) -> Dict:
    """
    Run all or specific crawlers and aggregate results
    
    Args:
        days_back: Number of days to look back for articles
        max_articles_per_source: Maximum articles to scrape per source
        max_pages: Maximum pages to crawl per source
        headless: Run browsers in headless mode
        sources: List of sources to crawl ['icir', 'ehub'] or None for all
    
    Returns:
        Dictionary with crawl results and statistics
    
    Examples:
        # Crawl all sources
        all_crawlers(days_back=7)
        
        # Crawl only ICIR
        all_crawlers(days_back=7, sources=['icir'])
        
        # Crawl both
        all_crawlers(days_back=7, sources=['icir', 'ehub'])
    """
    
    logger.info("=" * 80)
    logger.info("⚡ POWERDIGEST CRAWLER")
    logger.info("=" * 80)
    
    # Define available crawlers
    available_crawlers = {
        'icir': {
            'name': 'ICIR Nigeria',
            'function': scrape_icir_news
        },
        'ehub': {
            'name': 'ElectricityHub',
            'function': scrape_ehub_news
        }
        # Add new crawlers here:
        # 'punch': {
        #     'name': 'Punch News',
        #     'function': scrape_punch_news
        # }
    }
    
    # Determine which sources to crawl
    if sources:
        sources_to_crawl = {k: v for k, v in available_crawlers.items() if k in sources}
    else:
        sources_to_crawl = available_crawlers
    
    logger.info(f"🎯 Crawling: {', '.join([v['name'] for v in sources_to_crawl.values()])}")
    
    # Results aggregation
    results = {
        'start_time': datetime.now().isoformat(),
        'total_articles': 0,
        'sources': {},
        'errors': []
    }
    
    # Crawl each source
    for source_key, source_info in sources_to_crawl.items():
        logger.info(f"\n🕷️  Crawling: {source_info['name']}")
        
        try:
            articles = source_info['function'](
                days_back=days_back,
                max_articles=max_articles_per_source,
                max_pages=max_pages,
                headless=headless
            )
            
            article_count = len(articles) if articles else 0
            
            results['sources'][source_key] = {
                'name': source_info['name'],
                'articles_found': article_count
            }
            
            results['total_articles'] += article_count
            logger.info(f"✅ {source_info['name']}: {article_count} articles")
            
        except Exception as e:
            error_msg = f"{source_info['name']}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            results['sources'][source_key] = {
                'name': source_info['name'],
                'articles_found': 0,
                'error': error_msg
            }
            results['errors'].append(error_msg)
    
    # Finalize
    results['end_time'] = datetime.now().isoformat()
    start = datetime.fromisoformat(results['start_time'])
    end = datetime.fromisoformat(results['end_time'])
    results['duration_seconds'] = round((end - start).total_seconds(), 2)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ COMPLETE: {results['total_articles']} articles in {results['duration_seconds']}s")
    logger.info("=" * 80)
    
    return results


def get_database_stats() -> Dict:
    """Get statistics from database about stored articles"""
    db_client = DatabaseClient()
    
    try:
        return db_client.get_stats()
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {'error': str(e)}
    finally:
        db_client.close()


# Main execution for testing
if __name__ == "__main__":
    import json
    
    print("\n⚡ PowerDigest Main Crawler")
    print("=" * 60)
    
    # Run all crawlers
    crawl_results = all_crawlers(
        days_back=14,
        max_articles_per_source=5,
        max_pages=3,
        headless=True,
        sources= ['icir']
    )
    
    # Save results
    with open('tests/crawl_results.json', 'w', encoding='utf-8') as f:
        json.dump(crawl_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: tests/crawl_results.json")
    
    # Database stats
    db_stats = get_database_stats()
    print("\n📊 DATABASE STATS")
    print(json.dumps(db_stats, indent=2))
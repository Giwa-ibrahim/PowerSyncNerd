"""
PowerSyncNerd Main Pipeline
Orchestrates crawling, summarization, and email sending
"""
import time
import logging
from src.crawlers.main_crawler import all_crawlers
from src.ai.summarizer import summarize_recent_articles
from src.email_module.email_sender import send_digest_email

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("powersyncnerd_pipeline")


def run_digest_pipeline(days_back: int = 1, max_articles: int = 20, trigger_time: str = None):
    """
    Run complete PowerSyncNerd pipeline
    
    Args:
        days_back: Number of days to look back for articles
        max_articles: Maximum articles to process
        trigger_time: Optional time context (e.g., '8am', '6pm') to filter recipients
    """
    
    logger.info("=" * 80)
    logger.info("⚡ POWERSYNCNERD PIPELINE STARTED")
    logger.info("=" * 80)
    logger.info(f"Configuration: days_back={days_back}, max_articles={max_articles}")
    
    start_time = time.time()
    
    # Step 1: Crawl news
    logger.info("\n📰 Step 1: Crawling news sources...")
    try:
        crawl_results = all_crawlers(days_back=days_back, max_articles_per_source=10)
        logger.info(f"✅ Crawled {crawl_results['total_articles']} articles successfully")
    except Exception as e:
        logger.error(f"❌ Crawling failed: {e}")
        logger.warning("Continuing with existing database articles...")
    
    # Step 2: Summarize articles
    logger.info("\n🤖 Step 2: Generating AI summaries...")
    try:
        summaries = summarize_recent_articles(days_back=days_back, max_articles=max_articles)
        
        if not summaries:
            logger.error("❌ No articles to summarize")
            logger.warning("Pipeline stopped - no content available")
            return False
        
        logger.info(f"✅ Summarized {len(summaries)} articles successfully")
        
        # Show impact breakdown
        high = len([s for s in summaries if s['impact'] == 'HIGH'])
        medium = len([s for s in summaries if s['impact'] == 'MEDIUM'])
        low = len([s for s in summaries if s['impact'] == 'LOW'])
        
        logger.info("Impact Distribution:")
        logger.info(f"   🔴 High: {high}")
        logger.info(f"   🟠 Medium: {medium}")
        logger.info(f"   🔵 Low: {low}")
        
    except Exception as e:
        logger.error(f"❌ Summarization failed: {e}", exc_info=True)
        return False
    
    # Step 3: Send email digest
    logger.info("\n📧 Step 3: Sending email digest...")
    try:
        success = send_digest_email(summaries, trigger_time=trigger_time)
        
        if success:
            logger.info("✅ Email sent successfully!")
        else:
            logger.error("❌ Email sending failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}", exc_info=True)
        return False
    
    # Pipeline complete
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    logger.info("\n" + "=" * 80)
    logger.info("🎉 PIPELINE COMPLETE")
    logger.info(f"⏱️ Total Processing Time: {minutes} minutes and {seconds} seconds")
    logger.info("=" * 80)
    logger.info("📊 Summary:")
    logger.info(f"   • Articles processed: {len(summaries)}")
    logger.info(f"   • High impact news: {high}")
    logger.info(f"   • Medium impact news: {medium}")
    logger.info(f"   • Low impact news: {low}")
    logger.info(f"   • Email recipients notified")
    logger.info("=" * 80)
    
    return True


def run_quick_test():
    """Run a quick test with minimal articles"""
    logger.info("🧪 QUICK TEST MODE")
    logger.info("=" * 80)
    logger.info("Testing with last 7 days, max 5 articles")
    
    return run_digest_pipeline(days_back=7, max_articles=5)


if __name__ == "__main__":
    import sys
    
    try:
        # Check command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            # Quick test mode
            success = run_quick_test()
        else:
            # Full pipeline
            success = run_digest_pipeline()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 Unexpected error in pipeline: {e}", exc_info=True)
        sys.exit(1)
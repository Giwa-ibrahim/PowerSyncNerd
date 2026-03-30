# ICIR Nigeria Scrapy Spider

Scrapy spider for scraping news articles from ICIR Nigeria's Energy & Power category.

## Spider Details

- **Name**: `icirnigeria`
- **Website**: https://www.icirnigeria.org
- **Category**: Business & Economy > Energy & Power
- **XPath Container**: `//*[@id="tdi_156"]`

## Usage

Navigate to the project directory:
```bash
cd src/news_crawlers
```

Run the spider:
```bash
scrapy crawl icirnigeria
```

With parameters:
```bash
scrapy crawl icirnigeria -a days_back=60 -a max_pages=2 -o articles.json
```

## Parameters

- `days_back` (default: 7) - Number of days to look back for articles
- `max_pages` (default: 3) - Maximum number of pages to scrape

## Output

Articles are saved with the following fields:
- url
- title
- content
- author
- date_text
- published_date
- word_count
- paragraph_count
- scraped_at
- source (always "ICIR Nigeria")

## File Structure

```
src/news_crawlers/
├── scrapy.cfg                          # Scrapy project configuration
└── news_crawlers/
    ├── __init__.py
    ├── items.py                        # Data structure definitions
    ├── settings.py                     # Scrapy settings
    ├── pipelines.py                    # Data processing pipelines
    └── spiders/
        ├── __init__.py
        ├── ehub_spider.py              # ICIR Nigeria spider (renamed)
        └── icirnigeria_spider.py       # Alternative implementation
```

## How It Works

1. **Parse category pages** - Extracts article links using XPath `//*[@id="tdi_156"]`
2. **Follow article links** - Visits each article page
3. **Extract content** - Gets title, author, date, and article text
4. **Filter by date** - Only keeps articles within the specified date range
5. **Save results** - Outputs to JSON/CSV/XML

## Based On

This spider follows the same structure as `src/crawlers/icirniger_crawler.py` but uses Scrapy framework instead of Selenium + BeautifulSoup.

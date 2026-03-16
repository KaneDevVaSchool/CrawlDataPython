# -*- coding: utf-8 -*-
"""
Scrapy settings for product_crawler project.

Production-ready configuration with:
- Retry on failure
- Request throttling (delay + concurrency limits)
- Custom/rotating user-agent
- Pipelines for JSON and MySQL
- Middlewares for user-agent rotation and delay
"""

BOT_NAME = 'product_crawler'
SPIDER_MODULES = ['product_crawler.spiders']
NEWSPIDER_MODULE = 'product_crawler.spiders'

# Obey robots.txt - Set to False only if you have permission to crawl
ROBOTSTXT_OBEY = False

# =============================================================================
# REQUEST THROTTLING - Avoid blocking
# =============================================================================
# Delay between requests (seconds) - be respectful to the server
DOWNLOAD_DELAY = 2.0
# Randomize delay between 0.5 * DOWNLOAD_DELAY and 1.5 * DOWNLOAD_DELAY
RANDOMIZE_DOWNLOAD_DELAY = True
# Maximum concurrent requests per domain
CONCURRENT_REQUESTS_PER_DOMAIN = 2
# Maximum concurrent requests (global)
CONCURRENT_REQUESTS = 8

# =============================================================================
# RETRY ON FAILURE
# =============================================================================
# Retry failed HTTP requests (conn errors, timeouts, 5xx)
RETRY_ENABLED = True
RETRY_TIMES = 3  # Max retries per request
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
# Retry on connection errors too (handled by RetryMiddleware)
RETRY_PRIORITY_ADJUST = -1

# =============================================================================
# CUSTOM USER-AGENT
# =============================================================================
# Default user-agent (our RotatingUserAgentMiddleware overrides per-request)
USER_AGENT = 'product_crawler/1.0 (+https://example.com/bot)'

# =============================================================================
# DOWNLOADER MIDDLEWARES
# =============================================================================
DOWNLOADER_MIDDLEWARES = {
    # Rotating user-agent - HIGH priority (runs first)
    'product_crawler.middlewares.RotatingUserAgentMiddleware': 400,
    # Disable default UserAgent (we use RotatingUserAgentMiddleware)
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# =============================================================================
# ITEM PIPELINES
# =============================================================================
# Order matters: DuplicateFilter first, then storage pipelines
ITEM_PIPELINES = {
    'product_crawler.pipelines.DuplicateFilterPipeline': 100,
    'product_crawler.pipelines.JsonFilePipeline': 300,
    'product_crawler.pipelines.CandidateJsonPipeline': 320,
    'product_crawler.pipelines.DetailUrlsFilePipeline': 350,
    'product_crawler.pipelines.MySQLPipeline': 400,
    'product_crawler.pipelines.CandidateMySQLPipeline': 500,
    'product_crawler.pipelines.HdndXaMySQLPipeline': 510,
}

# =============================================================================
# REQUEST/LOG SETTINGS
# =============================================================================
# Respect no-store and no-cache
COOKIES_ENABLED = True
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = 'INFO'
# Uncomment to save logs to file
# LOG_FILE = 'crawler.log'

# =============================================================================
# JSON PIPELINE CONFIG
# =============================================================================
JSON_OUTPUT_FILE = 'output/products.json'

# =============================================================================
# MYSQL PIPELINE CONFIG
# =============================================================================
# Configure these before using MySQL pipeline
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_DATABASE = 'scrapy_products'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'ServBay.dev'

# =============================================================================
# AUTOTHROTTLE (Optional - adaptive delay based on server load)
# =============================================================================
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

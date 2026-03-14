# -*- coding: utf-8 -*-
"""
Working example spider: Crawls https://books.toscrape.com/

This spider demonstrates the full crawling flow on a real, crawlable test site:
- List pages with pagination (catalogue page 1, 2, 3...)
- Product detail pages with full data
- All pipelines (JSON, dedup) work out of the box

Use this as a reference when adapting products_spider.py for your target site.
"""

import scrapy
from urllib.parse import urljoin
from product_crawler.items import ProductItem


class BooksSpider(scrapy.Spider):
    """
    Spider for books.toscrape.com - a Scrapy testing sandbox.
    
    Demonstrates: pagination, detail extraction, image URLs, prices.
    """
    
    name = 'books'
    allowed_domains = ['books.toscrape.com']
    start_urls = ['https://books.toscrape.com/']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'JSON_OUTPUT_FILE': 'output/books.json',
    }
    
    def parse(self, response):
        """
        Parse catalogue page: extract book links and follow pagination.
        """
        # Book links are in article.product_pod
        book_links = response.css('article.product_pod h3 a::attr(href)').getall()
        
        for link in book_links:
            book_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=book_url,
                callback=self.parse_book,
                meta={'product_url': book_url},
                errback=self.errback_book
            )
        
        # Pagination: next button
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            next_url = urljoin(response.url, next_page)
            yield scrapy.Request(url=next_url, callback=self.parse)
    
    def parse_book(self, response):
        """
        Parse book detail page and yield ProductItem.
        """
        product_url = response.meta.get('product_url', response.url)
        
        title = response.css('div.product_main h1::text').get()
        title = (title or '').strip()
        
        # Price (e.g., "£51.77")
        price = response.css('p.price_color::text').get()
        price = (price or '').strip()
        
        # Description (in product_description div)
        description_parts = response.css('#product_description + div ::text').getall()
        description = ' '.join((t or '').strip() for t in description_parts).strip()
        
        # Image - relative URL in src
        image_rel = response.css('div.item.active img::attr(src)').get()
        image_url = urljoin(response.url, image_rel) if image_rel else ''
        
        yield ProductItem(
            title=title,
            price=price,
            description=description,
            image_url=image_url,
            product_url=product_url
        )
    
    def errback_book(self, failure):
        """Log request failures."""
        self.logger.error('Book request failed: %s' % failure.request.url)

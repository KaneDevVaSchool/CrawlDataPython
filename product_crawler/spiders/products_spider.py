# -*- coding: utf-8 -*-
"""
Example spider: Crawls product listings with pagination and detail pages.

Flow:
1. Start from list page (e.g., https://example.com/products?page=1)
2. Extract product URLs from each list page
3. Follow pagination to next pages
4. Visit each product detail page and extract full information
5. Yield ProductItem for each product (deduplication handled by pipeline)

Note: This spider uses example.com as the target. For real crawling,
replace with actual URLs and adjust selectors to match the target site's HTML.
"""

import scrapy
from urllib.parse import urljoin, urlparse
from product_crawler.items import ProductItem


class ProductsSpider(scrapy.Spider):
    """
    Spider that crawls product listings with pagination and detail extraction.
    
    Uses two parse strategies:
    - parse: Handles list pages, extracts product links, follows pagination
    - parse_product: Handles detail pages, extracts full product data
    """
    
    name = 'products'
    allowed_domains = ['example.com']
    
    # Start URL - list page with pagination
    start_urls = ['https://example.com/products?page=1']
    
    # Custom settings (override project settings if needed)
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # 2 seconds between requests
    }
    
    def parse(self, response):
        """
        Parse list page: extract product URLs and pagination links.
        
        Called for:
        - Initial start_urls
        - Pagination links (next page)
        """
        # ---------------------------------------------------------------------
        # 1. Extract product detail URLs from the list page
        # ---------------------------------------------------------------------
        # Selector examples - adjust to match your target site structure:
        # Common patterns: .product-card a, .product-link, a[href*="/products/"]
        product_links = response.css('a[href*="/products/"]::attr(href)').getall()
        
        for link in product_links:
            # Build absolute URL (handles relative paths)
            product_url = urljoin(response.url, link)
            
            # Normalize URL (remove fragments, sort query params for deduplication)
            parsed = urlparse(product_url)
            product_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Yield request to detail page - callback extracts full data
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product,
                meta={'product_url': product_url},
                errback=self.errback_product,
                # Avoid duplicate requests - Scrapy filters by URL
                dont_filter=False
            )
        
        # ---------------------------------------------------------------------
        # 2. Follow pagination - find and request next page
        # ---------------------------------------------------------------------
        # Common pagination patterns:
        # - Next button: a.next-page, a[rel="next"], .pagination a:contains("Next")
        # - Page numbers: .pagination a[href*="page="]
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if not next_page:
            next_page = response.css('.pagination a.next::attr(href)').get()
        if not next_page:
            # Alternative: extract current page number and increment
            next_page = self._get_next_page_url(response)
        
        if next_page:
            next_url = urljoin(response.url, next_page)
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={'page': 'list'}
            )
    
    def _get_next_page_url(self, response):
        """
        Build next page URL by incrementing page query parameter.
        Fallback when no explicit next link exists.
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(response.url)
        params = parse_qs(parsed.query)
        current_page = int(params.get('page', [1])[0])
        next_page_num = current_page + 1
        
        params['page'] = [str(next_page_num)]
        new_query = urlencode(params, doseq=True)
        new_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
        return new_url
    
    def parse_product(self, response):
        """
        Parse product detail page: extract all product fields.
        
        Called for each product URL discovered on list pages.
        """
        # Use canonical URL from meta (passed from list page) for consistency
        product_url = response.meta.get('product_url', response.url)
        
        # ---------------------------------------------------------------------
        # Extract fields - adjust selectors for your target site
        # ---------------------------------------------------------------------
        title = response.css('h1.product-title::text').get()
        if not title:
            title = response.css('h1::text').get()
        title = (title or '').strip()
        
        price = response.css('.product-price::text').get()
        if not price:
            price = response.css('span.price::text').get()
        price = (price or '').strip()
        
        description = response.css('.product-description::text').getall()
        if not description:
            description = response.css('#product-description ::text').getall()
        description = ' '.join((t or '').strip() for t in description).strip()
        
        image_url = response.css('.product-image img::attr(src)').get()
        if not image_url:
            image_url = response.css('meta[property="og:image"]::attr(content)').get()
        if image_url:
            image_url = urljoin(response.url, image_url)
        
        # ---------------------------------------------------------------------
        # Build and yield ProductItem
        # ---------------------------------------------------------------------
        item = ProductItem(
            title=title,
            price=price,
            description=description,
            image_url=image_url or '',
            product_url=product_url
        )
        
        yield item
    
    def errback_product(self, failure):
        """
        Handle request failures (timeouts, connection errors, etc.).
        
        Scrapy will retry automatically based on RETRY_TIMES setting.
        This callback allows custom logging or alternative handling.
        """
        self.logger.error(
            'Request failed: %s - %s' % (failure.request.url, failure.value)
        )

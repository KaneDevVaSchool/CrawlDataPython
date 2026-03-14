# -*- coding: utf-8 -*-
"""
Middlewares module - Custom request/response processing.

Middlewares sit between the engine and the spider, processing requests
before they're sent and responses before they reach the spider.
"""

import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


# =============================================================================
# ROTATING USER-AGENT MIDDLEWARE
# =============================================================================
# Rotates through a pool of user-agents to avoid detection and blocking.
# Many sites block requests with default or suspicious user-agents.

class RotatingUserAgentMiddleware(UserAgentMiddleware):
    """
    Randomly assigns a user-agent from a predefined list to each request.
    
    This helps avoid blocking since requests appear to come from different
    browsers/devices. Add more user-agents to the list for better rotation.
    """
    
    # Pool of realistic user-agents (browsers, mobile, etc.)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]
    
    def process_request(self, request, spider):
        """Assign a random user-agent to each outgoing request."""
        user_agent = random.choice(self.USER_AGENTS)
        request.headers['User-Agent'] = user_agent
        # Don't return anything - let request continue through the pipeline


# =============================================================================
# REQUEST DELAY MIDDLEWARE
# =============================================================================
# Adds configurable delay between requests to avoid overwhelming the server
# and reduce the risk of being blocked (throttling).

class RequestDelayMiddleware:
    """
    Enforces a minimum delay between consecutive requests to the same domain.
    
    Uses Scrapy's built-in DOWNLOAD_DELAY in settings. This middleware
    provides additional control if needed (e.g., per-spider delays).
    """
    
    def __init__(self, delay):
        self.delay = delay
    
    @classmethod
    def from_crawler(cls, crawler):
        """Factory method - extracts delay from settings."""
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 1.0)
        return cls(delay)
    
    def process_request(self, request, spider):
        """Requests pass through - actual delay is handled by Scrapy's scheduler."""
        return None

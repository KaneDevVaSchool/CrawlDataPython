# -*- coding: utf-8 -*-
"""
Middlewares module - Custom request/response processing.

Middlewares sit between the engine and the spider, processing requests
before they're sent and responses before they reach the spider.
"""

import logging
import random
import re
from urllib.parse import urlparse

from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

logger = logging.getLogger(__name__)


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


class QuochoiD1nMiddleware:
    """
    Trang HTML rất ngắn yêu cầu set cookie D1N — tự gửi lại request kèm cookie,
    giảm miss khi spider chưa kịp xử lý.
    """

    def process_response(self, request, response, spider):
        if response.status != 200:
            return response
        try:
            host = urlparse(response.url).netloc or ""
        except Exception:
            return response
        if "hoidongbaucu.quochoi.vn" not in host:
            return response
        body = response.text or ""
        if len(body) > 900:
            return response
        if "document.cookie" not in body or "D1N=" not in body:
            return response
        m = re.search(r"D1N=([a-f0-9]+)", body)
        if not m:
            return response
        retries = request.meta.get("d1n_retries", 0)
        if retries >= 5:
            logger.warning("D1N: bo qua sau 5 lan: %s", response.url[:120])
            return response
        logger.debug("D1N: thu lai lan %s %s", retries + 1, response.url[:90])
        new_meta = dict(request.meta)
        new_meta["d1n_retries"] = retries + 1
        return request.replace(
            cookies={"D1N": m.group(1)},
            meta=new_meta,
            dont_filter=True,
        )

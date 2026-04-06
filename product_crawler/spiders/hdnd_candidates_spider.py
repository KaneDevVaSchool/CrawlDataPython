# -*- coding: utf-8 -*-
"""
Spider crawl danh sách ứng cử HĐND cấp tỉnh từ hoidongbaucu.quochoi.vn

Cấu hình nguồn: sửa HDND_SOURCES trong product_crawler/config.py
"""

import re
from urllib.parse import urljoin
import scrapy
from product_crawler.items import CandidateItem
from product_crawler.hdnd_crawl_support import QuochoiHdndMixin

try:
    from product_crawler.config import (
        BASE_URL, CANDIDATE_API_PATH, DETAIL_PATH, REFERER_URL,
        KHOA, PAGE_SIZE, HDND_SOURCES,
    )
except ImportError:
    BASE_URL = 'https://hoidongbaucu.quochoi.vn'
    CANDIDATE_API_PATH = '/get-chi-tiet-danh-sach-ung-cu-hdnd'
    DETAIL_PATH = '/thong-tin-nguoi-ung-cu'
    REFERER_URL = 'https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu-hdnd'
    KHOA = 16
    PAGE_SIZE = 300
    HDND_SOURCES = [{"name": "Thành phố Hồ Chí Minh", "province_id": "ddfaac97-a898-48ae-f9d7-08ddb2649d30", "khoa": 16}]


class HdndCandidatesSpider(QuochoiHdndMixin, scrapy.Spider):
    """
    Crawl danh sách ứng cử HĐND cấp tỉnh - parse HTML table từ API.
    Nguồn cấu hình: config.HDND_SOURCES
    """

    name = 'hdnd_candidates'
    allowed_domains = ['hoidongbaucu.quochoi.vn']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.35,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 6,
        'CONCURRENT_REQUESTS': 12,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
        'AUTOTHROTTLE_START_DELAY': 0.25,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'JSON_OUTPUT_FILE': 'output/hdnd_candidates.json',
    }

    def start_requests(self):
        """Request API cho từng tỉnh (từ config)."""
        if not HDND_SOURCES:
            self.logger.error('HDND_SOURCES trống. Thêm nguồn vào product_crawler/config.py')
            return

        sources = HDND_SOURCES
        # Chỉ chạy 1 nguồn: -a source=0 (index) hoặc -a source="Hà Nội" (tên)
        source_arg = getattr(self, 'source', None)
        if source_arg is not None:
            try:
                idx = int(source_arg)
                sources = [HDND_SOURCES[idx]] if 0 <= idx < len(HDND_SOURCES) else sources
            except ValueError:
                name = str(source_arg).strip().lower()
                name = name.replace('tp hcm', 'hồ chí minh').replace('hcm', 'hồ chí minh').replace('hanoi', 'hà nội')
                sources = [s for s in HDND_SOURCES if name in (s.get('name') or '').lower()]
            if sources:
                self.logger.info('Chay 1 nguon: %s', sources[0].get('name'))

        for src in sources:
            province_name = src.get('name', '')
            province_id = src.get('province_id', '')
            khoa = src.get('khoa', KHOA)
            if not province_id:
                continue
            url = (
                f"{BASE_URL}{CANDIDATE_API_PATH}"
                f"?lang=vi&tinhThanhKhoaId={province_id}&khoa={khoa}"
                f"&pageSize={PAGE_SIZE}&page=1"
            )
            yield scrapy.Request(
                url,
                callback=self.parse_table,
                meta={
                    'province': province_name,
                    'tinh_thanh_id': province_id,
                    'khoa': khoa,
                    'page': 1,
                },
                headers={'Referer': REFERER_URL},
            )
    
    def parse_table(self, response):
        """
        Parse HTML table từ API.
        Cấu trúc: | STT | Họ và tên | Chức vụ tóm tắt | Ngày sinh | Quê quán |
        """
        province = response.meta.get('province', '')
        tinh_thanh_id = response.meta.get('tinh_thanh_id', '')
        khoa = response.meta.get('khoa', KHOA)
        page = response.meta.get('page', 1)
        body = response.text

        # Trang set cookie qua JS (anti-bot) - request lai voi cookie
        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                d1n = m.group(1)
                self.logger.info('[%s] Nhan cookie D1N, request lai...', province)
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_table,
                    meta=response.meta,
                    headers={'Referer': REFERER_URL},
                    cookies={'D1N': d1n},
                    dont_filter=True,
                )
                return

        if len(body) < 500 and 'table' not in body.lower():
            self.logger.warning('[%s] API tra ve ngan (%d bytes)', province, len(body))
        
        # Parse "Tổng số: 208" để biết có cần request trang tiếp
        total_match = re.search(r'Tổng\s*số\s*[:\=]?\s*(\d+)', body, re.I | re.U)
        total = int(total_match.group(1)) if total_match else 0
        
        # Lấy tên tỉnh từ tiêu đề (ví dụ: "THÀNH PHỐ HỒ CHÍ MINH") - bỏ qua thông báo lỗi
        title_match = re.search(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', body, re.I)
        if title_match:
            t = title_match.group(1).strip()
            if t and 'lỗi' not in t.lower() and 'error' not in t.lower():
                province = t
        
        # 1. Thử parse HTML table (ưu tiên tr có data-id)
        rows = response.css('tr[data-id], tr.card-nguoi-ung-cu')
        if not rows:
            rows = response.css('table tr, tbody tr')
        # 2. Fallback: regex parse bảng (| 1 | Tên | Chức vụ | Ngày | Quê |)
        if not rows:
            row_pattern = re.compile(
                r'\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\s*\|'
            )
            for m in row_pattern.finditer(body):
                stt, name, position, birthdate, hometown = m.groups()
                name = name.strip()
                if name and not re.match(r'^(STT|HỌ)', name, re.I):
                    yield CandidateItem(
                        name=name,
                        province=province,
                        party='',
                        constituency='',
                        description=position.strip(),
                        detail_url='',
                        candidate_id=stt.strip(),
                        position=position.strip(),
                        birthdate=birthdate.strip(),
                        hometown=hometown.strip(),
                    )
            return
        
        # Parse HTML table
        headers = []
        list_limit = getattr(self, 'list_limit', None) or getattr(self, 'limit', None)
        try:
            list_limit = int(list_limit) if list_limit is not None else None
        except (ValueError, TypeError):
            list_limit = None
        emitted = response.meta.get('emitted', 0)

        for i, row in enumerate(rows):
            cells = row.css('td, th')
            texts = [c.css('::text').getall() for c in cells]
            cell_values = [''.join(t).strip() if t else '' for t in texts]
            
            # Chỉ bỏ qua hàng tiêu đề (STT | Họ và tên...) - không bỏ qua hàng dữ liệu đầu
            if i == 0 and cell_values:
                first = (cell_values[0] or '').strip().upper()
                second = (cell_values[1] or '').strip().upper()[:20]
                if first == 'STT' or second.startswith('HỌ') or second.startswith('HỌ VÀ'):
                    headers = cell_values
                    continue
            
            if len(cell_values) < 2:
                continue
            
            # Cột: STT, Họ và tên, Chức vụ tóm tắt, Ngày sinh, Quê quán
            stt = cell_values[0] if len(cell_values) > 0 else ''
            name = cell_values[1] if len(cell_values) > 1 else ''
            position = cell_values[2] if len(cell_values) > 2 else ''
            birthdate = cell_values[3] if len(cell_values) > 3 else ''
            hometown = cell_values[4] if len(cell_values) > 4 else ''
            
            if not name or name.upper().startswith('HỌ') or name.upper().startswith('STT'):
                continue
            
            # Link chi tiết: data-id, thẻ a, hoặc regex tìm UUID trong HTML
            candidate_uuid = row.xpath('@data-id').get() or row.css('::attr(data-id)').get() or ''
            if not candidate_uuid:
                row_html = row.get() or ''
                uuid_m = re.search(
                    r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
                    row_html, re.I
                )
                if uuid_m:
                    candidate_uuid = uuid_m.group(1)
            if not candidate_uuid:
                detail_link = row.css('a::attr(href)').get()
                if detail_link and 'thong-tin-nguoi-ung-cu' in detail_link:
                    uuid_m = re.search(
                        r'thong-tin-nguoi-ung-cu/([a-f0-9\-]+)',
                        detail_link, re.I
                    )
                    if uuid_m:
                        candidate_uuid = uuid_m.group(1)
                detail_url = urljoin(response.url, detail_link) if detail_link else ''
            else:
                detail_url = (
                    f"{BASE_URL}{DETAIL_PATH}/{candidate_uuid}"
                    f"?lang=vi&khoa={khoa}"
                )
            
            yield CandidateItem(
                name=name,
                province=province,
                party='',
                constituency='',
                description=position,
                detail_url=detail_url,
                candidate_id=stt,
                candidate_uuid=candidate_uuid,
                position=position,
                birthdate=birthdate,
                hometown=hometown,
            )
            emitted += 1
            if list_limit and emitted >= list_limit:
                self.logger.info('[%s] Dat limit=%d, dung lai', province, list_limit)
                return

        if not list(rows):
            self.logger.warning('[%s] Khong tim thay bang. body_len=%d', province, len(body))
        
        # Phân trang: request trang tiếp nếu còn dữ liệu (và chưa đạt list_limit)
        max_page = ((total - 1) // PAGE_SIZE) + 1 if total > 0 else 1
        if page < max_page and tinh_thanh_id and (not list_limit or emitted < list_limit):
            next_url = (
                f"{BASE_URL}{CANDIDATE_API_PATH}"
                f"?lang=vi&tinhThanhKhoaId={tinh_thanh_id}&khoa={khoa}"
                f"&pageSize={PAGE_SIZE}&page={page + 1}"
            )
            yield scrapy.Request(
                next_url,
                callback=self.parse_table,
                meta={
                    'province': province,
                    'tinh_thanh_id': tinh_thanh_id,
                    'khoa': khoa,
                    'page': page + 1,
                    'emitted': emitted,
                },
                headers={'Referer': REFERER_URL},
            )

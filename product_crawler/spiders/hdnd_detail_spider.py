# -*- coding: utf-8 -*-
"""
Spider crawl trang chi tiết ứng viên: /thong-tin-nguoi-ung-cu/{uuid}

Chạy với URL đơn:
  scrapy crawl hdnd_detail -a url="https://hoidongbaucu.quochoi.vn/thong-tin-nguoi-ung-cu/xxx?lang=vi&khoa=16"

Hoặc file URLs:
  scrapy crawl hdnd_detail -a url_file=output/detail_urls.txt

Hoặc đọc detail_url từ MySQL (bảng hdnd_candidates):
  scrapy crawl hdnd_detail -a from_db=1

Giới hạn: scrapy crawl hdnd_detail -a url_file=... -a limit=10
"""

import re
from urllib.parse import urlparse
import scrapy
from product_crawler.items import CandidateItem

try:
    from product_crawler.config import BASE_URL, DETAIL_PATH, KHOA, DETAIL_FIELD_MAP, DETAIL_URLS_FILE, REFERER_URL
    FIELD_MAP = DETAIL_FIELD_MAP
    DEFAULT_URL_FILE = DETAIL_URLS_FILE
except ImportError:
    BASE_URL = 'https://hoidongbaucu.quochoi.vn'
    DETAIL_PATH = '/thong-tin-nguoi-ung-cu'
    KHOA = 16
    REFERER_URL = 'https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu-hdnd'
    DEFAULT_URL_FILE = 'output/detail_urls.txt'
    FIELD_MAP = {
        'Ngày tháng năm sinh': 'birthdate', 'Giới tính': 'gender', 'Quốc tịch': 'nationality',
        'Dân tộc': 'ethnic', 'Tôn giáo': 'religion', 'Quê quán': 'hometown',
        'Nơi ở hiện nay': 'current_address', 'Giáo dục phổ thông': 'education',
        'Ngoại ngữ': 'foreign_lang', 'Học hàm, học vị': 'degree',
        'Trình độ lý luận chính trị': 'party_theory', 'Chuyên môn nghiệp vụ': 'professional',
        'Nghề nghiệp, chức vụ': 'position', 'Nơi công tác': 'work_place',
        'Ngày vào Đảng': 'party_join_date', 'Đại biểu Quốc hội': 'qh_rep', 'Đại biểu HĐND': 'hdnd_rep',
    }


class HdndDetailSpider(scrapy.Spider):
    """
    Crawl trang chi tiết ứng viên - /thong-tin-nguoi-ung-cu/{uuid}
    """
    
    name = 'hdnd_detail'
    allowed_domains = ['hoidongbaucu.quochoi.vn']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'JSON_OUTPUT_FILE': 'output/hdnd_candidates_detail.json',
    }
    
    def _load_urls_from_db(self):
        """Lấy detail_url từ bảng hdnd_candidates trong MySQL."""
        try:
            from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_HOST, port=MYSQL_PORT, database=MYSQL_DATABASE,
                user=MYSQL_USER, password=MYSQL_PASSWORD, charset='utf8mb4'
            )
            cur = conn.cursor()
            cur.execute("SELECT detail_url FROM hdnd_candidates WHERE detail_url IS NOT NULL AND detail_url != ''")
            urls = [r[0] for r in cur.fetchall() if r[0] and 'thong-tin-nguoi-ung-cu' in r[0]]
            cur.close()
            conn.close()
            self.logger.info('Lay %d URL tu MySQL (hdnd_candidates)', len(urls))
            return urls
        except Exception as e:
            self.logger.error('Khong doc duoc MySQL: %s', e)
            return []

    def start_requests(self):
        urls = []
        # Đọc từ MySQL nếu -a from_db=1
        if getattr(self, 'from_db', None) in ('1', 'true', 'yes', True):
            urls = self._load_urls_from_db()
        if hasattr(self, 'url') and self.url:
            urls.extend(u.strip() for u in self.url.split(',') if u.strip())
        url_file = getattr(self, 'url_file', None) or (DEFAULT_URL_FILE if not urls else None)
        if url_file:
            try:
                with open(url_file, 'r', encoding='utf-8') as f:
                    urls.extend(line.strip() for line in f if line.strip())
            except FileNotFoundError:
                if not urls:
                    self.logger.warning('File %s not found. Use -a url_file=... or -a from_db=1', url_file)
            except Exception as e:
                self.logger.error('Cannot read url_file %s: %s', url_file, e)
        if not urls:
            urls = [f"{BASE_URL}{DETAIL_PATH}/d9cca651-14c8-499a-8550-01cde72ede76?lang=vi&khoa={KHOA}"]
            self.logger.info('Using default URL. Pass -a url=... or -a url_file=... for more.')
        limit = getattr(self, 'limit', None)
        if limit is not None:
            try:
                limit = int(limit)
                urls = urls[:limit]
                self.logger.info('Limit=%d: crawl first %d URL(s)', limit, len(urls))
            except (ValueError, TypeError):
                pass
        self.logger.info('Scheduling %d URL(s) to crawl', len(urls))
        for url in urls:
            if url and 'thong-tin-nguoi-ung-cu' in url:
                yield scrapy.Request(url, callback=self.parse_detail, headers={'Referer': REFERER_URL})
    
    def parse_detail(self, response):
        """Parse trang chi tiết ứng viên."""
        body = response.text
        # Anti-bot: trang set cookie D1N qua JS - request lai voi cookie
        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                d1n = m.group(1)
                self.logger.info('Nhan cookie D1N, request lai: %s', response.url[:60])
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_detail,
                    headers={'Referer': REFERER_URL},
                    cookies={'D1N': d1n},
                    dont_filter=True,
                )
                return

        # UUID từ URL
        path = urlparse(response.url).path
        uuid_match = re.search(r'thong-tin-nguoi-ung-cu/([a-f0-9\-]+)', path, re.I)
        candidate_uuid = uuid_match.group(1) if uuid_match else ''
        
        # Tên - h5.vice-chair-name hoặc h5/h6 (tránh "Khóa XVI")
        name = (response.css('h5.vice-chair-name::text').get() or '').strip()
        if not name:
            for h in response.css('h5::text, h6::text').getall():
                h = (h or '').strip()
                if h and len(h) > 3 and 'khóa' not in h.lower() and 'xvi' not in h.lower():
                    name = h
                    break
        if not name:
            name = (response.css('h1::text, h2::text, h3::text, h4::text').get() or '').strip()
        
        # Ảnh - ưu tiên ảnh thật (viettelcloud/ctt-baucu/Files), loại trừ Quốc huy
        image_url = None
        for img in response.css('img[src]'):
            src = img.css('::attr(src)').get() or ''
            if not src or 'QuocHuy' in src:
                continue
            if 'viettelcloud' in src or 'ctt-baucu' in src or 'Files' in src:
                image_url = src
                break
        if not image_url:
            image_url = response.css('.dai-bieu-avatar img::attr(src), .chu-tich-avatar img::attr(src)').get()
        if not image_url:
            image_url = response.css('img[src*="avatar"]::attr(src), img[src*="/images/"]::attr(src)').get()
        if image_url:
            if not image_url.startswith('http'):
                image_url = 'https:' + image_url if image_url.startswith('//') else response.urljoin(image_url)
        
        # Parse từ grid Bootstrap: .vice-chair-info .row.g-0 > div.col-3/col-9 (fw-bold = label, kế tiếp = value)
        data = {}
        cells = response.css('.vice-chair-info div.row.g-0 div[class*="col-"]')
        if not cells:
            cells = response.css('.modal-body div.row.g-0 div[class*="col-"]')
        if cells:
            i = 0
            while i < len(cells):
                el = cells[i]
                cls = el.css('::attr(class)').get() or ''
                txt = ''.join(el.css('::text').getall()).strip().rstrip(':')
                if 'fw-bold' in cls and txt:
                    if i + 1 < len(cells):
                        val = ''.join(cells[i + 1].css('::text').getall()).strip()
                        if val:
                            field = FIELD_MAP.get(txt.strip())
                            if field:
                                data[field] = re.sub(r'\s+', ' ', val)
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
        
        # Luôn chạy regex để bổ sung/bắt lại (chữ "Label:\nValue" trong HTML)
        body_text = '\n'.join(response.css('body *::text').getall() or [])
        if len(body_text) < 200:
            body_text = response.text  # Fallback: raw HTML khi cấu trúc khác
        for label, field in FIELD_MAP.items():
            m = re.search(rf'{re.escape(label)}\s*:\s*(.+?)(?=\n[A-ZĂÂĐÊÔƠƯ]\w|\n\n|$)', body_text, re.S | re.U)
            if not m:
                m = re.search(rf'{re.escape(label)}\s*:\s*([^\n]+)', body_text)
            if m:
                val = re.sub(r'\s+', ' ', m.group(1).strip())
                if val and len(val) > 1:
                    data[field] = val
        if not data.get('birthdate') and ('Ngày' in body_text or 'sinh' in body_text):
            m = re.search(r'(\d{2}/\d{2}/\d{4})', body_text)
            if m:
                data['birthdate'] = m.group(1)
        
        # Build item
        item = CandidateItem(
            name=name,
            province='',
            party='',
            constituency='',
            description=data.get('position', ''),
            detail_url=response.url,
            candidate_id='',
            candidate_uuid=candidate_uuid,
            position=data.get('position', ''),
            birthdate=data.get('birthdate', ''),
            hometown=data.get('hometown', ''),
            gender=data.get('gender', ''),
            nationality=data.get('nationality', ''),
            ethnic=data.get('ethnic', ''),
            religion=data.get('religion', ''),
            current_address=data.get('current_address', ''),
            education=data.get('education', ''),
            foreign_lang=data.get('foreign_lang', ''),
            degree=data.get('degree', ''),
            party_theory=data.get('party_theory', ''),
            professional=data.get('professional', ''),
            work_place=data.get('work_place', ''),
            party_join_date=data.get('party_join_date', ''),
            qh_rep=data.get('qh_rep', ''),
            hdnd_rep=data.get('hdnd_rep', ''),
            image_url=image_url or '',
        )
        yield item

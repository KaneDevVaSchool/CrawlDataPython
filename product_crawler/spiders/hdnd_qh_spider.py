# -*- coding: utf-8 -*-
"""
Spider crawl danh sách ứng cử Quốc hội từ hoidongbaucu.quochoi.vn

Quy trình:
1. API: get-chi-tiet-danh-sach-ung-cu → lấy danh sách + UUID từng ứng viên
2. Trang chi tiết: /thong-tin-nguoi-ung-cu/{uuid} → lấy thông tin đầy đủ

Lưu: hdnd_qh_candidates (danh sách), hdnd_qh_detail_info (chi tiết)

Chạy:
  scrapy crawl hdnd_qh
  scrapy crawl hdnd_qh -a source=0 -a limit=5
"""

import re
from urllib.parse import urljoin
import scrapy
from product_crawler.items import CandidateItem
from product_crawler.hdnd_crawl_support import (
    QuochoiHdndMixin,
    build_raw_data_meta,
    merge_list_into_item_fields,
    sanitize_parsed_detail,
)

try:
    from product_crawler.config import (
        BASE_URL, DETAIL_PATH, REFERER_URL, KHOA, PAGE_SIZE,
        QH_API_PATH, QH_REFERER_URL, QH_SOURCES, DETAIL_FIELD_MAP,
    )
    FIELD_MAP = DETAIL_FIELD_MAP
except ImportError:
    BASE_URL = 'https://hoidongbaucu.quochoi.vn'
    DETAIL_PATH = '/thong-tin-nguoi-ung-cu'
    REFERER_URL = 'https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu'
    KHOA = 16
    PAGE_SIZE = 300
    QH_API_PATH = '/get-chi-tiet-danh-sach-ung-cu'
    QH_REFERER_URL = REFERER_URL
    QH_SOURCES = [{"name": "Thành phố Hà Nội", "province_id": "08497e01-0003-44b1-f9c6-08ddb2649d30", "khoa": 16}]
    FIELD_MAP = {
        'Ngày tháng năm sinh': 'birthdate', 'Giới tính': 'gender', 'Quốc tịch': 'nationality',
        'Dân tộc': 'ethnic', 'Tôn giáo': 'religion', 'Quê quán': 'hometown',
        'Nơi ở hiện nay': 'current_address', 'Giáo dục phổ thông': 'education',
        'Ngoại ngữ': 'foreign_lang', 'Học hàm, học vị': 'degree',
        'Trình độ lý luận chính trị': 'party_theory', 'Chuyên môn nghiệp vụ': 'professional',
        'Nghề nghiệp, chức vụ': 'position', 'Nơi công tác': 'work_place',
        'Ngày vào Đảng': 'party_join_date', 'Đại biểu Quốc hội': 'qh_rep', 'Đại biểu HĐND': 'hdnd_rep',
    }


class HdndQhSpider(QuochoiHdndMixin, scrapy.Spider):
    """
    Crawl danh sách ứng cử Quốc hội → chi tiết từng ứng viên.
    Lưu vào hdnd_qh_candidates và hdnd_qh_detail_info.
    """

    name = 'hdnd_qh'
    allowed_domains = ['hoidongbaucu.quochoi.vn']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS': 20,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 6.0,
        'AUTOTHROTTLE_START_DELAY': 0.2,
        'AUTOTHROTTLE_MAX_DELAY': 2.0,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'JSON_OUTPUT_FILE': 'output/hdnd_qh_candidates.json',
    }

    def start_requests(self):
        sources = QH_SOURCES or []
        source_arg = getattr(self, 'source', None)
        if source_arg is not None:
            try:
                idx = int(source_arg)
                sources = [sources[idx]] if 0 <= idx < len(sources) else sources
            except (ValueError, TypeError):
                name = str(source_arg).strip().lower()
                sources = [s for s in sources if name in (s.get('name') or '').lower()]
            if sources:
                self.logger.info('Chạy 1 nguồn: %s', sources[0].get('name'))

        for src in sources:
            province_name = src.get('name', '')
            province_id = src.get('province_id') or src.get('tinh_thanh_id', '')
            khoa = src.get('khoa', KHOA)
            if not province_id:
                continue
            url = (
                f"{BASE_URL}{QH_API_PATH}"
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
                headers={'Referer': QH_REFERER_URL},
            )

    def parse_table(self, response):
        """Parse bảng danh sách ứng viên QH."""
        province = response.meta.get('province', '')
        tinh_thanh_id = response.meta.get('tinh_thanh_id', '')
        khoa = response.meta.get('khoa', KHOA)
        page = response.meta.get('page', 1)
        body = response.text

        # Anti-bot: cookie D1N
        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                self.logger.info('[%s] Nhận cookie D1N, request lại...', province)
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_table,
                    meta=response.meta,
                    headers={'Referer': QH_REFERER_URL},
                    cookies={'D1N': m.group(1)},
                    dont_filter=True,
                )
                return

        total_match = re.search(r'Tổng\s*số\s*[:\=]?\s*(\d+)', body, re.I | re.U)
        total = int(total_match.group(1)) if total_match else 0

        title_match = re.search(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', body, re.I)
        if title_match:
            t = title_match.group(1).strip()
            if t and 'lỗi' not in t.lower():
                province = t

        rows = response.css('tr[data-id], tr.card-nguoi-ung-cu')
        if not rows:
            rows = response.css('table tr, tbody tr')

        list_limit = getattr(self, 'limit', None) or getattr(self, 'list_limit', None)
        try:
            list_limit = int(list_limit) if list_limit is not None else None
        except (ValueError, TypeError):
            list_limit = None
        emitted = response.meta.get('emitted', 0)

        for i, row in enumerate(rows):
            cells = row.css('td, th')
            texts = [c.css('::text').getall() for c in cells]
            cell_values = [''.join(t).strip() if t else '' for t in texts]

            if i == 0 and cell_values:
                first = (cell_values[0] or '').strip().upper()
                second = (cell_values[1] or '').strip().upper()[:20]
                if first == 'STT' or second.startswith('HỌ') or second.startswith('HỌ VÀ'):
                    continue

            if len(cell_values) < 2:
                continue

            stt = cell_values[0] if len(cell_values) > 0 else ''
            name = cell_values[1] if len(cell_values) > 1 else ''
            position = cell_values[2] if len(cell_values) > 2 else ''
            birthdate = cell_values[3] if len(cell_values) > 3 else ''
            hometown = cell_values[4] if len(cell_values) > 4 else ''

            if not name or name.upper().startswith('HỌ') or name.upper().startswith('STT'):
                continue

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
                    uuid_m = re.search(r'thong-tin-nguoi-ung-cu/([a-f0-9\-]+)', detail_link, re.I)
                    if uuid_m:
                        candidate_uuid = uuid_m.group(1)

            if candidate_uuid:
                detail_url = f"{BASE_URL}{DETAIL_PATH}/{candidate_uuid}?lang=vi&khoa={khoa}"
            else:
                detail_url = urljoin(response.url, row.css('a::attr(href)').get() or '') or ''

            # Yield list item (pipeline -> hdnd_qh_candidates)
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

            # Request detail page (pipeline -> hdnd_qh_detail_info)
            if detail_url and 'thong-tin-nguoi-ung-cu' in detail_url:
                list_snap = {
                    'stt': stt,
                    'list_name': name,
                    'list_position': position,
                    'list_birthdate': birthdate,
                    'list_hometown': hometown,
                    'cells': cell_values,
                }
                yield scrapy.Request(
                    detail_url,
                    callback=self.parse_detail,
                    meta={
                        'province': province,
                        'constituency': '',
                        'khoa': khoa,
                        'list_snapshot': list_snap,
                    },
                    headers={'Referer': QH_REFERER_URL},
                )

            if list_limit and emitted >= list_limit:
                self.logger.info('[%s] Đạt limit=%d', province, list_limit)
                return

        # Phân trang
        max_page = ((total - 1) // PAGE_SIZE) + 1 if total > 0 else 1
        if page < max_page and tinh_thanh_id and (not list_limit or emitted < list_limit):
            next_url = (
                f"{BASE_URL}{QH_API_PATH}"
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
                headers={'Referer': QH_REFERER_URL},
            )

    def parse_detail(self, response):
        """Parse trang chi tiết ứng viên."""
        from urllib.parse import urlparse

        body = response.text
        province = response.meta.get('province', '')
        constituency = response.meta.get('constituency', '')
        khoa = response.meta.get('khoa', KHOA)

        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_detail,
                    meta=response.meta,
                    headers={'Referer': QH_REFERER_URL},
                    cookies={'D1N': m.group(1)},
                    dont_filter=True,
                )
                return

        path = urlparse(response.url).path
        uuid_match = re.search(r'thong-tin-nguoi-ung-cu/([a-f0-9\-]+)', path, re.I)
        candidate_uuid = uuid_match.group(1) if uuid_match else ''

        name = (response.css('h5.vice-chair-name::text').get() or '').strip()
        if not name:
            for h in response.css('h5::text, h6::text').getall():
                h = (h or '').strip()
                if h and len(h) > 3 and 'khóa' not in h.lower() and 'xvi' not in h.lower():
                    name = h
                    break
        if not name:
            name = (response.css('h1::text, h2::text, h3::text, h4::text').get() or '').strip()

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
        if image_url and not image_url.startswith('http'):
            image_url = 'https:' + image_url if image_url.startswith('//') else response.urljoin(image_url)

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
                if 'fw-bold' in cls and txt and FIELD_MAP:
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

        body_text = '\n'.join(response.css('body *::text').getall() or [])
        if len(body_text) < 200:
            body_text = response.text
        if FIELD_MAP:
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

        sanitize_parsed_detail(data)
        if image_url and 'QuocHuy' in image_url:
            image_url = ''

        item = {
            'name': name,
            'province': province,
            'party': '',
            'constituency': constituency,
            'description': data.get('position', ''),
            'detail_url': response.url,
            'candidate_id': '',
            'candidate_uuid': candidate_uuid,
            'position': data.get('position', ''),
            'birthdate': data.get('birthdate', ''),
            'hometown': data.get('hometown', ''),
            'gender': data.get('gender', ''),
            'nationality': data.get('nationality', ''),
            'ethnic': data.get('ethnic', ''),
            'religion': data.get('religion', ''),
            'current_address': data.get('current_address', ''),
            'education': data.get('education', ''),
            'foreign_lang': data.get('foreign_lang', ''),
            'degree': data.get('degree', ''),
            'party_theory': data.get('party_theory', ''),
            'professional': data.get('professional', ''),
            'work_place': data.get('work_place', ''),
            'party_join_date': data.get('party_join_date', ''),
            'qh_rep': data.get('qh_rep', ''),
            'hdnd_rep': data.get('hdnd_rep', ''),
            'image_url': image_url or '',
        }
        merge_list_into_item_fields(item, response.meta.get('list_snapshot'))
        item['raw_data'] = build_raw_data_meta(response.meta, response.meta.get('list_snapshot'))
        yield CandidateItem(**item)

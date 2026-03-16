# -*- coding: utf-8 -*-
"""
Spider crawl danh sách ứng cử HĐND cấp xã từ hoidongbaucu.quochoi.vn

Quy trình:
1. Trang chính: get-danh-sach-ung-cu-hdnd-cap-xa → lấy link "Xem thêm" từng xã/phường
2. Trang xã: chi-tiet-danh-sach-ung-cu-hdnd-cap-xa → lấy link chi tiết ứng viên
3. Trang chi tiết: thong-tin-nguoi-ung-cu/{uuid} → lấy toàn bộ thông tin

Chạy:
  scrapy crawl hdnd_xa
  scrapy crawl hdnd_xa -a source=0 -a limit=5   # Giới hạn 5 xã, 5 ứng viên/xã
"""

import re
from urllib.parse import urljoin
import scrapy
from product_crawler.items import CandidateItem

try:
    from product_crawler.config import (
        BASE_URL, DETAIL_PATH, REFERER_URL, KHOA,
        HDND_XA_SOURCES, DETAIL_FIELD_MAP,
    )
    FIELD_MAP = DETAIL_FIELD_MAP
except ImportError:
    BASE_URL = 'https://hoidongbaucu.quochoi.vn'
    DETAIL_PATH = '/thong-tin-nguoi-ung-cu'
    REFERER_URL = 'https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu-hdnd'
    KHOA = 16
    HDND_XA_SOURCES = [{
        "name": "Bến Tre",
        "tinh_thanh_id": "8fcfe1bb-81ce-4abe-f9da-08ddb2649d30",
        "khoa": 16,
    }]
    FIELD_MAP = {
        'Ngày tháng năm sinh': 'birthdate', 'Giới tính': 'gender', 'Quốc tịch': 'nationality',
        'Dân tộc': 'ethnic', 'Tôn giáo': 'religion', 'Quê quán': 'hometown',
        'Nơi ở hiện nay': 'current_address', 'Giáo dục phổ thông': 'education',
        'Ngoại ngữ': 'foreign_lang', 'Học hàm, học vị': 'degree',
        'Trình độ lý luận chính trị': 'party_theory', 'Chuyên môn nghiệp vụ': 'professional',
        'Nghề nghiệp, chức vụ': 'position', 'Nơi công tác': 'work_place',
        'Ngày vào Đảng': 'party_join_date', 'Đại biểu Quốc hội': 'qh_rep', 'Đại biểu HĐND': 'hdnd_rep',
    }


class HdndXaSpider(scrapy.Spider):
    """
    Crawl HĐND cấp xã: Danh sách xã → Chi tiết xã → Chi tiết ứng viên.
    """

    name = 'hdnd_xa'
    allowed_domains = ['hoidongbaucu.quochoi.vn']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'JSON_OUTPUT_FILE': 'output/hdnd_xa_candidates.json',
    }

    LIST_XA_API = '/get-danh-sach-ung-cu-hdnd-cap-xa'
    CHI_TIET_XA_PATH = '/chi-tiet-danh-sach-ung-cu-hdnd-cap-xa'
    # API trả về HTML danh sách ứng viên (AJAX), dùng thay vì trang chi-tiet
    CHI_TIET_XA_API = '/get-chi-tiet-danh-sach-ung-cu-hdnd-cap-xa'

    def start_requests(self):
        sources = HDND_XA_SOURCES or []
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
            tinh_id = src.get('tinh_thanh_id', '')
            khoa = src.get('khoa', KHOA)
            if not tinh_id:
                continue
            url = (
                f"{BASE_URL}{self.LIST_XA_API}"
                f"?lang=vi&tinhThanhKhoaId={tinh_id}&khoa={khoa}&pageNumber=1"
            )
            yield scrapy.Request(
                url,
                callback=self.parse_list_xa,
                meta={
                    'province': province_name,
                    'tinh_thanh_id': tinh_id,
                    'khoa': khoa,
                    'page_number': 1,
                },
                headers={'Referer': REFERER_URL},
            )

    def parse_list_xa(self, response):
        """Parse trang danh sách xã/phường → lấy link Xem thêm từng xã. Hỗ trợ phân trang pageNumber."""
        body = response.text
        province = response.meta.get('province', '')
        tinh_id = response.meta.get('tinh_thanh_id', '')
        khoa = response.meta.get('khoa', KHOA)
        page_num = response.meta.get('page_number', 1)

        # Anti-bot: cookie D1N
        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                self.logger.info('[%s] Nhận cookie D1N, request lại...', province)
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_list_xa,
                    meta=response.meta,
                    headers={'Referer': REFERER_URL},
                    cookies={'D1N': m.group(1)},
                    dont_filter=True,
                )
                return

        # Lấy tất cả link "Xem thêm" (chi-tiet-danh-sach-ung-cu-hdnd-cap-xa)
        commune_selectors = response.css(
            f'a.more-btn[href*="chi-tiet-danh-sach-ung-cu-hdnd-cap-xa"], '
            f'a[href*="chi-tiet-danh-sach-ung-cu-hdnd-cap-xa"]'
        )
        if not commune_selectors:
            hrefs = response.css('a::attr(href)').re(
                r'(/[^"\'<>]*chi-tiet-danh-sach-ung-cu-hdnd-cap-xa[^"\'<>]*)'
            )
            commune_links = [{'href': h, 'el': None} for h in set(hrefs)]
        else:
            commune_links = [{'el': sel, 'href': sel.css('::attr(href)').get()} for sel in commune_selectors]

        # Map section -> commune name (h2 trước link)
        sections = response.css('section, .card, div[class*="commune"]')
        limit_xa = getattr(self, 'limit', None) or getattr(self, 'limit_xa', None)
        try:
            limit_xa = int(limit_xa) if limit_xa is not None else None
        except (ValueError, TypeError):
            limit_xa = None

        seen_urls = set()
        count = 0
        for item in commune_links:
            href = (item.get('href') or '').replace('&amp;', '&')
            el = item.get('el')
            commune_name = ''
            if el is not None:
                commune_name = (
                    el.xpath('preceding::h2[1]/text()').get() or
                    el.xpath('preceding::h3[1]/text()').get() or
                    ''
                ).strip()
            if not href or 'chi-tiet-danh-sach-ung-cu-hdnd-cap-xa' not in href:
                continue
            url = urljoin(response.url, href)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            count += 1
            if limit_xa and count > limit_xa:
                self.logger.info('[%s] Đạt limit_xa=%d', province, limit_xa)
                break
            # Trích xaPhuongKhoaId từ URL để gọi API (API trả HTML, trang chi-tiet chỉ load qua AJAX)
            xa_id_m = re.search(r'xaPhuongKhoaId=([a-f0-9\-]+)', url, re.I)
            xa_phuong_id = xa_id_m.group(1) if xa_id_m else ''
            api_url = (
                f"{BASE_URL}{self.CHI_TIET_XA_API}"
                f"?lang=vi&tinhThanhKhoaId={tinh_id}&xaPhuongKhoaId={xa_phuong_id}&khoa={khoa}"
            )
            yield scrapy.Request(
                api_url,
                callback=self.parse_chi_tiet_xa,
                meta={
                    'province': province,
                    'commune': commune_name,
                    'tinh_thanh_id': tinh_id,
                    'xa_phuong_id': xa_phuong_id,
                    'khoa': khoa,
                    'commune_url': url,
                },
                headers={'Referer': REFERER_URL},
            )

        # Phân trang danh sách xã: ~5 xã/trang, request trang tiếp khi đủ 1 trang
        if seen_urls and count >= 5 and (not limit_xa or count < limit_xa):
            next_url = (
                f"{BASE_URL}{self.LIST_XA_API}"
                f"?lang=vi&tinhThanhKhoaId={tinh_id}&khoa={khoa}&pageNumber={page_num + 1}"
            )
            yield scrapy.Request(
                next_url,
                callback=self.parse_list_xa,
                meta={
                    'province': province,
                    'tinh_thanh_id': tinh_id,
                    'khoa': khoa,
                    'page_number': page_num + 1,
                },
                headers={'Referer': REFERER_URL},
            )

        if not seen_urls:
            # Fallback: regex tìm href trong HTML
            for m in re.finditer(
                r'href=["\']([^"\']*chi-tiet-danh-sach-ung-cu-hdnd-cap-xa[^"\']*)["\']',
                body, re.I
            ):
                href = m.group(1).replace('&amp;', '&')
                url = urljoin(response.url, href)
                if url in seen_urls:
                    continue
                xa_id_m = re.search(r'xaPhuongKhoaId=([a-f0-9\-]+)', url, re.I)
                xa_phuong_id = xa_id_m.group(1) if xa_id_m else ''
                if not xa_phuong_id:
                    continue
                seen_urls.add(url)
                count += 1
                if limit_xa and count > limit_xa:
                    break
                api_url = (
                    f"{BASE_URL}{self.CHI_TIET_XA_API}"
                    f"?lang=vi&tinhThanhKhoaId={tinh_id}&xaPhuongKhoaId={xa_phuong_id}&khoa={khoa}"
                )
                yield scrapy.Request(
                    api_url,
                    callback=self.parse_chi_tiet_xa,
                    meta={
                        'province': province,
                        'commune': '',
                        'tinh_thanh_id': tinh_id,
                        'xa_phuong_id': xa_phuong_id,
                        'khoa': khoa,
                        'commune_url': url,
                    },
                    headers={'Referer': REFERER_URL},
                )

    def parse_chi_tiet_xa(self, response):
        """Parse trang chi tiết xã → lấy UUID ứng viên (có phân trang pageNumber)."""
        body = response.text
        province = response.meta.get('province', '')
        commune = response.meta.get('commune', '')
        khoa = response.meta.get('khoa', KHOA)
        tinh_id = response.meta.get('tinh_thanh_id', '')
        xa_id = response.meta.get('xa_phuong_id', '')
        page_num = response.meta.get('page_number', 1)
        collected = set(response.meta.get('collected_uuids') or [])
        total_from_page = response.meta.get('total_candidates')

        if 'document.cookie' in body and 'D1N=' in body:
            m = re.search(r'D1N=([a-f0-9]+)', body)
            if m:
                yield scrapy.Request(
                    response.url,
                    callback=self.parse_chi_tiet_xa,
                    meta=response.meta,
                    headers={'Referer': REFERER_URL},
                    cookies={'D1N': m.group(1)},
                    dont_filter=True,
                )
                return

        if not commune:
            commune = (
                response.css('.province-title::text').get() or
                response.css('h1::text, h2::text, h3::text, .commune-name::text').get() or
                ''
            ).strip()
        constituency = commune or ''

        # Lấy total từ "Tổng số: N" (chỉ trang 1)
        if page_num == 1:
            total_m = re.search(r'Tổng\s*số\s*[:\s]+(\d+)', body, re.I | re.U)
            total_from_page = int(total_m.group(1)) if total_m else 0

        # Thu thập UUID từ tr[data-id]
        rows = response.css('tr[data-id], tr.card-nguoi-ung-cu')
        for row in rows:
            uuid = row.xpath('@data-id').get()
            if uuid and len(uuid) == 36:
                collected.add(uuid)

        limit_candidate = getattr(self, 'limit_candidate', None)
        try:
            limit_candidate = int(limit_candidate) if limit_candidate else None
        except (ValueError, TypeError):
            limit_candidate = None

        # Phân trang: mặc định ~12 ứng viên/trang, request trang tiếp nếu còn
        page_size = 12
        need_more = total_from_page and len(collected) < min(total_from_page, limit_candidate or 99999)
        if need_more and (page_num * page_size < total_from_page):
            next_page = page_num + 1
            base_url = f"{BASE_URL}{self.CHI_TIET_XA_API}"
            next_url = f"{base_url}?lang=vi&tinhThanhKhoaId={tinh_id}&xaPhuongKhoaId={xa_id}&khoa={khoa}&pageNumber={next_page}"
            yield scrapy.Request(
                next_url,
                callback=self.parse_chi_tiet_xa,
                meta={
                    'province': province,
                    'commune': commune,
                    'tinh_thanh_id': tinh_id,
                    'xa_phuong_id': xa_id,
                    'khoa': khoa,
                    'page_number': next_page,
                    'collected_uuids': collected,
                    'total_candidates': total_from_page,
                },
                headers={'Referer': REFERER_URL},
            )
            return

        # Đã thu thập đủ -> request chi tiết từng ứng viên
        yielded = 0
        for uuid in collected:
            if limit_candidate and yielded >= limit_candidate:
                break
            url = f"{BASE_URL}{DETAIL_PATH}/{uuid}?lang=vi&khoa={khoa}"
            yield scrapy.Request(
                url,
                callback=self.parse_detail,
                meta={
                    'province': province,
                    'constituency': constituency,
                    'khoa': khoa,
                },
                headers={'Referer': REFERER_URL},
            )
            yielded += 1

    def parse_detail(self, response):
        """Parse trang chi tiết ứng viên - lấy toàn bộ thông tin."""
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
                    headers={'Referer': REFERER_URL},
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

        body_text = '\n'.join(response.css('body *::text').getall() or [])
        if len(body_text) < 200:
            body_text = response.text
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

        yield CandidateItem(
            name=name,
            province=province,
            party='',
            constituency=constituency,
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

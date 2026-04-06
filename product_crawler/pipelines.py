# -*- coding: utf-8 -*-
"""
Pipelines module - Process and store scraped items.

Pipelines receive items from spiders and can:
- Validate/clean data
- Remove duplicates
- Store to files or databases
"""

import json
import logging
from datetime import datetime
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


# =============================================================================
# JSON FILE PIPELINE
# =============================================================================

class JsonFilePipeline:
    """
    Stores scraped items into a JSON file.
    
    Supports incremental output - items are appended as they're scraped.
    Uses UTF-8 encoding and proper JSON array formatting.
    """
    
    def __init__(self, output_file):
        self.output_file = output_file
        self.items = []
    
    @classmethod
    def from_crawler(cls, crawler):
        """Factory - get output filename from settings."""
        output_file = crawler.settings.get(
            'JSON_OUTPUT_FILE',
            'output/products_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        return cls(output_file)
    
    def open_spider(self, spider):
        """Called when spider opens - prepare for writing."""
        self.items = []
    
    def process_item(self, item, spider):
        """Add item to the collection. Skip HDND - chi luu vao MySQL."""
        if spider.name in ('hdnd_candidates', 'hdnd_detail', 'hdnd_xa', 'hdnd_qh', 'hdnd_tc_xa'):
            return item
        self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        """Write all items to JSON file when spider closes."""
        if spider.name in ('hdnd_candidates', 'hdnd_detail', 'hdnd_xa', 'hdnd_qh', 'hdnd_tc_xa'):
            return
        import os
        os.makedirs(os.path.dirname(self.output_file) or '.', exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        spider.logger.info('Saved %d items to %s' % (len(self.items), self.output_file))


# =============================================================================
# MYSQL DATABASE PIPELINE
# =============================================================================

class MySQLPipeline:
    """
    Stores scraped items into a MySQL database.
    
    Requires: pip install mysqlclient (or PyMySQL)
    Configure DB credentials in settings.py
    """
    
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
    
    @classmethod
    def from_crawler(cls, crawler):
        """Factory - get DB config from settings."""
        return cls(
            host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            port=crawler.settings.get('MYSQL_PORT', 3306),
            database=crawler.settings.get('MYSQL_DATABASE', 'scrapy_products'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '')
        )
    
    def open_spider(self, spider):
        """Establish MySQL connection and create table if not exists (chỉ với spider products)."""
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
            # Không tạo bảng products - chỉ dùng HDND
        except ImportError:
            spider.logger.warning(
                'PyMySQL not installed. Run: pip install pymysql'
            )
        except Exception as e:
            spider.logger.error('MySQL connection failed: %s' % e)
    
    def _create_table(self):
        """Create products table if it doesn't exist.
        Note: product_url max 767 chars (utf8mb4) to satisfy InnoDB key length limit (3072 bytes).
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500),
                price VARCHAR(100),
                description TEXT,
                image_url VARCHAR(1000),
                product_url VARCHAR(767) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
    
    def process_item(self, item, spider=None):
        """Insert or update item in database (ProductItem only)."""
        if not self.connection:
            return item
        adapter = ItemAdapter(item)
        if not adapter.get('product_url'):
            return item  # Skip non-product items (e.g. CandidateItem)
        product_url = adapter.get('product_url') or ''
        if len(product_url) > 767:
            product_url = product_url[:767]
        try:
            self.cursor.execute("""
                INSERT INTO products (title, price, description, image_url, product_url)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    price = VALUES(price),
                    description = VALUES(description),
                    image_url = VALUES(image_url)
            """, (
                adapter.get('title'),
                adapter.get('price'),
                adapter.get('description'),
                adapter.get('image_url'),
                product_url
            ))
            self.connection.commit()
        except Exception as e:
            logger.error('MySQL insert error: %s', e)
            self.connection.rollback()
        
        return item
    
    def close_spider(self, spider):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


# =============================================================================
# DETAIL URLS FILE PIPELINE (cho hdnd_candidates - ghi link chi tiết để crawl sau)
# =============================================================================

class DetailUrlsFilePipeline:
    """Thu thập detail_url từ hdnd_candidates, ghi ra file để chạy hdnd_detail."""

    def __init__(self, output_file):
        self.output_file = output_file
        self.urls = set()

    @classmethod
    def from_crawler(cls, crawler):
        try:
            from product_crawler.config import DETAIL_URLS_FILE
            default_file = DETAIL_URLS_FILE
        except ImportError:
            default_file = 'output/detail_urls.txt'
        output_file = crawler.settings.get('DETAIL_URLS_FILE', default_file)
        return cls(output_file)

    def open_spider(self, spider):
        self.urls = set()

    def process_item(self, item, spider):
        if spider.name != 'hdnd_candidates':
            return item
        adapter = ItemAdapter(item)
        url = adapter.get('detail_url') or ''
        if url and 'thong-tin-nguoi-ung-cu' in url:
            self.urls.add(url)
        return item

    def close_spider(self, spider):
        if spider.name != 'hdnd_candidates' or not self.urls:
            return
        import os
        os.makedirs(os.path.dirname(self.output_file) or '.', exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(self.urls)))
        spider.logger.info('Ghi %d link chi tiết vào %s', len(self.urls), self.output_file)


# =============================================================================
# CANDIDATE JSON PIPELINE (hdnd_xa, hdnd_detail -> JSON)
# =============================================================================

class CandidateJsonPipeline:
    """Ghi CandidateItem từ hdnd_xa, hdnd_detail ra file JSON."""

    def __init__(self, output_file):
        self.output_file = output_file
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get(
            'JSON_OUTPUT_FILE',
            'output/hdnd_xa_candidates.json'
        )
        return cls(output_file)

    def open_spider(self, spider):
        self.items = []

    def process_item(self, item, spider):
        if spider.name not in ('hdnd_xa', 'hdnd_detail', 'hdnd_qh', 'hdnd_tc_xa'):
            return item
        if hasattr(item, 'keys') and 'name' in item:
            self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        if spider.name not in ('hdnd_xa', 'hdnd_detail', 'hdnd_qh', 'hdnd_tc_xa') or not self.items:
            return
        import os
        os.makedirs(os.path.dirname(self.output_file) or '.', exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        spider.logger.info('Đã ghi %d ứng viên vào %s', len(self.items), self.output_file)


# =============================================================================
# DUPLICATE FILTER PIPELINE
# =============================================================================

class DuplicateFilterPipeline:
    """
    Drops duplicate items based on product_url, candidate_id, or detail_url.
    
    Uses an in-memory set to track seen keys. For production at scale,
    consider using Redis or a database for persistent deduplication.
    """
    
    def __init__(self):
        self.seen_keys = set()
    
    def _get_dedup_key(self, adapter):
        """Get unique key for deduplication."""
        # Product: product_url
        if adapter.get('product_url'):
            return 'product:' + str(adapter.get('product_url'))
        # Candidate list item (có candidate_id/STT) -> dùng province|candidate_id để không trùng key với detail
        if adapter.get('province') and adapter.get('candidate_id'):
            return 'candidate_list:' + str(adapter.get('province')) + '|' + str(adapter.get('candidate_id'))
        # Candidate detail: detail_url hoặc candidate_uuid (trang chi tiết)
        if adapter.get('detail_url'):
            return 'candidate:' + str(adapter.get('detail_url'))
        if adapter.get('candidate_uuid'):
            return 'candidate:' + str(adapter.get('candidate_uuid'))
        # Fallback: province + name + birthdate
        if adapter.get('province') and adapter.get('name'):
            return 'candidate:' + str(adapter.get('province')) + '|' + str(adapter.get('name')) + '|' + str(adapter.get('birthdate', ''))
        for key in ('detail_url',):
            val = adapter.get(key)
            if val:
                return str(val)
        return str(adapter.asdict())
    
    def process_item(self, item, spider):
        """Drop item if key was already seen."""
        adapter = ItemAdapter(item)
        key = self._get_dedup_key(adapter)
        if key in self.seen_keys:
            raise DropItem('Duplicate item: %s' % key[:100])
        self.seen_keys.add(key)
        return item


# =============================================================================
# CANDIDATE MYSQL PIPELINE
# =============================================================================

class CandidateMySQLPipeline:
    """
    Stores CandidateItem into MySQL.
    - hdnd_candidates: danh sách + link (detail_url, candidate_uuid)
    - hdnd_detail_info: thông tin chi tiết (liên kết qua candidate_uuid)
    """

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        self._current_spider = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            port=crawler.settings.get('MYSQL_PORT', 3306),
            database=crawler.settings.get('MYSQL_DATABASE', 'scrapy_products'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '')
        )

    def open_spider(self, spider):
        self._current_spider = spider
        if spider.name not in ('hdnd_candidates', 'hdnd_detail', 'hdnd_xa'):
            return
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=self.password, charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
            self._create_tables()
            self._ensure_detail_columns()
        except ImportError:
            spider.logger.warning('PyMySQL not installed.')
        except Exception as e:
            spider.logger.error('MySQL connection failed: %s' % e)

    def _create_tables(self):
        # Bảng 1: Danh sách + link
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_candidates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                province VARCHAR(255),
                party VARCHAR(255),
                constituency VARCHAR(500),
                description TEXT,
                detail_url VARCHAR(767),
                candidate_id VARCHAR(100),
                candidate_uuid VARCHAR(100),
                position VARCHAR(500),
                birthdate VARCHAR(50),
                hometown VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_detail_url (detail_url),
                INDEX idx_province (province),
                INDEX idx_candidate_id (candidate_id),
                INDEX idx_candidate_uuid (candidate_uuid)
            )
        """)
        self.connection.commit()
        # Bảng 2: Chi tiết (1-1 với candidate qua candidate_uuid)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_detail_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_detail_url (detail_url)
            )
        """)
        self.connection.commit()

    def _ensure_detail_columns(self):
        """Thêm cột province, constituency vào hdnd_detail_info nếu chưa có (migration)."""
        for col, spec in [('province', 'VARCHAR(255)'), ('constituency', 'VARCHAR(500)')]:
            try:
                self.cursor.execute(
                    f"ALTER TABLE hdnd_detail_info ADD COLUMN {col} {spec}"
                )
                self.connection.commit()
            except Exception as e:
                if 'Duplicate column' not in str(e):
                    logger.warning('ALTER hdnd_detail_info: %s', e)

    def process_item(self, item, spider=None):
        spider = spider or self._current_spider
        if spider and spider.name not in ('hdnd_candidates', 'hdnd_detail', 'hdnd_xa'):
            return item
        adapter = ItemAdapter(item)
        if not adapter.get('name') and not adapter.get('candidate_id') and not adapter.get('detail_url'):
            return item
        if not self.connection:
            return item
        try:
            detail_url = (adapter.get('detail_url') or '')[:767] or None
            cid = (adapter.get('candidate_id') or '')[:100] or None
            cuuid = (adapter.get('candidate_uuid') or '')[:100] or None

            # Phân biệt detail (từ hdnd_detail) vs list (từ hdnd_candidates). hdnd_xa -> HdndXaMySQLPipeline
            is_detail = (spider and spider.name == 'hdnd_detail') or (
                adapter.get('detail_url') and 'thong-tin-nguoi-ung-cu' in str(adapter.get('detail_url', ''))
                and (adapter.get('gender') or adapter.get('education') or adapter.get('work_place'))
            )
            if is_detail:
                # Chi tiết -> bảng hdnd_detail_info (UPDATE hoặc INSERT)
                if not cuuid:
                    cuuid = adapter.get('detail_url', '')[:100] or 'unknown'
                self.cursor.execute("""
                    INSERT INTO hdnd_detail_info
                    (candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                     gender, nationality, ethnic, religion, current_address,
                     education, foreign_lang, degree, party_theory, professional,
                     work_place, party_join_date, qh_rep, hdnd_rep, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        detail_url=VALUES(detail_url), province=VALUES(province), constituency=VALUES(constituency),
                        name=VALUES(name), birthdate=VALUES(birthdate),
                        position=VALUES(position), hometown=VALUES(hometown),
                        gender=VALUES(gender), nationality=VALUES(nationality), ethnic=VALUES(ethnic),
                        religion=VALUES(religion), current_address=VALUES(current_address),
                        education=VALUES(education), foreign_lang=VALUES(foreign_lang),
                        degree=VALUES(degree), party_theory=VALUES(party_theory),
                        professional=VALUES(professional), work_place=VALUES(work_place),
                        party_join_date=VALUES(party_join_date), qh_rep=VALUES(qh_rep),
                        hdnd_rep=VALUES(hdnd_rep), image_url=VALUES(image_url)
                """, (
                    cuuid, detail_url,
                    (adapter.get('province') or '')[:255],
                    (adapter.get('constituency') or '')[:500],
                    adapter.get('name'), adapter.get('birthdate') or '',
                    (adapter.get('position') or '')[:500], (adapter.get('hometown') or '')[:500],
                    (adapter.get('gender') or '')[:50], (adapter.get('nationality') or '')[:100],
                    (adapter.get('ethnic') or '')[:100], (adapter.get('religion') or '')[:100],
                    (adapter.get('current_address') or '')[:500],
                    (adapter.get('education') or '')[:255], (adapter.get('foreign_lang') or '')[:255],
                    (adapter.get('degree') or '')[:255], (adapter.get('party_theory') or '')[:255],
                    (adapter.get('professional') or '')[:500], (adapter.get('work_place') or '')[:500],
                    (adapter.get('party_join_date') or '')[:50],
                    (adapter.get('qh_rep') or '')[:255], (adapter.get('hdnd_rep') or '')[:255],
                    (adapter.get('image_url') or '')[:1000]
                ))
            else:
                # Danh sách -> bảng hdnd_candidates
                self.cursor.execute("""
                    INSERT INTO hdnd_candidates
                    (name, province, party, constituency, description, detail_url, candidate_id, candidate_uuid, position, birthdate, hometown)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    adapter.get('name'), adapter.get('province'), adapter.get('party'),
                    adapter.get('constituency'), adapter.get('description'),
                    detail_url, cid, cuuid,
                    (adapter.get('position') or '')[:500],
                    adapter.get('birthdate') or '',
                    (adapter.get('hometown') or '')[:500]
                ))
            self.connection.commit()
        except Exception as e:
            logger.error('Candidate MySQL error: %s', e)
            self.connection.rollback()
        return item
    
    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


# =============================================================================
# QUỐC HỘI - hdnd_qh_candidates + hdnd_qh_detail_info
# =============================================================================

class HdndQhMySQLPipeline:
    """Lưu CandidateItem từ spider hdnd_qh: danh sách -> hdnd_qh_candidates, chi tiết -> hdnd_qh_detail_info."""

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        self._current_spider = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            port=crawler.settings.get('MYSQL_PORT', 3306),
            database=crawler.settings.get('MYSQL_DATABASE', 'scrapy_products'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '')
        )

    def open_spider(self, spider):
        self._current_spider = spider
        if spider.name != 'hdnd_qh':
            return
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=self.password, charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
            self._create_tables()
        except Exception as e:
            spider.logger.error('HdndQh MySQL: %s', e)

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_qh_candidates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                province VARCHAR(255),
                party VARCHAR(255),
                constituency VARCHAR(500),
                description TEXT,
                detail_url VARCHAR(767),
                candidate_id VARCHAR(100),
                candidate_uuid VARCHAR(100),
                position VARCHAR(500),
                birthdate VARCHAR(50),
                hometown VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_detail_url (detail_url),
                INDEX idx_province (province),
                INDEX idx_candidate_uuid (candidate_uuid)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_qh_detail_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_detail_url (detail_url)
            )
        """)
        self.connection.commit()

    def process_item(self, item, spider=None):
        spider = spider or getattr(self, '_current_spider', None)
        if spider and spider.name != 'hdnd_qh':
            return item
        adapter = ItemAdapter(item)
        if not adapter.get('name') and not adapter.get('candidate_id') and not adapter.get('detail_url'):
            return item
        if not self.connection:
            return item
        try:
            detail_url = (adapter.get('detail_url') or '')[:767] or None
            cuuid = (adapter.get('candidate_uuid') or '')[:100] or None
            is_detail = bool(
                adapter.get('gender') or adapter.get('education') or adapter.get('work_place')
            )
            if is_detail:
                if not cuuid:
                    cuuid = (adapter.get('detail_url') or '')[:100] or 'unknown'
                self.cursor.execute("""
                    INSERT INTO hdnd_qh_detail_info
                    (candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                     gender, nationality, ethnic, religion, current_address,
                     education, foreign_lang, degree, party_theory, professional,
                     work_place, party_join_date, qh_rep, hdnd_rep, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        detail_url=VALUES(detail_url), province=VALUES(province), constituency=VALUES(constituency),
                        name=VALUES(name), birthdate=VALUES(birthdate),
                        position=VALUES(position), hometown=VALUES(hometown),
                        gender=VALUES(gender), nationality=VALUES(nationality), ethnic=VALUES(ethnic),
                        religion=VALUES(religion), current_address=VALUES(current_address),
                        education=VALUES(education), foreign_lang=VALUES(foreign_lang),
                        degree=VALUES(degree), party_theory=VALUES(party_theory),
                        professional=VALUES(professional), work_place=VALUES(work_place),
                        party_join_date=VALUES(party_join_date), qh_rep=VALUES(qh_rep),
                        hdnd_rep=VALUES(hdnd_rep), image_url=VALUES(image_url)
                """, (
                    cuuid, detail_url,
                    (adapter.get('province') or '')[:255],
                    (adapter.get('constituency') or '')[:500],
                    adapter.get('name'), adapter.get('birthdate') or '',
                    (adapter.get('position') or '')[:500], (adapter.get('hometown') or '')[:500],
                    (adapter.get('gender') or '')[:50], (adapter.get('nationality') or '')[:100],
                    (adapter.get('ethnic') or '')[:100], (adapter.get('religion') or '')[:100],
                    (adapter.get('current_address') or '')[:500],
                    (adapter.get('education') or '')[:255], (adapter.get('foreign_lang') or '')[:255],
                    (adapter.get('degree') or '')[:255], (adapter.get('party_theory') or '')[:255],
                    (adapter.get('professional') or '')[:500], (adapter.get('work_place') or '')[:500],
                    (adapter.get('party_join_date') or '')[:50],
                    (adapter.get('qh_rep') or '')[:255], (adapter.get('hdnd_rep') or '')[:255],
                    (adapter.get('image_url') or '')[:1000]
                ))
            else:
                cid = (adapter.get('candidate_id') or '')[:100] or None
                self.cursor.execute("""
                    INSERT INTO hdnd_qh_candidates
                    (name, province, party, constituency, description, detail_url, candidate_id, candidate_uuid, position, birthdate, hometown)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    adapter.get('name'), adapter.get('province'), adapter.get('party'),
                    adapter.get('constituency'), adapter.get('description'),
                    detail_url, cid, cuuid,
                    (adapter.get('position') or '')[:500],
                    adapter.get('birthdate') or '',
                    (adapter.get('hometown') or '')[:500]
                ))
            self.connection.commit()
        except Exception as e:
            logger.error('HdndQh MySQL error: %s', e)
            self.connection.rollback()
        return item

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


# =============================================================================
# HĐND CẤP XÃ - BẢNG RIÊNG hdnd_xa_candidates
# =============================================================================

class HdndXaMySQLPipeline:
    """Lưu CandidateItem từ spider hdnd_xa vào bảng hdnd_xa_candidates."""

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            port=crawler.settings.get('MYSQL_PORT', 3306),
            database=crawler.settings.get('MYSQL_DATABASE', 'scrapy_products'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '')
        )

    def open_spider(self, spider):
        if spider.name != 'hdnd_xa':
            return
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=self.password, charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
            self._create_tables()
        except Exception as e:
            spider.logger.error('HdndXa MySQL: %s', e)

    def _create_tables(self):
        # Bảng danh sách (giữ cấu trúc cũ để tương thích)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_xa_candidates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_province (province),
                INDEX idx_constituency (constituency)
            )
        """)
        # Bảng chi tiết (cấu trúc giống hdnd_detail_info)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdnd_xa_detail_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_detail_url (detail_url),
                INDEX idx_province (province)
            )
        """)
        self.connection.commit()

    def process_item(self, item, spider):
        if spider.name != 'hdnd_xa':
            return item
        if not self.connection:
            return item
        adapter = ItemAdapter(item)
        if not adapter.get('name') and not adapter.get('detail_url'):
            return item
        try:
            cuuid = (adapter.get('candidate_uuid') or '')[:100] or None
            if not cuuid:
                cuuid = (adapter.get('detail_url') or '')[:100] or 'unknown'
            detail_url = (adapter.get('detail_url') or '')[:767] or None

            # 1. hdnd_xa_candidates: danh sách (đủ field để hiển thị)
            self.cursor.execute("""
                INSERT INTO hdnd_xa_candidates
                (candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                 gender, nationality, ethnic, religion, current_address, education, foreign_lang,
                 degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    detail_url=VALUES(detail_url), province=VALUES(province), constituency=VALUES(constituency),
                    name=VALUES(name), birthdate=VALUES(birthdate), position=VALUES(position), hometown=VALUES(hometown),
                    gender=VALUES(gender), nationality=VALUES(nationality), ethnic=VALUES(ethnic), religion=VALUES(religion),
                    current_address=VALUES(current_address), education=VALUES(education), foreign_lang=VALUES(foreign_lang),
                    degree=VALUES(degree), party_theory=VALUES(party_theory), professional=VALUES(professional),
                    work_place=VALUES(work_place), party_join_date=VALUES(party_join_date),
                    qh_rep=VALUES(qh_rep), hdnd_rep=VALUES(hdnd_rep), image_url=VALUES(image_url)
            """, (
                cuuid, detail_url,
                (adapter.get('province') or '')[:255],
                (adapter.get('constituency') or '')[:500],
                adapter.get('name'), adapter.get('birthdate') or '',
                (adapter.get('position') or '')[:500], (adapter.get('hometown') or '')[:500],
                (adapter.get('gender') or '')[:50], (adapter.get('nationality') or '')[:100],
                (adapter.get('ethnic') or '')[:100], (adapter.get('religion') or '')[:100],
                (adapter.get('current_address') or '')[:500],
                (adapter.get('education') or '')[:255], (adapter.get('foreign_lang') or '')[:255],
                (adapter.get('degree') or '')[:255], (adapter.get('party_theory') or '')[:255],
                (adapter.get('professional') or '')[:500], (adapter.get('work_place') or '')[:500],
                (adapter.get('party_join_date') or '')[:50],
                (adapter.get('qh_rep') or '')[:255], (adapter.get('hdnd_rep') or '')[:255],
                (adapter.get('image_url') or '')[:1000]
            ))

            # 2. hdnd_xa_detail_info: chi tiết đầy đủ (cấu trúc giống hdnd_detail_info)
            self.cursor.execute("""
                INSERT INTO hdnd_xa_detail_info
                (candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                 gender, nationality, ethnic, religion, current_address, education, foreign_lang,
                 degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    detail_url=VALUES(detail_url), province=VALUES(province), constituency=VALUES(constituency),
                    name=VALUES(name), birthdate=VALUES(birthdate), position=VALUES(position), hometown=VALUES(hometown),
                    gender=VALUES(gender), nationality=VALUES(nationality), ethnic=VALUES(ethnic), religion=VALUES(religion),
                    current_address=VALUES(current_address), education=VALUES(education), foreign_lang=VALUES(foreign_lang),
                    degree=VALUES(degree), party_theory=VALUES(party_theory), professional=VALUES(professional),
                    work_place=VALUES(work_place), party_join_date=VALUES(party_join_date),
                    qh_rep=VALUES(qh_rep), hdnd_rep=VALUES(hdnd_rep), image_url=VALUES(image_url)
            """, (
                cuuid, detail_url,
                (adapter.get('province') or '')[:255],
                (adapter.get('constituency') or '')[:500],
                adapter.get('name'), adapter.get('birthdate') or '',
                (adapter.get('position') or '')[:500], (adapter.get('hometown') or '')[:500],
                (adapter.get('gender') or '')[:50], (adapter.get('nationality') or '')[:100],
                (adapter.get('ethnic') or '')[:100], (adapter.get('religion') or '')[:100],
                (adapter.get('current_address') or '')[:500],
                (adapter.get('education') or '')[:255], (adapter.get('foreign_lang') or '')[:255],
                (adapter.get('degree') or '')[:255], (adapter.get('party_theory') or '')[:255],
                (adapter.get('professional') or '')[:500], (adapter.get('work_place') or '')[:500],
                (adapter.get('party_join_date') or '')[:50],
                (adapter.get('qh_rep') or '')[:255], (adapter.get('hdnd_rep') or '')[:255],
                (adapter.get('image_url') or '')[:1000]
            ))
            self.connection.commit()
        except Exception as e:
            logger.error('HdndXa MySQL error: %s', e)
            self.connection.rollback()
        return item

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


# =============================================================================
# TRÚNG CỬ HĐND CẤP XÃ — hdbc_candidates_tc_cx + hdbc_candidates_tc_cx_info
# =============================================================================

class HdbcTcCxMySQLPipeline:
    """Lưu CandidateItem từ spider hdnd_tc_xa (đại biểu trúng cử cấp xã)."""

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            port=crawler.settings.get('MYSQL_PORT', 3306),
            database=crawler.settings.get('MYSQL_DATABASE', 'scrapy_products'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '')
        )

    def open_spider(self, spider):
        if spider.name != 'hdnd_tc_xa':
            return
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=self.password, charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
            self._create_tables()
        except Exception as e:
            spider.logger.error('HdbcTcCx MySQL: %s', e)

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdbc_candidates_tc_cx (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_province (province),
                INDEX idx_constituency (constituency)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hdbc_candidates_tc_cx_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_uuid VARCHAR(100) NOT NULL,
                detail_url VARCHAR(767),
                province VARCHAR(255),
                constituency VARCHAR(500),
                name VARCHAR(255),
                birthdate VARCHAR(50),
                position VARCHAR(500),
                hometown VARCHAR(500),
                gender VARCHAR(50),
                nationality VARCHAR(100),
                ethnic VARCHAR(100),
                religion VARCHAR(100),
                current_address VARCHAR(500),
                education VARCHAR(255),
                foreign_lang VARCHAR(255),
                degree VARCHAR(255),
                party_theory VARCHAR(255),
                professional VARCHAR(500),
                work_place VARCHAR(500),
                party_join_date VARCHAR(50),
                qh_rep VARCHAR(255),
                hdnd_rep VARCHAR(255),
                image_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_candidate_uuid (candidate_uuid),
                INDEX idx_detail_url (detail_url),
                INDEX idx_province (province)
            )
        """)
        self.connection.commit()

    def process_item(self, item, spider):
        if spider.name != 'hdnd_tc_xa':
            return item
        if not self.connection:
            return item
        adapter = ItemAdapter(item)
        if not adapter.get('name') and not adapter.get('detail_url'):
            return item
        try:
            cuuid = (adapter.get('candidate_uuid') or '')[:100] or None
            if not cuuid:
                cuuid = (adapter.get('detail_url') or '')[:100] or 'unknown'
            detail_url = (adapter.get('detail_url') or '')[:767] or None
            row = (
                cuuid, detail_url,
                (adapter.get('province') or '')[:255],
                (adapter.get('constituency') or '')[:500],
                adapter.get('name'), adapter.get('birthdate') or '',
                (adapter.get('position') or '')[:500], (adapter.get('hometown') or '')[:500],
                (adapter.get('gender') or '')[:50], (adapter.get('nationality') or '')[:100],
                (adapter.get('ethnic') or '')[:100], (adapter.get('religion') or '')[:100],
                (adapter.get('current_address') or '')[:500],
                (adapter.get('education') or '')[:255], (adapter.get('foreign_lang') or '')[:255],
                (adapter.get('degree') or '')[:255], (adapter.get('party_theory') or '')[:255],
                (adapter.get('professional') or '')[:500], (adapter.get('work_place') or '')[:500],
                (adapter.get('party_join_date') or '')[:50],
                (adapter.get('qh_rep') or '')[:255], (adapter.get('hdnd_rep') or '')[:255],
                (adapter.get('image_url') or '')[:1000]
            )
            sql_ins = (
                "INSERT INTO {} "
                "(candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown, "
                "gender, nationality, ethnic, religion, current_address, education, foreign_lang, "
                "degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "detail_url=VALUES(detail_url), province=VALUES(province), constituency=VALUES(constituency), "
                "name=VALUES(name), birthdate=VALUES(birthdate), position=VALUES(position), hometown=VALUES(hometown), "
                "gender=VALUES(gender), nationality=VALUES(nationality), ethnic=VALUES(ethnic), religion=VALUES(religion), "
                "current_address=VALUES(current_address), education=VALUES(education), foreign_lang=VALUES(foreign_lang), "
                "degree=VALUES(degree), party_theory=VALUES(party_theory), professional=VALUES(professional), "
                "work_place=VALUES(work_place), party_join_date=VALUES(party_join_date), "
                "qh_rep=VALUES(qh_rep), hdnd_rep=VALUES(hdnd_rep), image_url=VALUES(image_url)"
            )
            self.cursor.execute(sql_ins.format('hdbc_candidates_tc_cx'), row)
            self.cursor.execute(sql_ins.format('hdbc_candidates_tc_cx_info'), row)
            self.connection.commit()
        except Exception as e:
            logger.error('HdbcTcCx MySQL error: %s', e)
            self.connection.rollback()
        return item

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

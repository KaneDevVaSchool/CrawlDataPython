# -*- coding: utf-8 -*-
"""Crawl danh sach ung cu Quoc hoi (hdnd_qh).

  python run_crawl_qh.py
  python run_crawl_qh.py -limit 5           # Giới hạn 5 ứng viên
  python run_crawl_qh.py -source 0           # Chỉ nguồn đầu tiên (Hà Nội)
  python run_crawl_qh.py -fast               # Chế độ nhanh

Lưu vào MySQL: hdnd_qh_candidates + hdnd_qh_detail_info
"""

import subprocess
import sys
import os
import argparse

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def ensure_db():
    try:
        import pymysql
        from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
        conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        conn.cursor().execute(
            "CREATE DATABASE IF NOT EXISTS scrapy_products "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Warning: Could not ensure DB:", e)


ensure_db()

p = argparse.ArgumentParser()
p.add_argument("-limit", type=int, help="Giới hạn số ứng viên (vd: 5)")
p.add_argument("-source", type=str, help="Chỉ 1 nguồn: index (0) hoặc tên tỉnh")
p.add_argument("-fast", action="store_true", help="Chế độ nhanh")
p.add_argument("-debug", action="store_true", help="Log DEBUG")
args = p.parse_args()

cmd = [sys.executable, "-m", "scrapy", "crawl", "hdnd_qh"]
if args.limit:
    cmd.extend(["-a", f"limit={args.limit}"])
if args.source:
    cmd.extend(["-a", f"source={args.source}"])
if args.debug:
    cmd.extend(["-s", "LOG_LEVEL=DEBUG"])
if args.fast:
    cmd.extend([
        "-s", "DOWNLOAD_DELAY=0.2",
        "-s", "CONCURRENT_REQUESTS_PER_DOMAIN=6",
        "-s", "CONCURRENT_REQUESTS=12",
        "-s", "AUTOTHROTTLE_ENABLED=False",
    ])
    print("  Che do nhanh: -fast")

print("=" * 50)
print("Crawl ung cu Quoc hoi (hdnd_qh)")
print("=" * 50)
if args.limit:
    print(f"  Gioi han: {args.limit} ung vien")
if args.source:
    print(f"  Nguon: {args.source}")

r = subprocess.run(cmd)
sys.exit(r.returncode)

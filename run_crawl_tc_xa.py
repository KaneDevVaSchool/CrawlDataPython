# -*- coding: utf-8 -*-
"""Crawl danh sách trúng cử HĐND cấp xã (hdnd_tc_xa).

  python run_crawl_tc_xa.py
  python run_crawl_tc_xa.py -limit_candidate 5
  python run_crawl_tc_xa.py -source 0
  python run_crawl_tc_xa.py -limit_xa 2 -fast

MySQL: hdbc_candidates_tc_cx + hdbc_candidates_tc_cx_info
JSON: output/hdnd_tc_xa_candidates.json
"""

import argparse
import os
import subprocess
import sys

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
p.add_argument("-limit_candidate", type=int, help="Giới hạn số đại biểu crawl chi tiết")
p.add_argument("-limit_xa", type=int, help="Giới hạn số xã/phường mỗi tỉnh")
p.add_argument("-source", type=str, help="Chỉ 1 nguồn: index (0) hoặc tên tỉnh")
p.add_argument("-fast", action="store_true", help="Chế độ nhanh")
p.add_argument("-debug", action="store_true", help="Log DEBUG")
args = p.parse_args()

cmd = [sys.executable, "-m", "scrapy", "crawl", "hdnd_tc_xa"]
if args.limit_candidate:
    cmd.extend(["-a", f"limit_candidate={args.limit_candidate}"])
if args.limit_xa:
    cmd.extend(["-a", f"limit_xa={args.limit_xa}"])
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
    print("  Chế độ nhanh: -fast")

print("=" * 50)
print("Crawl trúng cử HĐND cấp xã (hdnd_tc_xa)")
print("=" * 50)
r = subprocess.run(cmd)
sys.exit(r.returncode)

# -*- coding: utf-8 -*-
"""
Chay crawl HDND cap xa (xa/phuong):

  python run_crawl_xa.py
  python run_crawl_xa.py -limit 2          # Gioi han 2 xa
  python run_crawl_xa.py -limit-candidate 3  # Toi da 3 ung vien moi xa
  python run_crawl_xa.py -source 0          # Chi nguon dau tien (Ben Tre)
"""

import subprocess
import sys
import os
import argparse

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def ensure_db():
    """Tao database scrapy_products neu chua co."""
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
p.add_argument("-limit", type=int, help="Gioi han so xa (vd: 5)")
p.add_argument("-limit-candidate", type=int, dest="limit_candidate", help="Gioi han ung vien moi xa")
p.add_argument("-source", type=str, help="Chi 1 nguon: index (0) hoac ten tinh")
p.add_argument("-fast", action="store_true", help="Che do nhanh (delay 0.2s, 6 concurrent)")
p.add_argument("-debug", action="store_true", help="Log DEBUG")
args = p.parse_args()

cmd = [sys.executable, "-m", "scrapy", "crawl", "hdnd_xa"]
if args.limit:
    cmd.extend(["-a", f"limit_xa={args.limit}"])
if args.limit_candidate:
    cmd.extend(["-a", f"limit_candidate={args.limit_candidate}"])
if args.source:
    cmd.extend(["-a", f"source={args.source}"])
if args.debug:
    cmd.extend(["-s", "LOG_LEVEL=DEBUG"])
if args.fast:
    cmd.extend([
        "-s", "HDND_FAST=1",
        "-s", "DOWNLOAD_DELAY=0.15",
        "-s", "CONCURRENT_REQUESTS_PER_DOMAIN=12",
        "-s", "CONCURRENT_REQUESTS=24",
        "-s", "AUTOTHROTTLE_ENABLED=False",
    ])
    print("  Che do nhanh: -fast (HDND_FAST=1)")

print("=" * 50)
print("Crawl HDND cap xa (hdnd_xa)")
print("=" * 50)
if args.limit:
    print(f"  Gioi han: {args.limit} xa")
if args.limit_candidate:
    print(f"  Ung vien/xa: toi da {args.limit_candidate}")

r = subprocess.run(cmd)
sys.exit(r.returncode)

# -*- coding: utf-8 -*-
"""
Chay crawl danh sach + chi tiet bang 1 lenh:

  python run_crawl.py
  python run_crawl.py -limit 10             # 10 record list + 10 chi tiet
  python run_crawl.py -source 1 -limit 10   # Ha Noi, 10 record
  python run_crawl.py -fast                 # HDND_FAST=1 (nhanh hon, giong run_crawl_all --fast)
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
p.add_argument("-limit", type=int, help="Gioi han so trang chi tiet (vd: 10)")
p.add_argument("-source", type=str, help="Chi chay 1 tinh: index (0,1) hoac ten (HCM, Ha Noi)")
p.add_argument("-detail", action="store_true", help="Chi crawl chi tiet tu detail_urls.txt (bo qua list)")
p.add_argument("-debug", action="store_true", help="Log DEBUG de tim loi")
p.add_argument("-fast", action="store_true", help="Scrapy -s HDND_FAST=1 (delay/concurrent toi uu)")
args = p.parse_args()

def _fast_settings():
    return ["-s", "HDND_FAST=1"] if args.fast else []

url_file = "output/detail_urls.txt"

if args.detail:
    # Chi crawl chi tiet tu file
    if not os.path.exists(url_file):
        print("Khong tim thay", url_file, "- chay list truoc hoac tao file.")
        sys.exit(1)
    print("=" * 50)
    print("Crawl detail tu", url_file)
    print("=" * 50)
    cmd = [sys.executable, "-m", "scrapy", "crawl", "hdnd_detail", "-a", f"url_file={url_file}"]
    if args.limit:
        cmd.extend(["-a", f"limit={args.limit}"])
        print("Limit:", args.limit)
    cmd.extend(_fast_settings())
    if args.fast:
        print("  Che do nhanh: -fast (HDND_FAST=1)")
    r = subprocess.run(cmd)
    sys.exit(r.returncode)

print("=" * 50)
print("1. Crawl list (hdnd_candidates)...")
print("=" * 50)
cmd1 = [sys.executable, "-m", "scrapy", "crawl", "hdnd_candidates"]
if args.source:
    cmd1.extend(["-a", f"source={args.source}"])
    print(f"   Source: {args.source}")
if args.limit:
    cmd1.extend(["-a", f"list_limit={args.limit}"])
    print(f"   List limit: {args.limit}")
if args.debug:
    cmd1.extend(["-s", "LOG_LEVEL=DEBUG"])
cmd1.extend(_fast_settings())
if args.fast:
    print("  Che do nhanh: -fast (HDND_FAST=1)")
r1 = subprocess.run(cmd1)
if r1.returncode != 0:
    print("Error: list crawl failed.")
    sys.exit(r1.returncode)

print()
print("=" * 50)
print("2. Crawl detail tu", url_file)
print("=" * 50)
cmd = [sys.executable, "-m", "scrapy", "crawl", "hdnd_detail", "-a", f"url_file={url_file}"]
if args.limit:
    cmd.extend(["-a", f"limit={args.limit}"])
    print(f"   Limit: {args.limit} records")
cmd.extend(_fast_settings())
r2 = subprocess.run(cmd)
sys.exit(r2.returncode)

# -*- coding: utf-8 -*-
"""
Tao database scrapy_products. Chay: python init_db.py
"""
try:
    import pymysql
    from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
except ImportError:
    print("pip install pymysql")
    exit(1)

try:
    conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        charset='utf8mb4'
    )
    conn.cursor().execute("CREATE DATABASE IF NOT EXISTS scrapy_products CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    conn.close()
    print("Database 'scrapy_products' ready.")
except Exception as e:
    print("Error:", e)

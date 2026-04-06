# -*- coding: utf-8 -*-
"""
Chạy toàn bộ crawl bầu cử (MySQL + JSON) theo thứ tự:

  1. HĐND cấp tỉnh — danh sách + chi tiết (hdnd_candidates → hdnd_detail)
  2. Quốc hội — hdnd_qh
  3. HĐND cấp xã (ứng cử) — hdnd_xa
  4. HĐND cấp xã (trúng cử) — hdnd_tc_xa

  python run_crawl_all.py
  python run_crawl_all.py --skip-tinh          # bỏ qua bước 1
  python run_crawl_all.py --skip-qh --skip-xa
  python run_crawl_all.py --fast               # nới throttle (từng script con)
  python run_crawl_all.py --source 0           # chỉ 1 tỉnh (index) cho mọi bước
  python run_crawl_all.py --source "Hà Nội" --fast

Lưu ý: Mất nhiều giờ nếu crawl hết tỉnh; thử nghiệm: --source / --fast hoặc chạy riêng run_crawl*.py với -limit.
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)


def ensure_db():
    try:
        import pymysql
        from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
        conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            charset='utf8mb4',
        )
        conn.cursor().execute(
            "CREATE DATABASE IF NOT EXISTS scrapy_products "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Warning: ensure DB:", e)


def run_script(name: str, extra: list | None = None) -> int:
    cmd = [sys.executable, os.path.join(ROOT, name)]
    if extra:
        cmd.extend(extra)
    print("\n" + "=" * 60)
    print(">>>", " ".join(cmd))
    print("=" * 60 + "\n")
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl tuần tự toàn bộ nguồn DSBC")
    p.add_argument("--skip-tinh", action="store_true", help="Bỏ HĐND cấp tỉnh (run_crawl.py)")
    p.add_argument("--skip-qh", action="store_true", help="Bỏ Quốc hội")
    p.add_argument("--skip-xa", action="store_true", help="Bỏ ứng cử cấp xã")
    p.add_argument("--skip-tc-xa", action="store_true", help="Bỏ trúng cử cấp xã")
    p.add_argument("--fast", action="store_true", help="Truyền -fast cho từng script hỗ trợ")
    p.add_argument(
        "--source",
        type=str,
        metavar="INDEX|TÊN",
        help="Truyền -source cho mỗi bước (index 0,1,... hoặc tên tỉnh như spider hỗ trợ)",
    )
    args = p.parse_args()

    ensure_db()
    extra: list[str] = []
    if args.fast:
        extra.append("-fast")
    if args.source:
        extra.extend(["-source", args.source])

    steps = []
    if not args.skip_tinh:
        steps.append(("run_crawl.py", list(extra)))
    if not args.skip_qh:
        steps.append(("run_crawl_qh.py", list(extra)))
    if not args.skip_xa:
        steps.append(("run_crawl_xa.py", list(extra)))
    if not args.skip_tc_xa:
        steps.append(("run_crawl_tc_xa.py", list(extra)))

    if not steps:
        print("Không có bước nào (tất cả đều --skip-*).")
        return 1

    for script, step_extra in steps:
        code = run_script(script, step_extra if step_extra else None)
        if code != 0:
            print(f"\nDừng: {script} thoát mã {code}")
            return code

    print("\n" + "=" * 60)
    print("Xong tất cả các bước crawl đã chọn.")
    print("Xem web: python serve.py → http://localhost:5000/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

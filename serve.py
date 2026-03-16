# -*- coding: utf-8 -*-
"""
Chạy server để xem danh sách ứng cử HĐND tại http://localhost:5000/

  python serve.py

Dữ liệu: chỉ từ MySQL (hdnd_candidates + hdnd_detail_info).
"""

import os

def load_from_db():
    """Đọc từ MySQL: hdnd_candidates + hdnd_detail_info (cấp tỉnh) + hdnd_detail_info (cấp xã)."""
    try:
        import pymysql
        from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
        conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, database=MYSQL_DATABASE,
            user=MYSQL_USER, password=MYSQL_PASSWORD, charset='utf8mb4'
        )
        cur = conn.cursor(pymysql.cursors.DictCursor)
        # 1. Cấp tỉnh: hdnd_candidates merge với hdnd_detail_info
        cur.execute("""
            SELECT c.id, c.name, c.province, c.party, c.constituency, c.description,
                   c.detail_url, c.candidate_id, c.candidate_uuid, c.position, c.birthdate, c.hometown
            FROM hdnd_candidates c
            ORDER BY c.province, c.candidate_id
        """)
        rows = cur.fetchall()
        cur.execute("SELECT * FROM hdnd_detail_info")
        details = {r['candidate_uuid']: r for r in cur.fetchall() if r.get('candidate_uuid')}
        # Merge detail vào list cấp tỉnh
        for r in rows:
            d = details.get(r.get('candidate_uuid'))
            if d:
                r.update({k: v for k, v in d.items() if k not in ('id', 'created_at') and v})
            r['level'] = 'tinh'
        # 2. Cấp xã: từ bảng riêng hdnd_xa_candidates
        try:
            cur.execute("""
                SELECT candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                       gender, nationality, ethnic, religion, current_address, education, foreign_lang,
                       degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url
                FROM hdnd_xa_candidates
            """)
            xa_rows = cur.fetchall()
            for r in xa_rows:
                r['level'] = 'xa'
                r['candidate_id'] = ''
                rows.append(r)
        except Exception:
            pass
        cur.close()
        conn.close()
        rows.sort(key=lambda x: ((x.get('province') or ''), (x.get('constituency') or ''), (x.get('name') or '')))
        return rows
    except Exception as e:
        print(f"[serve] MySQL: {e}")
        return None


def main():
    try:
        from flask import Flask, send_from_directory, jsonify
    except ImportError:
        print("Install Flask: pip install flask")
        return
    app = Flask(__name__, static_folder='output', static_url_path='')
    base = os.path.join(os.path.dirname(__file__), 'output')

    @app.route('/api/candidates')
    def api_candidates():
        from flask import request
        data = load_from_db()
        if data is None:
            return jsonify({"error": "MySQL connection failed. Run crawlers first."}), 500
        # Phân trang API: ?page=1&per_page=20 (nếu có thì trả {items, total, page, per_page, total_pages})
        page = request.args.get('page', type=int, default=0)
        per_page = request.args.get('per_page', type=int, default=0)
        if page > 0 and per_page > 0:
            per_page = min(per_page, 500)
            total = len(data)
            start = (page - 1) * per_page
            items = data[start:start + per_page]
            return jsonify({"items": items, "total": total, "page": page, "per_page": per_page, "total_pages": (total + per_page - 1) // per_page})
        return jsonify(data)

    @app.route('/')
    def index():
        return send_from_directory(base, 'index.html')

    @app.route('/output')
    def output_redirect():
        from flask import redirect
        return redirect('/')

    print("Open: http://localhost:5000/")
    print("Or: http://localhost:5000/output/index.html")
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()

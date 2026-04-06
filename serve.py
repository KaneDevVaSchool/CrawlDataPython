# -*- coding: utf-8 -*-
"""
Chạy server để xem danh sách ứng cử HĐND tại http://localhost:5000/

  python serve.py

Dữ liệu: MySQL (hdnd_* + hdnd_qh_* + hdnd_xa_* + hdbc_candidates_tc_cx).
       Nếu MySQL trống/lỗi, có thể fallback JSON (hdnd_xa / hdnd_tc_xa).
"""

import os
import json

def load_from_db():
    """Đọc từ MySQL: hdnd_candidates + hdnd_detail_info (cấp tỉnh) + hdnd_xa_candidates (cấp xã).
       Nếu MySQL lỗi, fallback JSON khi có file hdnd_xa_candidates.json."""
    try:
        import pymysql
        from product_crawler.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
        conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, database=MYSQL_DATABASE,
            user=MYSQL_USER, password=MYSQL_PASSWORD, charset='utf8mb4'
        )
        cur = conn.cursor(pymysql.cursors.DictCursor)
        rows = []
        # 1. Cấp tỉnh: hdnd_candidates (có thể chưa có bảng nếu chỉ crawl cấp xã)
        try:
            cur.execute("""
                SELECT c.id, c.name, c.province, c.party, c.constituency, c.description,
                       c.detail_url, c.candidate_id, c.candidate_uuid, c.position, c.birthdate, c.hometown
                FROM hdnd_candidates c
                ORDER BY c.province, c.candidate_id
            """)
            rows = list(cur.fetchall())  # ensure list (not tuple)
            cur.execute("SELECT * FROM hdnd_detail_info")
            details = {r['candidate_uuid']: r for r in cur.fetchall() if r.get('candidate_uuid')}
            for r in rows:
                d = details.get(r.get('candidate_uuid'))
                if d:
                    r.update({k: v for k, v in d.items() if k not in ('id', 'created_at') and v})
                r['level'] = 'tinh'
        except Exception as ex:
            print(f"[serve] hdnd_candidates/detail_info: {ex} (bỏ qua nếu chỉ có cấp xã)")
        # 2. Quốc hội: hdnd_qh_candidates + hdnd_qh_detail_info
        qh_rows = []
        try:
            cur.execute("""
                SELECT id, name, province, party, constituency, description,
                       detail_url, candidate_id, candidate_uuid, position, birthdate, hometown
                FROM hdnd_qh_candidates
                ORDER BY province, candidate_id
            """)
            qh_rows = list(cur.fetchall())  # ensure list
            try:
                cur.execute("SELECT * FROM hdnd_qh_detail_info")
                qh_details = {r['candidate_uuid']: r for r in cur.fetchall() if r.get('candidate_uuid')}
                for r in qh_rows:
                    d = qh_details.get(r.get('candidate_uuid'))
                    if d:
                        r.update({k: v for k, v in d.items() if k not in ('id', 'created_at') and v})
            except Exception:
                pass
            for r in qh_rows:
                r['level'] = 'qh'
                rows.append(r)
            if qh_rows:
                print(f"[serve] Loaded {len(qh_rows)} from hdnd_qh_candidates")
        except Exception as ex:
            print(f"[serve] hdnd_qh_candidates error: {ex}")
        # 3. Cấp xã: hdnd_xa_candidates + hdnd_xa_detail_info (merge chi tiết như cấp tỉnh)
        xa_rows = []
        try:
            cur.execute("""
                SELECT candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                       gender, nationality, ethnic, religion, current_address, education, foreign_lang,
                       degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url
                FROM hdnd_xa_candidates
            """)
            xa_rows = list(cur.fetchall())  # ensure list
            try:
                cur.execute("SELECT * FROM hdnd_xa_detail_info")
                xa_details = {r['candidate_uuid']: r for r in cur.fetchall() if r.get('candidate_uuid')}
                for r in xa_rows:
                    d = xa_details.get(r.get('candidate_uuid'))
                    if d:
                        r.update({k: v for k, v in d.items() if k not in ('id', 'created_at') and v})
            except Exception:
                pass  # bảng chưa có dữ liệu
            for r in xa_rows:
                r['level'] = 'xa'
                r['candidate_id'] = ''
                rows.append(r)
            if xa_rows:
                print(f"[serve] Loaded {len(xa_rows)} from hdnd_xa_candidates")
        except Exception as ex:
            print(f"[serve] hdnd_xa_candidates error: {ex}")
        # 4. Trúng cử HĐND cấp xã: hdbc_candidates_tc_cx + hdbc_candidates_tc_cx_info
        tc_xa_rows = []
        try:
            cur.execute("""
                SELECT candidate_uuid, detail_url, province, constituency, name, birthdate, position, hometown,
                       gender, nationality, ethnic, religion, current_address, education, foreign_lang,
                       degree, party_theory, professional, work_place, party_join_date, qh_rep, hdnd_rep, image_url
                FROM hdbc_candidates_tc_cx
            """)
            tc_xa_rows = list(cur.fetchall())
            try:
                cur.execute("SELECT * FROM hdbc_candidates_tc_cx_info")
                tc_details = {r['candidate_uuid']: r for r in cur.fetchall() if r.get('candidate_uuid')}
                for r in tc_xa_rows:
                    d = tc_details.get(r.get('candidate_uuid'))
                    if d:
                        r.update({k: v for k, v in d.items() if k not in ('id', 'created_at') and v})
            except Exception:
                pass
            for r in tc_xa_rows:
                r['level'] = 'tc_xa'
                r['candidate_id'] = ''
                rows.append(r)
            if tc_xa_rows:
                print(f"[serve] Loaded {len(tc_xa_rows)} from hdbc_candidates_tc_cx")
        except Exception as ex:
            print(f"[serve] hdbc_candidates_tc_cx error: {ex}")
        # Fallback: đọc từ JSON nếu MySQL cấp xã trống/lỗi
        json_path = os.path.join(os.path.dirname(__file__), 'output', 'hdnd_xa_candidates.json')
        if not xa_rows and os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    xa_fallback = json.load(f)
                if isinstance(xa_fallback, list) and xa_fallback:
                    for r in xa_fallback:
                        r['level'] = 'xa'
                        r['candidate_id'] = r.get('candidate_id', '')
                        rows.append(r)
                    print(f"[serve] Fallback: loaded {len(xa_fallback)} from hdnd_xa_candidates.json")
            except Exception as ex:
                print(f"[serve] JSON fallback error: {ex}")
        json_tc = os.path.join(os.path.dirname(__file__), 'output', 'hdnd_tc_xa_candidates.json')
        if not tc_xa_rows and os.path.exists(json_tc):
            try:
                with open(json_tc, 'r', encoding='utf-8') as f:
                    tc_fallback = json.load(f)
                if isinstance(tc_fallback, list) and tc_fallback:
                    for r in tc_fallback:
                        r['level'] = 'tc_xa'
                        r['candidate_id'] = r.get('candidate_id', '')
                        rows.append(r)
                    print(f"[serve] Fallback: loaded {len(tc_fallback)} from hdnd_tc_xa_candidates.json")
            except Exception as ex:
                print(f"[serve] JSON tc_xa fallback error: {ex}")
        cur.close()
        conn.close()
        rows = list(rows)  # ensure list before sort
        rows.sort(key=lambda x: ((x.get('province') or ''), (x.get('constituency') or ''), (x.get('name') or '')))
        return rows
    except Exception as e:
        print(f"[serve] MySQL: {e}")
        # Fallback: nếu MySQL lỗi hoàn toàn, thử đọc JSON
        out_dir = os.path.join(os.path.dirname(__file__), 'output')
        merged = []
        for fname, lvl in (('hdnd_xa_candidates.json', 'xa'), ('hdnd_tc_xa_candidates.json', 'tc_xa')):
            jpath = os.path.join(out_dir, fname)
            if os.path.exists(jpath):
                try:
                    with open(jpath, 'r', encoding='utf-8') as f:
                        chunk = json.load(f)
                    if isinstance(chunk, list):
                        for r in chunk:
                            r['level'] = lvl
                            r['candidate_id'] = r.get('candidate_id', '')
                        merged.extend(chunk)
                except Exception as ex:
                    print(f"[serve] JSON {fname}: {ex}")
        if merged:
            merged.sort(key=lambda x: ((x.get('province') or ''), (x.get('constituency') or ''), (x.get('name') or '')))
            print(f"[serve] Fallback JSON: loaded {len(merged)} records (MySQL unavailable)")
            return merged
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

    @app.after_request
    def cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

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

# Hướng dẫn sử dụng DSBC

Dự án crawl dữ liệu ứng cử / trúng cử từ **hoidongbaucu.quochoi.vn**, lưu **MySQL** và/hoặc **JSON**, xem qua **Flask** tại trình duyệt.

---

## 1. Chuẩn bị môi trường

- Python 3.10+ (khuyến nghị)
- MySQL (tùy chọn nhưng nên có để pipeline ghi DB và `serve.py` đọc đầy đủ)

Cài dependency:

```bash
pip install -r requirements.txt
```

Thông tin kết nối MySQL: chỉnh trong `product_crawler/settings.py` (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`). Các script `run_crawl*.py` sẽ tạo database `scrapy_products` nếu chưa có (theo cấu hình trong settings).

---

## 2. Cấu hình nguồn crawl (tỉnh / thành)

File chính: **`product_crawler/config.py`**

| Biến | Ý nghĩa |
|------|---------|
| `HDND_SOURCES` | HĐND **cấp tỉnh** (`run_crawl.py` → `hdnd_candidates`, `hdnd_detail`) |
| `QH_SOURCES` | **Ứng cử Quốc hội** (`run_crawl_qh.py` → `hdnd_qh`) |
| `HDND_XA_SOURCES` | HĐND **cấp xã — ứng cử** (`run_crawl_xa.py` → `hdnd_xa`) |
| `HDND_TC_XA_SOURCES` | HĐND cấp xã **trúng cử** — mặc định lấy từ `QH_SOURCES` |

Mỗi phần tử thường có: `name`, `province_id` hoặc `tinh_thanh_id`, `khoa` (ví dụ `16`).

Thêm tỉnh mới: mở trang quochoi → DevTools → Network → chọn tỉnh trong dropdown → copy id từ request (xem gợi ý đầu file `config.py`).

---

## 3. Chạy crawl

### 3.1. Một lệnh — cả pipeline (theo thứ tự)

**`run_crawl_all.py`** chạy lần lượt:

1. HĐND cấp tỉnh (danh sách + chi tiết)  
2. Quốc hội  
3. HĐND cấp xã (ứng cử)  
4. HĐND cấp xã (trúng cử)

```bash
python run_crawl_all.py
```

Tùy chọn thường dùng:

| Tham số | Ý nghĩa |
|---------|---------|
| `--fast` | Bật chế độ nhanh (`HDND_FAST` + throttle nới ở từng bước) |
| `--source INDEX` hoặc `--source "Tên tỉnh"` | Chỉ crawl **một** nguồn (truyền xuống mọi bước còn bật) |
| `--skip-tinh` | Bỏ bước HĐND cấp tỉnh |
| `--skip-qh` | Bỏ Quốc hội |
| `--skip-xa` | Bỏ ứng cử cấp xã |
| `--skip-tc-xa` | Bỏ trúng cử cấp xã |

Ví dụ:

```bash
python run_crawl_all.py --source 0 --fast
python run_crawl_all.py --skip-tinh --source "Thành phố Hồ Chí Minh"
```

**Lưu ý:** Crawl hết mọi tỉnh trong config có thể mất nhiều giờ. Nên thử `--source` hoặc `-limit` trên từng script con trước.

### 3.2. Chạy từng loại riêng

| Script | Nội dung |
|--------|----------|
| `run_crawl.py` | HĐND cấp tỉnh: list → `output/detail_urls.txt` → detail |
| `run_crawl_qh.py` | Quốc hội |
| `run_crawl_xa.py` | HĐND cấp xã (ứng cử) |
| `run_crawl_tc_xa.py` | HĐND cấp xã (trúng cử) |

Tham số chung (tùy file):

- **`-source`** — index (`0`, `1`, …) trong list config tương ứng, hoặc chuỗi con của **`name`** (so khớp không phân biệt hoa thường).
- **`-fast`** — chế độ nhanh.
- **`-limit`** / **`-limit_xa`** / **`-limit-candidate`** / **`-limit_candidate`** — giới hạn bản ghi (xem `--help` của từng script).

`run_crawl.py` thêm:

- **`-detail`** — chỉ crawl chi tiết từ `output/detail_urls.txt` (bỏ qua bước list).
- **`-debug`** — log DEBUG.

Ví dụ:

```bash
python run_crawl.py -source 0 -limit 20 -fast
python run_crawl_xa.py -source 0 -limit 3 -fast
python run_crawl_qh.py -source 1 -limit 50
```

**Windows (PowerShell):** nối lệnh bằng `;` thay vì `&&` nếu môi trường không hỗ trợ `&&`.

### 3.3. Chạy Scrapy trực tiếp (nâng cao)

```bash
python -m scrapy crawl hdnd_candidates
python -m scrapy crawl hdnd_detail -a url_file=output/detail_urls.txt
python -m scrapy crawl hdnd_qh
python -m scrapy crawl hdnd_xa
python -m scrapy crawl hdnd_tc_xa
```

Có thể thêm `-a source=0` (hoặc tên), `-s HDND_FAST=1`, v.v. tùy spider.

---

## 4. Xem dữ liệu trên web

```bash
python serve.py
```

Mở trình duyệt: **http://localhost:5000/**

Ưu tiên đọc từ **MySQL** (các bảng `hdnd_*`, `hdnd_qh_*`, `hdnd_xa_*`, `hdbc_candidates_tc_cx*`, …). Nếu DB trống hoặc lỗi kết nối, có thể fallback **JSON** trong `output/` (tùy triển khai hiện tại).

Giao diện danh sách nằm tại **`output/index.html`** (được serve qua Flask).

---

## 5. File output thường gặp

- `output/detail_urls.txt` — URL chi tiết HĐND cấp tỉnh (sau bước list).
- `output/hdnd_candidates.json`, `output/hdnd_qh_candidates.json`, … — tùy spider/pipeline đã bật trong `settings.py`.

Schema bảng tham khảo: **`output/schema_all_tables.sql`** (nếu có trong repo).

---

## 6. Khắc phục nhanh

| Hiện tượng | Gợi ý |
|------------|--------|
| 429 / trang ngắn / thiếu dữ liệu | Giảm tốc: bỏ `--fast`, tăng delay trong settings hoặc giảm concurrent. |
| Cookie / HTML challenge | Middleware D1N + retry đã hỗ trợ; chạy lại hoặc giảm áp lực request. |
| Detail sai tỉnh sau khi đổi `-source` | `detail_urls.txt` có thể còn URL cũ — chạy lại bước list với `-source` hoặc xóa/lọc file trước khi `-detail`. |
| MySQL lỗi kết nối | Kiểm tra `settings.py`, firewall, user/password; vẫn có thể xem một phần qua JSON. |

---

## 7. Cấu trúc thư mục gợi ý

- `product_crawler/spiders/` — spider Scrapy  
- `product_crawler/pipelines.py` — ghi DB / JSON  
- `product_crawler/settings.py` — pipeline, middleware, MySQL  
- `product_crawler/hdnd_crawl_support.py` — tiện ích chung (fast mode, snapshot, sanitize)  

---

*Tài liệu này mô tả cách dùng theo trạng thái repo tại thời điểm viết; nếu thêm spider hoặc đổi tên bảng, cập nhật tương ứng trong `settings.py` và `serve.py`.*

# Chạy crawl trên Server - Nhanh hơn local

## Tại sao server nhanh hơn?

| Yếu tố | Máy local | Server (VPS) |
|--------|-----------|--------------|
| **Độ trễ mạng** | Cao nếu xa VN | Thấp nếu đặt server tại VN (FPT, Viettel, VNPT) |
| **Băng thông** | Phụ thuộc WiFi/ADSL | Thường ổn định, tốc độ cao |
| **Chạy nền** | Bị ảnh hưởng khi tắt máy | Chạy 24/7, không bị gián đoạn |

**Kết luận:** Server tại Việt Nam (gần hoidongbaucu.quochoi.vn) sẽ giảm round-trip ~50–100ms/request → tăng tốc rõ rệt.

---

## Cấu hình server gợi ý

### 1. VPS trong nước (Viettel, FPT, VNPT…)
- CPU: 2 core
- RAM: 2 GB
- Giá: ~100–200k/tháng

### 2. Chạy với chế độ nhanh nhất

```bash
# SSH vào server, clone/upload code
cd DSBC

# Cài đặt nếu chưa có
pip install scrapy pymysql itemadapter

# Chạy crawl tối đa tốc độ (cẩn thận có thể bị rate-limit)
python run_crawl_xa.py -source 0 -fast

# Hoặc chạy nền với nohup
nohup python run_crawl_xa.py -source 0 -fast > crawl.log 2>&1 &
```

### 3. Dùng screen/tmux để chạy nền

```bash
screen -S crawl
python run_crawl_xa.py -source 0
# Ctrl+A, D để thoát nhưng vẫn chạy
# screen -r crawl để quay lại xem
```

---

## Lưu ý khi chạy trên server

1. **MySQL:** Cấu hình `product_crawler/settings.py` (host, user, password).
2. **Rate limit:** Nếu bị block (429/timeout), bỏ `-fast` và chạy mặc định.
3. **Disk:** Đảm bảo đủ dung lượng cho MySQL và file JSON.

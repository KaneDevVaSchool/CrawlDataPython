# -*- coding: utf-8 -*-
"""
Cấu hình nguồn dữ liệu - thêm tỉnh/link tại đây.

Thêm tỉnh mới: mở hoidongbaucu.quochoi.vn > DevTools > Network >
chọn tỉnh trong dropdown > copy tinhThanhKhoaId từ request.
"""

# URL gốc và đường dẫn API
BASE_URL = "https://hoidongbaucu.quochoi.vn"
CANDIDATE_API_PATH = "/get-chi-tiet-danh-sach-ung-cu-hdnd"
DETAIL_PATH = "/thong-tin-nguoi-ung-cu"
REFERER_URL = "https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu-hdnd"

# Khóa HĐND (16 = Khóa XVI)
KHOA = 16
PAGE_SIZE = 300

# File output
DETAIL_URLS_FILE = "output/detail_urls.txt"

# Danh sách nguồn HĐND cấp xã (xã/phường) - spider hdnd_xa
# ds-ung-cu-hdnd-cap-xa?tinhThanhKhoaId=... (API: get-danh-sach-ung-cu-hdnd-cap-xa)
HDND_XA_SOURCES = [
    {
        "name": "Điện Biên",
        "tinh_thanh_id": "02503149-b62e-4807-2760-08ddb263ac09",
        "khoa": 16,
    },
   
]

# Danh sách nguồn: tỉnh/thành cần crawl (HĐND cấp tỉnh)
# Thêm tỉnh: copy tinhThanhKhoaId từ request khi chọn tỉnh trên trang
HDND_SOURCES = [
    {
        "name": "Thành phố Hồ Chí Minh",
        "province_id": "ddfaac97-a898-48ae-f9d7-08ddb2649d30",
        "khoa": 16,
    },
    {
        "name": "Hà Nội",
        "province_id": "08497e01-0003-44b1-f9c6-08ddb2649d30",
        "khoa": 16,
    },
]

# Map nhãn trang chi tiết -> tên field (dùng trong hdnd_detail_spider)
DETAIL_FIELD_MAP = {
    "Ngày tháng năm sinh": "birthdate",
    "Giới tính": "gender",
    "Quốc tịch": "nationality",
    "Dân tộc": "ethnic",
    "Tôn giáo": "religion",
    "Quê quán": "hometown",
    "Nơi ở hiện nay": "current_address",
    "Giáo dục phổ thông": "education",
    "Ngoại ngữ": "foreign_lang",
    "Học hàm, học vị": "degree",
    "Trình độ lý luận chính trị": "party_theory",
    "Chuyên môn nghiệp vụ": "professional",
    "Nghề nghiệp, chức vụ": "position",
    "Nơi công tác": "work_place",
    "Ngày vào Đảng": "party_join_date",
    "Đại biểu Quốc hội": "qh_rep",
    "Đại biểu HĐND": "hdnd_rep",
}

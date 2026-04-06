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
        "name": "Lai Châu",
        "tinh_thanh_id": "bc729a39-9973-45ac-275d-08ddb263ac09",
        "khoa": 16,
    },

]

# API danh sách ứng cử Quốc hội (không có -hdnd trong path)
QH_API_PATH = "/get-chi-tiet-danh-sach-ung-cu"
QH_REFERER_URL = "https://hoidongbaucu.quochoi.vn/vi/danh-sach-ung-cu"
# Nguồn tỉnh/thành cho ứng cử Quốc hội (cấu trúc giống HDND_SOURCES)
QH_SOURCES = [
    {"name": "An Giang", "province_id": "992c4a74-46f1-4b6b-f9d9-08ddb2649d30", "khoa": 16},
    {"name": "Bắc Ninh", "province_id": "57a5ba9a-4ee9-4614-f9c4-08ddb2649d30", "khoa": 16},
    {"name": "Cà Mau", "province_id": "691fecb4-cf4d-4729-f9dc-08ddb2649d30", "khoa": 16},
    {"name": "Cao Bằng", "province_id": "50947c75-3d15-46bc-275c-08ddb263ac09", "khoa": 16},
    {"name": "Thành Phố Cần Thơ",
        "province_id": "d8f66f2b-1ee2-462a-f9db-08ddb2649d30", "khoa": 16},
    {"name": "Thành Phố Đà Nẵng",
        "province_id": "985dc7e5-094a-4440-f9cf-08ddb2649d30", "khoa": 16},
    {"name": "Đăk Lăk", "province_id": "154bc82b-1917-4744-f9d2-08ddb2649d30", "khoa": 16},
    {"name": "Điện Biên", "province_id": "02503149-b62e-4807-2760-08ddb263ac09", "khoa": 16},
    {"name": "Đồng Nai", "province_id": "423cfbb0-d4a7-4a72-f9d5-08ddb2649d30", "khoa": 16},
    {"name": "Đồng Tháp", "province_id": "a934a18b-74ca-4561-f9d8-08ddb2649d30", "khoa": 16},
    {"name": "Gia Lai", "province_id": "355b0b9a-908a-45f2-f9d1-08ddb2649d30", "khoa": 16},
    {"name": "Thành Phố Hà Nội",
        "province_id": "08497e01-0003-44b1-f9c6-08ddb2649d30", "khoa": 16},
    {"name": "Hà Tĩnh", "province_id": "2d7d8ef7-c043-4f4a-f9cc-08ddb2649d30", "khoa": 16},
    {"name": "Thành phố Hải Phòng",
        "province_id": "8bae010e-15c7-4617-f9c7-08ddb2649d30", "khoa": 16},
    {"name": "Hưng Yên", "province_id": "776abe7b-939b-4ed0-f9c8-08ddb2649d30", "khoa": 16},
    {"name": "Khánh Hòa", "province_id": "6d078bcb-caf9-45f7-bbae-588c62cdbeb8", "khoa": 16},
    {"name": "Lai Châu", "province_id": "bc729a39-9973-45ac-275d-08ddb263ac09", "khoa": 16},
    {"name": "Lạng Sơn", "province_id": "dd51f9a8-0ad9-40cf-f9c1-08ddb2649d30", "khoa": 16},
    {"name": "Lào Cai", "province_id": "d48c922d-ae81-41bd-275e-08ddb263ac09", "khoa": 16},
    {"name": "Lâm Đồng", "province_id": "4ac23efc-bfa4-4b18-f9d4-08ddb2649d30", "khoa": 16},
    {"name": "Nghệ An", "province_id": "0fdb4aa1-8609-46e0-f9cb-08ddb2649d30", "khoa": 16},
    {"name": "Ninh Bình", "province_id": "840011ae-0d18-428f-f9c9-08ddb2649d30", "khoa": 16},
    {"name": "Phú Thọ", "province_id": "50bd74bb-e776-4286-f9c3-08ddb2649d30", "khoa": 16},
    {"name": "Quảng Ngãi", "province_id": "cf82e159-c8d4-4b9f-f9d0-08ddb2649d30", "khoa": 16},
    {"name": "Quảng Ninh", "province_id": "04ce0ff7-52b0-417d-f9c5-08ddb2649d30", "khoa": 16},
    {"name": "Quảng Trị", "province_id": "650e1e08-8d00-4491-f9cd-08ddb2649d30", "khoa": 16},
    {"name": "Sơn La", "province_id": "d56d135b-9990-46b2-f9c2-08ddb2649d30", "khoa": 16},
    {"name": "Tây Ninh", "province_id": "589ad671-2cab-4cf6-f9d6-08ddb2649d30", "khoa": 16},
    {"name": "Thái Nguyên", "province_id": "6786a229-964c-44bb-275f-08ddb263ac09", "khoa": 16},
    {"name": "Thanh Hóa", "province_id": "2d90ec2d-08d4-445f-f9ca-08ddb2649d30", "khoa": 16},
    {"name": "Thành phố Hồ Chí Minh",
        "province_id": "ddfaac97-a898-48ae-f9d7-08ddb2649d30", "khoa": 16},
    {"name": "Thành phố Huế",
        "province_id": "b0f81569-c0a6-4701-f9ce-08ddb2649d30", "khoa": 16},
    {"name": "Tuyên Quang", "province_id": "5b46222f-fd9e-44f2-275b-08ddb263ac09", "khoa": 16},
    {"name": "Vĩnh Long", "province_id": "8fcfe1bb-81ce-4abe-f9da-08ddb2649d30", "khoa": 16}
]

# Trúng cử HĐND cấp xã — spider hdnd_tc_xa (API get-danh-sach-trung-cu-hdnd-cap-xa)
TRUNG_CU_XA_REFERER_URL = "https://hoidongbaucu.quochoi.vn/vi/danh-sach-trung-cu-hdnd-cap-xa"
HDND_TC_XA_SOURCES = [
    {"name": s["name"], "tinh_thanh_id": s["province_id"], "khoa": s.get("khoa", KHOA)}
    for s in QH_SOURCES
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

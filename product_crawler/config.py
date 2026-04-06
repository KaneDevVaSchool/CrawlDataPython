# -*- coding: utf-8 -*-
"""Cấu hình nguồn crawl (tỉnh/id). Thêm tỉnh: DevTools → Network → chọn dropdown → copy tinhThanhKhoaId."""

# --- Khóa & phân trang ---
KHOA = 16  # Khóa XVI
PAGE_SIZE = 300

# --- Site HĐND cấp tỉnh (ứng cử) ---
BASE_URL = "https://hoidongbaucu.quochoi.vn"
CANDIDATE_API_PATH = "/get-chi-tiet-danh-sach-ung-cu-hdnd"
DETAIL_PATH = "/thong-tin-nguoi-ung-cu"
REFERER_URL = f"{BASE_URL}/vi/danh-sach-ung-cu-hdnd"
DETAIL_URLS_FILE = "output/detail_urls.txt"

# --- Quốc hội (ứng cử) ---
QH_API_PATH = "/get-chi-tiet-danh-sach-ung-cu"
QH_REFERER_URL = f"{BASE_URL}/vi/danh-sach-ung-cu"

# --- HĐND cấp xã trúng cử (hdnd_tc_xa) ---
TRUNG_CU_XA_REFERER_URL = f"{BASE_URL}/vi/danh-sach-trung-cu-hdnd-cap-xa"


def _p(name: str, province_id: str) -> dict:
    """Tỉnh dùng chung: QH + HĐND cấp tỉnh (khóa province_id)."""
    return {"name": name, "province_id": province_id, "khoa": KHOA}


def _xa(name: str, tinh_thanh_id: str) -> dict:
    """Tỉnh cho spider cấp xã ứng cử (khóa tinh_thanh_id)."""
    return {"name": name, "tinh_thanh_id": tinh_thanh_id, "khoa": KHOA}


# Danh sách tỉnh — Quốc hội (hdnd_qh). Index 0,1,… dùng với -a source=
QH_SOURCES = [
    _p("An Giang", "992c4a74-46f1-4b6b-f9d9-08ddb2649d30"),
    _p("Bắc Ninh", "57a5ba9a-4ee9-4614-f9c4-08ddb2649d30"),
    _p("Cà Mau", "691fecb4-cf4d-4729-f9dc-08ddb2649d30"),
    _p("Cao Bằng", "50947c75-3d15-46bc-275c-08ddb263ac09"),
    _p("Thành Phố Cần Thơ", "d8f66f2b-1ee2-462a-f9db-08ddb2649d30"),
    _p("Thành Phố Đà Nẵng", "985dc7e5-094a-4440-f9cf-08ddb2649d30"),
    _p("Đăk Lăk", "154bc82b-1917-4744-f9d2-08ddb2649d30"),
    _p("Điện Biên", "02503149-b62e-4807-2760-08ddb263ac09"),
    _p("Đồng Nai", "423cfbb0-d4a7-4a72-f9d5-08ddb2649d30"),
    _p("Đồng Tháp", "a934a18b-74ca-4561-f9d8-08ddb2649d30"),
    _p("Gia Lai", "355b0b9a-908a-45f2-f9d1-08ddb2649d30"),
    _p("Thành Phố Hà Nội", "08497e01-0003-44b1-f9c6-08ddb2649d30"),
    _p("Hà Tĩnh", "2d7d8ef7-c043-4f4a-f9cc-08ddb2649d30"),
    _p("Thành phố Hải Phòng", "8bae010e-15c7-4617-f9c7-08ddb2649d30"),
    _p("Hưng Yên", "776abe7b-939b-4ed0-f9c8-08ddb2649d30"),
    _p("Khánh Hòa", "6d078bcb-caf9-45f7-bbae-588c62cdbeb8"),
    _p("Lai Châu", "bc729a39-9973-45ac-275d-08ddb263ac09"),
    _p("Lạng Sơn", "dd51f9a8-0ad9-40cf-f9c1-08ddb2649d30"),
    _p("Lào Cai", "d48c922d-ae81-41bd-275e-08ddb263ac09"),
    _p("Lâm Đồng", "4ac23efc-bfa4-4b18-f9d4-08ddb2649d30"),
    _p("Nghệ An", "0fdb4aa1-8609-46e0-f9cb-08ddb2649d30"),
    _p("Ninh Bình", "840011ae-0d18-428f-f9c9-08ddb2649d30"),
    _p("Phú Thọ", "50bd74bb-e776-4286-f9c3-08ddb2649d30"),
    _p("Quảng Ngãi", "cf82e159-c8d4-4b9f-f9d0-08ddb2649d30"),
    _p("Quảng Ninh", "04ce0ff7-52b0-417d-f9c5-08ddb2649d30"),
    _p("Quảng Trị", "650e1e08-8d00-4491-f9cd-08ddb2649d30"),
    _p("Sơn La", "d56d135b-9990-46b2-f9c2-08ddb2649d30"),
    _p("Tây Ninh", "589ad671-2cab-4cf6-f9d6-08ddb2649d30"),
    _p("Thái Nguyên", "6786a229-964c-44bb-275f-08ddb263ac09"),
    _p("Thanh Hóa", "2d90ec2d-08d4-445f-f9ca-08ddb2649d30"),
    _p("Thành phố Hồ Chí Minh", "ddfaac97-a898-48ae-f9d7-08ddb2649d30"),
    _p("Thành phố Huế", "b0f81569-c0a6-4701-f9ce-08ddb2649d30"),
    _p("Tuyên Quang", "5b46222f-fd9e-44f2-275b-08ddb263ac09"),
    _p("Vĩnh Long", "8fcfe1bb-81ce-4abe-f9da-08ddb2649d30"),
]

# Trúng cử cấp xã: cùng id tỉnh với QH, đổi tên khóa cho API xã
HDND_TC_XA_SOURCES = [
    {"name": s["name"], "tinh_thanh_id": s["province_id"], "khoa": s["khoa"]}
    for s in QH_SOURCES
]

# HĐND cấp xã — ứng cử (hdnd_xa). Thêm/bớt tỉnh tại đây (không bắt buộc trùng QH_SOURCES)
HDND_XA_SOURCES = [
    _xa("Lai Châu", "bc729a39-9973-45ac-275d-08ddb263ac09"),
]

# HĐND cấp tỉnh — danh sách ứng cử (hdnd_candidates / hdnd_detail)
HDND_SOURCES = [
    _p("Thành phố Hồ Chí Minh", "ddfaac97-a898-48ae-f9d7-08ddb2649d30"),
    _p("Hà Nội", "08497e01-0003-44b1-f9c6-08ddb2649d30"),
]

# Nhãn HTML chi tiết → field item
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

# -*- coding: utf-8 -*-
"""
Items module - Defines the data structure for scraped data.

Items are used to define the structure of data that spiders extract.
Scrapy uses these to validate and serialize the scraped data.
"""

import scrapy


class CandidateItem(scrapy.Item):
    """
    Ứng viên ứng cử HĐND - Danh sách ứng cử HĐND cấp tỉnh.
    """
    name = scrapy.Field()           # Họ tên ứng cử viên
    province = scrapy.Field()       # Tỉnh/thành phố
    party = scrapy.Field()          # Đảng/cơ quan giới thiệu
    constituency = scrapy.Field()   # Đơn vị bầu cử
    description = scrapy.Field()     # Giới thiệu / Chức vụ tóm tắt
    detail_url = scrapy.Field()     # URL trang chi tiết
    candidate_id = scrapy.Field()   # ID / STT
    candidate_uuid = scrapy.Field() # UUID từ URL detail (d9cca651-14c8-499a-8550-01cde72ede76)
    position = scrapy.Field()       # Chức vụ tóm tắt
    birthdate = scrapy.Field()      # Ngày sinh
    hometown = scrapy.Field()       # Quê quán
    # Chi tiết từ trang thông tin cá nhân
    gender = scrapy.Field()         # Giới tính
    nationality = scrapy.Field()    # Quốc tịch
    ethnic = scrapy.Field()         # Dân tộc
    religion = scrapy.Field()       # Tôn giáo
    current_address = scrapy.Field() # Nơi ở hiện nay
    education = scrapy.Field()      # Giáo dục phổ thông
    foreign_lang = scrapy.Field()   # Ngoại ngữ
    degree = scrapy.Field()         # Học hàm, học vị
    party_theory = scrapy.Field()   # Trình độ lý luận chính trị
    professional = scrapy.Field()    # Chuyên môn nghiệp vụ
    work_place = scrapy.Field()     # Nơi công tác
    party_join_date = scrapy.Field() # Ngày vào Đảng
    qh_rep = scrapy.Field()        # Đại biểu Quốc hội
    hdnd_rep = scrapy.Field()      # Đại biểu HĐND
    image_url = scrapy.Field()     # Ảnh đại diện
    raw_data = scrapy.Field()       # Dữ liệu gốc để xử lý sau


class ProductItem(scrapy.Item):
    """
    Product item representing a single product's data structure.
    
    All fields are defined with Field() which allows optional metadata
    for serialization and validation.
    """
    # Product title/name
    title = scrapy.Field()
    
    # Product price (stored as string to preserve formatting, e.g., "$19.99")
    price = scrapy.Field()
    
    # Full product description
    description = scrapy.Field()
    
    # URL of the main product image
    image_url = scrapy.Field()
    
    # Canonical URL to the product detail page (used for deduplication)
    product_url = scrapy.Field()

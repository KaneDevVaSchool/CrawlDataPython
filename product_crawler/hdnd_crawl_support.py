# -*- coding: utf-8 -*-
"""Tiện ích chung cho spider Hội đồng bầu cử: tốc độ, làm sạch field, snapshot bảng."""

from __future__ import annotations

import json
import re
from typing import Any


def apply_hdnd_fast(crawler) -> None:
    """Bật khi settings HDND_FAST=1 hoặc -s HDND_FAST=1 (Scrapy coi true/1/yes)."""
    if not crawler.settings.getbool("HDND_FAST", default=False):
        return
    s = crawler.settings
    s.set("DOWNLOAD_DELAY", 0.1, priority="cmdline")
    s.set("RANDOMIZE_DOWNLOAD_DELAY", True, priority="cmdline")
    s.set("CONCURRENT_REQUESTS_PER_DOMAIN", 20, priority="cmdline")
    s.set("CONCURRENT_REQUESTS", 36, priority="cmdline")
    s.set("AUTOTHROTTLE_ENABLED", False, priority="cmdline")
    s.set("AUTOTHROTTLE_TARGET_CONCURRENCY", 12.0, priority="cmdline")


class QuochoiHdndMixin:
    """Áp dụng HDND_FAST trước khi spider khởi tạo."""

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        apply_hdnd_fast(crawler)
        return super().from_crawler(crawler, *args, **kwargs)


def row_cells_text(row) -> list[str]:
    """Lấy nội dung từng ô td trong một tr (scrapy Selector)."""
    out = []
    for td in row.css("td"):
        t = " ".join(td.css("::text").getall()).strip()
        out.append(re.sub(r"\s+", " ", t))
    return out


def list_snapshot_from_xa_row(row) -> dict[str, Any]:
    """Snapshot hàng danh sách API cấp xã (ứng cử / trúng cử)."""
    cells = row_cells_text(row)
    snap: dict[str, Any] = {"cells": cells}
    if len(cells) >= 2:
        snap["stt"] = cells[0]
        snap["list_name"] = cells[1]
    if len(cells) >= 3:
        snap["list_birthdate"] = cells[2]
    if len(cells) >= 4:
        snap["list_gender"] = cells[3]
    if len(cells) >= 5:
        snap["list_position"] = cells[4]
    if len(cells) >= 6:
        snap["list_hometown"] = cells[5]
    return snap


def sanitize_parsed_detail(data: dict) -> None:
    """Bỏ giá trị field bị gán nhầm từ nhãn HTML/regex."""
    deg = (data.get("degree") or "").strip()
    if not deg:
        return
    low = deg.lower()
    if "trình độ lý luận chính trị" in low or deg.rstrip().endswith(":"):
        data["degree"] = ""
    if low in ("học hàm, học vị:", "học hàm, học vị"):
        data["degree"] = ""


def build_raw_data_meta(response_meta: dict, list_snap: dict | None) -> str:
    """Chuỗi JSON: snapshot danh sách + id địa phương (cho JSON pipeline)."""
    payload = {
        "list": list_snap or {},
        "commune_url": response_meta.get("commune_url") or "",
        "xa_phuong_id": response_meta.get("xa_phuong_id") or "",
        "province": response_meta.get("province") or "",
        "constituency": response_meta.get("constituency") or "",
    }
    return json.dumps(payload, ensure_ascii=False)


def merge_list_into_item_fields(item: dict, list_snap: dict | None) -> None:
    """Điền field trống từ snapshot bảng (không ghi đè chi tiết đã có)."""
    if not list_snap:
        return
    cells = list_snap.get("cells") or []
    if not item.get("name"):
        item["name"] = list_snap.get("list_name") or (cells[1] if len(cells) > 1 else "") or item.get("name", "")
    if not item.get("birthdate"):
        item["birthdate"] = list_snap.get("list_birthdate") or ""
    if not item.get("gender"):
        item["gender"] = list_snap.get("list_gender") or ""
    if not item.get("position") and not item.get("description"):
        p = list_snap.get("list_position") or ""
        item["position"] = p
        item["description"] = p
    if not item.get("hometown"):
        item["hometown"] = list_snap.get("list_hometown") or ""

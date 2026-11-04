#!/usr/bin/env python3
"""adlib_api.py: Gọi Meta Ad Library API chính thức (ads_archive) để lấy ad + dữ liệu minh bạch EU/UK (DSA):
lượt tiếp cận EU, cơ cấu độ tuổi × giới tính × quốc gia, target khai báo (tuổi, giới, địa điểm), người trả tiền.

Điều kiện (một lần):
  1. Vào facebook.com/ID → xác minh danh tính & vị trí (bắt buộc với Ad Library API).
  2. Tạo app tại developers.facebook.com, lấy User Access Token (Graph API Explorer). Token KHÔNG ghi vào file/repo.
  3. export META_ADLIB_TOKEN=…
Giới hạn của Meta: ad THƯƠNG MẠI chỉ trả về nếu có phân phối ở EU/UK (trong 1 năm sau khi chạy); ad chỉ chạy ở Mỹ/VN sẽ không có.

Dùng:
  python3 adlib_api.py --page-ids 123,456 --countries DE,FR,GB -o ads_api.json [--status ALL] [--max 500]
  python3 adlib_api.py --search "posture corrector" --countries DE -o ads_api.json
Rồi: python3 adlib_parse.py -i ads_api.json -o ads_raw.json   ·   python3 audience.py --ads ads_raw.json …
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = os.environ.get("META_GRAPH_BASE", "https://graph.facebook.com")
FIELDS = ["id", "ad_snapshot_url", "page_id", "page_name", "ad_creation_time", "ad_delivery_start_time", "ad_delivery_stop_time",
          "ad_creative_bodies", "ad_creative_link_titles", "ad_creative_link_captions", "publisher_platforms", "languages",
          "eu_total_reach", "age_country_gender_reach_breakdown", "target_ages", "target_gender", "target_locations",
          "beneficiary_payers"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page-ids", help="tối đa 10, cách nhau dấu phẩy")
    ap.add_argument("--search", help="từ khoá")
    ap.add_argument("--countries", required=True, help="ISO-2, vd DE,FR,GB (phải là nước EU/UK để có dữ liệu DSA)")
    ap.add_argument("--status", default="ALL", choices=["ALL", "ACTIVE", "INACTIVE"])
    ap.add_argument("--platform", help="facebook | instagram | messenger | audience_network")
    ap.add_argument("--version", default=os.environ.get("META_GRAPH_VERSION", "v24.0"))
    ap.add_argument("--max", type=int, default=500)
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    tok = os.environ.get("META_ADLIB_TOKEN", "").strip()
    if not tok:
        sys.exit("Thiếu META_ADLIB_TOKEN (User Access Token sau khi xác minh danh tính tại facebook.com/ID).")
    if not a.page_ids and not a.search:
        sys.exit("Cần --page-ids hoặc --search")
    params = {
        "ad_reached_countries": json.dumps([c.strip().upper() for c in a.countries.split(",")]),
        "ad_type": "ALL", "ad_active_status": a.status, "fields": ",".join(FIELDS), "limit": "100",
    }
    if a.page_ids:
        params["search_page_ids"] = json.dumps([p.strip() for p in a.page_ids.split(",")][:10])
    if a.search:
        params["search_terms"] = a.search
    if a.platform:
        params["publisher_platforms"] = json.dumps([a.platform.lower()])
    url = f"{BASE}/{a.version}/ads_archive?" + urllib.parse.urlencode(params)
    ads = []
    while url and len(ads) < a.max:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                page = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")
            try:
                m = json.loads(err)["error"]
                msg = f"{m.get('code')}/{m.get('error_subcode')}: {m.get('message')}"
            except Exception:  # noqa: BLE001
                msg = err[:300]
            hint = ""
            if "identity" in msg.lower() or "2332002" in msg:
                hint = " → cần xác minh danh tính tại facebook.com/ID"
            elif e.code == 400 and "version" in msg.lower():
                hint = " → đổi --version (vd v23.0, v25.0)"
            elif e.code in (429,) or "limit" in msg.lower():
                hint = " → chạm giới hạn gọi API, đợi rồi chạy lại"
            sys.exit(f"Meta API lỗi {e.code}: {msg}{hint}")
        ads += page.get("data", [])
        url = page.get("paging", {}).get("next")
        print(f"  … {len(ads)} ad", file=sys.stderr)
        time.sleep(0.5)
    ads = ads[: a.max]
    Path(a.out).write_text(json.dumps({"source": "ads_archive", "countries": a.countries, "data": ads}, ensure_ascii=False, indent=1), encoding="utf-8")
    n_reach = sum(1 for x in ads if x.get("eu_total_reach"))
    n_bd = sum(1 for x in ads if x.get("age_country_gender_reach_breakdown"))
    print(f"→ {len(ads)} ad · {n_reach} có EU reach · {n_bd} có cơ cấu tuổi/giới → {a.out}")
    print(f"Bước tiếp: python3 adlib_parse.py -i {a.out} -o ads_raw.json && python3 audience.py --ads ads_raw.json")


if __name__ == "__main__":
    main()

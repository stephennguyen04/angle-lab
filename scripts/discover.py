#!/usr/bin/env python3
"""discover.py: Tự tìm đối thủ từ kết quả tìm Ad Library theo TỪ KHOÁ ngách → xếp hạng advertiser đáng spy.

Nguồn: bất kỳ file ad nào có page_id/page_name (adlib_parse.py output; MCP ads_library_search với search_terms;
scraper với URL ...&q=<từ khoá>&search_type=keyword_unordered; adlib_api.py --search). Trộn nhiều từ khoá được.

Dùng: python3 discover.py -i kw1.json -i kw2.json [--as-of …] [--exclude-domains amazon.com,temu.com] --out-md competitors.md
Điểm = ad active (log) + ad chạy lâu nhất + ad mới 30 ngày (đang đẩy) + % Instagram; loại sàn/brand lớn theo domain.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ad_cadence import load_rows, parse_bool, parse_date, parse_int, pick  # noqa: E402
from csvio import brief  # noqa: E402

MARKETPLACES = {"amazon.com", "amazon.co.uk", "amazon.de", "temu.com", "aliexpress.com", "shein.com", "walmart.com", "ebay.com",
                "etsy.com", "shopee.vn", "lazada.vn", "tiktok.com", "tiki.vn", "target.com"}


def domain(u) -> str | None:
    if not u:
        return None
    try:
        h = (urlparse(u if "://" in str(u) else "https://" + str(u)).hostname or "").lower()
        return h.removeprefix("www.") or None
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", action="append", required=True)
    ap.add_argument("--as-of")
    ap.add_argument("--exclude-domains", default="")
    ap.add_argument("--min-ads", type=int, default=2)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--country", default="ALL")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    excl = MARKETPLACES | {d.strip().lower() for d in a.exclude_domains.split(",") if d.strip()}
    pages = defaultdict(lambda: {"name": None, "ads": set(), "active": 0, "new30": 0, "max_days": 0, "ig": 0, "plat": 0,
                                 "domains": defaultdict(int), "samples": []})
    for f in a.input:
        if not Path(f).exists():
            print(f"[warn] không thấy {f}, bỏ qua", file=sys.stderr)
            continue
        for r in load_rows(Path(f)):
            pid = str(pick(r, "page_id") or "") or None
            name = pick(r, "page_name")
            key = pid or name
            aid = str(pick(r, "id") or "")
            sd = parse_date(pick(r, "start_date"))
            if not key or not aid or not sd:
                continue
            p = pages[key]
            if aid in p["ads"]:
                continue
            p["ads"].add(aid)
            p["name"] = p["name"] or name
            p["page_id"] = pid
            ed = parse_date(pick(r, "end_date"))
            act = parse_bool(pick(r, "is_active"))
            act = (ed is None or ed >= as_of) if act is None else act
            days = (as_of - sd).days + 1
            if act:
                p["active"] += 1
                p["max_days"] = max(p["max_days"], days)
            p["new30"] += days <= 30
            plats = str(pick(r, "platforms") or "").lower()
            if plats:
                p["plat"] += 1
                p["ig"] += "instagram" in plats
            d = domain(pick(r, "landing_url"))
            if d:
                p["domains"][d] += 1
            if len(p["samples"]) < 2 and pick(r, "body"):
                p["samples"].append(str(pick(r, "body"))[:70].replace("\n", " "))
    rows = []
    for key, p in pages.items():
        if len(p["ads"]) < a.min_ads:
            continue
        top_dom = max(p["domains"], key=p["domains"].get) if p["domains"] else None
        if top_dom and any(top_dom == m or top_dom.endswith("." + m) for m in excl):
            continue
        score = round(10 * math.log1p(p["active"]) + min(p["max_days"], 120) / 4 + 2 * min(p["new30"], 15)
                      + (10 * p["ig"] / p["plat"] if p["plat"] else 0), 1)
        rows.append({"page": p["name"] or key, "page_id": p.get("page_id"), "ads": len(p["ads"]), "active": p["active"], "new_30d": p["new30"],
                     "max_days_active": p["max_days"], "instagram_pct": round(100 * p["ig"] / p["plat"]) if p["plat"] else None,
                     "domain": top_dom, "score": score, "samples": p["samples"],
                     "ad_library": f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={a.country}&view_all_page_id={p['page_id']}" if p.get("page_id") else None})
    rows.sort(key=lambda x: -x["score"])
    L = [f"# Đối thủ tìm được ({len(rows)} advertiser)\n",
         "| # | Page | Domain | Ad (active) | Mới 30d | Ad lâu nhất | % IG | Điểm | Mẫu nội dung | Ad Library |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(rows[: a.top], 1):
        L.append(f"| {i} | {x['page']} | {x['domain'] or '—'} | {x['ads']} ({x['active']}) | {x['new_30d']} | {x['max_days_active']} ngày | "
                 f"{str(x['instagram_pct']) + '%' if x['instagram_pct'] is not None else '—'} | **{x['score']}** | {' / '.join(x['samples']).replace('|', '/')} | "
                 f"{'[mở](' + x['ad_library'] + ')' if x['ad_library'] else '—'} |")
    L.append("\n> Ưu tiên spy: nhiều ad active + có ad sống >30 ngày + vẫn ra ad mới. Chạy `/angle-lab:spy` với link Ad Library của page đó.")
    md = "\n".join(L) + "\n"
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(brief(md, a.out_md, 8))


if __name__ == "__main__":
    main()

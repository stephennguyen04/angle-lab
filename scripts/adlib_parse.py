#!/usr/bin/env python3
"""adlib_parse.py: Bóc dữ liệu ad từ GraphQL của Meta Ad Library → ads.json chuẩn cho ad_cadence / angle_scoreboard.

Nguồn đầu vào (trộn được nhiều file):
  - File .har: bạn tự lưu khi lướt Ad Library trên trình duyệt (DevTools → Network → chuột phải → "Save all as HAR").
                Ít rủi ro nhất vì bạn chỉ duyệt như người thường, không có bot.
  - File .graphql.jsonl do adlib_scrape.cjs ghi lại (mỗi dòng = 1 response GraphQL).
  - File .json bất kỳ chứa object ad (kết quả MCP ads_library_search, API ads_archive, actor Apify…).

Cách bóc: tìm đệ quy mọi object có "ad_archive_id" (hoặc "adArchiveID"/"id" + "ad_snapshot_url"), nên không phụ thuộc
đường dẫn JSON cụ thể khi Meta đổi cấu trúc.

Trường xuất: id, page_id, page_name, start_date, end_date, is_active, duplicates (collation_count), platforms,
media_type, video_url, image_url, landing_url, cta, body, title, eu_reach, partnership, snapshot_url.

Dùng:
  python3 adlib_parse.py -i ads.har -i scrape.graphql.jsonl -o ads.json [--page-id 123] [--platform instagram]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def iter_json_blobs(text: str):
    """Response GraphQL của Meta có thể có tiền tố 'for (;;);' và nhiều object nối nhau trên nhiều dòng."""
    text = text.strip()
    if text.startswith("for (;;);"):
        text = text[len("for (;;);"):]
    try:
        yield json.loads(text)
        return
    except json.JSONDecodeError:
        pass
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("for (;;);"):
            line = line[9:]
        if line.startswith("{") or line.startswith("["):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def blobs_from_file(path: Path):
    suf = path.suffix.lower()
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if suf == ".har":
        har = json.loads(raw)
        for e in har.get("log", {}).get("entries", []):
            url = e.get("request", {}).get("url", "")
            if "facebook.com" not in url and "graphql" not in url:
                continue
            c = e.get("response", {}).get("content", {})
            t = c.get("text")
            if not t:
                continue
            if c.get("encoding") == "base64":
                try:
                    t = base64.b64decode(t).decode("utf-8", "replace")
                except Exception:  # noqa: BLE001
                    continue
            if "ad_archive_id" in t or "adArchiveID" in t:
                yield from iter_json_blobs(t)
    elif suf == ".jsonl":
        for line in raw.splitlines():
            if line.strip():
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(d, dict) and isinstance(d.get("body"), str):  # {url, body} do scraper ghi
                    yield from iter_json_blobs(d["body"])
                else:
                    yield d
    else:
        yield from iter_json_blobs(raw)


def find_ads(o, out: list):
    if isinstance(o, dict):
        if "ad_archive_id" in o or "adArchiveID" in o or ("ad_snapshot_url" in o and "id" in o):
            out.append(o)
        # collated_results / edges… cứ đi sâu hết, kể cả trong object ad (để lấy bản nhân lồng nhau)
        for v in o.values():
            if isinstance(v, (dict, list)):
                find_ads(v, out)
    elif isinstance(o, list):
        for v in o:
            find_ads(v, out)


def deep_get(o, *keys):
    """Lấy giá trị đầu tiên khớp 1 trong các key, tìm đệ quy (giới hạn độ sâu)."""
    stack = [(o, 0)]
    while stack:
        cur, d = stack.pop(0)
        if isinstance(cur, dict):
            for k in keys:
                if k in cur and cur[k] not in (None, "", [], {}):
                    return cur[k]
            if d < 6:
                stack += [(v, d + 1) for v in cur.values() if isinstance(v, (dict, list))]
        elif isinstance(cur, list) and d < 6:
            stack += [(v, d + 1) for v in cur]
    return None


def to_date(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
        ts = float(v)
        ts = ts / 1000 if ts > 1e11 else ts
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v))
    return m[1] if m else str(v)


def text_of(v):
    if isinstance(v, dict):
        if v.get("text"):
            return v["text"]
        m = v.get("markup")
        return m.get("__html") if isinstance(m, dict) else None
    if isinstance(v, list):
        return " | ".join(filter(None, (text_of(x) for x in v)))
    return v


def normalize(a: dict) -> dict:
    snap = a.get("snapshot") or {}
    plats = a.get("publisher_platform") or a.get("publisher_platforms") or a.get("publisherPlatform") or []
    if isinstance(plats, str):
        plats = [plats]
    plats = sorted({str(p).lower() for p in plats})
    videos = snap.get("videos") or []
    cards = snap.get("cards") or []
    video_url = None
    for v in videos + cards:
        if isinstance(v, dict):
            video_url = v.get("video_hd_url") or v.get("video_sd_url")
            if video_url:
                break
    imgs = snap.get("images") or []
    image_url = next((i.get("original_image_url") or i.get("resized_image_url") for i in imgs if isinstance(i, dict)), None)
    fmt = (snap.get("display_format") or "").lower()
    media = "video" if video_url or fmt == "video" else "carousel" if fmt in ("carousel", "dco", "dpa") or len(cards) > 1 else "image"
    body = text_of(snap.get("body")) or text_of(a.get("ad_creative_bodies")) or deep_get(a, "ad_creative_body")
    reach = a.get("eu_total_reach") or deep_get(a, "eu_total_reach", "euTotalReach", "total_reach")
    if isinstance(reach, dict):
        reach = reach.get("lower_bound") or reach.get("value")
    partner = bool(snap.get("branded_content") or a.get("branded_content") or deep_get(a, "branded_content_sponsor", "sponsor_page_name")
                   or re.search(r"paid partnership|hợp tác có trả phí", str(body or ""), re.I))
    end = to_date(a.get("end_date") or a.get("ad_delivery_stop_time") or a.get("endDate"))
    active = a.get("is_active", a.get("isActive"))
    if active is None:
        active = end is None
    return {
        "id": str(a.get("ad_archive_id") or a.get("adArchiveID") or a.get("id")),
        "page_id": str(a.get("page_id") or snap.get("page_id") or a.get("pageID") or "") or None,
        "page_name": a.get("page_name") or snap.get("page_name") or a.get("pageName"),
        "start_date": to_date(a.get("start_date") or a.get("ad_delivery_start_time") or a.get("startDate")),
        "end_date": end,
        "is_active": bool(active),
        "duplicates": int(a.get("collation_count") or a.get("collationCount") or 1),
        "collation_id": a.get("collation_id"),
        "platforms": ",".join(plats) or None,
        "media_type": media,
        "video_url": video_url,
        "image_url": image_url,
        "landing_url": snap.get("link_url") or a.get("link_url") or deep_get(cards, "link_url"),
        "cta": snap.get("cta_text") or snap.get("cta_type"),
        "title": text_of(snap.get("title")) or text_of(a.get("ad_creative_link_titles")),
        "body": (body or "")[:1000],
        "eu_reach": int(reach) if isinstance(reach, (int, float)) or (isinstance(reach, str) and reach.isdigit()) else None,
        "partnership": partner,
        "snapshot_url": a.get("ad_snapshot_url"),
        # Dữ liệu minh bạch EU/UK (DSA): cơ cấu tiếp cận + target khai báo
        "reach_breakdown": a.get("age_country_gender_reach_breakdown") or deep_get(a, "age_country_gender_reach_breakdown"),
        "target_ages": a.get("target_ages") or deep_get(a, "target_ages"),
        "target_gender": a.get("target_gender") or deep_get(a, "target_gender"),
        "target_locations": a.get("target_locations") or deep_get(a, "target_locations"),
        "payer": (a.get("beneficiary_payers") or [{}])[0].get("payer") if isinstance(a.get("beneficiary_payers"), list) and a.get("beneficiary_payers") else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", action="append", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--page-id", help="Chỉ giữ ad của page này")
    ap.add_argument("--platform", help="Chỉ giữ ad có placement này, vd instagram")
    a = ap.parse_args()

    found = []
    for p in a.input:
        path = Path(p)
        if not path.exists():
            print(f"[warn] không thấy {p}", file=sys.stderr)
            continue
        n0 = len(found)
        for blob in blobs_from_file(path):
            find_ads(blob, found)
        print(f"{path.name}: {len(found) - n0} object ad", file=sys.stderr)

    # Lượt 1: chuẩn hoá + gộp theo id (response chi tiết thường chỉ có id + eu_total_reach, không có ngày)
    ads: dict[str, dict] = {}
    for raw in found:
        try:
            ad = normalize(raw)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] bỏ 1 ad lỗi: {e}", file=sys.stderr)
            continue
        if not ad["id"] or ad["id"] == "None":
            continue
        old = ads.get(ad["id"])
        if old:
            for k, v in ad.items():
                if k == "duplicates":
                    old[k] = max(old[k] or 1, v or 1)
                elif k == "is_active" and not ad["start_date"]:
                    continue          # object chi tiết không mang trạng thái thật
                elif old.get(k) in (None, "", False) and v not in (None, "", False):
                    old[k] = v
        else:
            ads[ad["id"]] = ad
    # Lượt 2: lọc
    res = []
    for ad in ads.values():
        if not ad["start_date"]:
            continue
        if a.page_id and ad["page_id"] != a.page_id:
            continue
        if a.platform and (ad["platforms"] is None or a.platform.lower() not in ad["platforms"]):
            continue
        res.append(ad)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    n_ig = sum(1 for x in res if x["platforms"] and "instagram" in x["platforms"])
    n_reach = sum(1 for x in res if x["eu_reach"])
    print(f"→ {len(res)} ad (đã dedupe) · {n_ig} chạy Instagram · {n_reach} có EU reach · {sum(x['partnership'] for x in res)} ad hợp tác creator → {a.out}")


if __name__ == "__main__":
    main()

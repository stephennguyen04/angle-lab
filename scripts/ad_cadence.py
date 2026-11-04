#!/usr/bin/env python3
"""ad_cadence.py — Đo mức độ scale & nhịp ra ad mới của đối thủ từ dữ liệu Ad Library.

Input: CSV / JSON / JSONL, mỗi dòng là 1 ad. Tên cột linh hoạt (xem FIELD_ALIASES).
Tối thiểu cần: id + start_date. Nên có: is_active/end_date, media_type, landing_url,
duplicates ("N ads use this creative"), video_url, body.

Output: Markdown (stdout hoặc --out-md) + JSON (--out-json) gồm:
  - số ad active / tổng, ad mới 7/14/30 ngày, histogram theo tuần
  - verdict nhịp ra ad (đều / theo đợt / chững / ngưng)
  - phân bố tuổi ad active, media mix
  - phân bố landing page (PDP / advertorial / collection / home / ngoài site)
  - xếp hạng "winner score" → đề xuất 5 video top để mổ

Chỉ dùng thư viện chuẩn.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

FIELD_ALIASES = {
    "id": ["id", "ad_id", "library_id", "ad_archive_id", "adarchiveid", "ma_thu_vien"],
    "start_date": ["start_date", "ad_delivery_start_time", "started", "started_running",
                   "start", "ngay_bat_dau", "bat_dau_chay"],
    "end_date": ["end_date", "ad_delivery_stop_time", "stopped", "end", "ngay_ket_thuc"],
    "is_active": ["is_active", "active", "status", "trang_thai"],
    "media_type": ["media_type", "type", "format", "display_format", "loai"],
    "landing_url": ["landing_url", "link_url", "url", "cta_link", "destination", "link"],
    "duplicates": ["duplicates", "collation_count", "ads_using_creative", "same_creative_count",
                   "variants", "so_ad_dung_creative"],
    "video_url": ["video_url", "video", "video_hd_url", "video_sd_url", "media_url"],
    "body": ["body", "text", "ad_creative_body", "primary_text", "caption", "noi_dung"],
    "page_name": ["page_name", "page", "advertiser"],
    "platforms": ["platforms", "publisher_platforms", "placements", "nen_tang"],
}

EN_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def norm_key(k: str) -> str:
    k = k.strip().lower()
    k = re.sub(r"[^a-z0-9]+", "_", k)
    return k.strip("_")


def pick(row: dict, field: str):
    keys = {norm_key(k): v for k, v in row.items()}
    for alias in FIELD_ALIASES[field]:
        if alias in keys and keys[alias] not in (None, ""):
            return keys[alias]
    return None


def parse_date(val) -> date | None:
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        # unix timestamp (s hoặc ms)
        ts = val / 1000 if val > 1e11 else val
        return datetime.utcfromtimestamp(ts).date()
    s = str(val).strip()
    if re.fullmatch(r"\d{10,13}", s):
        return parse_date(int(s))
    s_low = s.lower()
    # ISO: 2026-10-01 hoặc 2026-10-01T...
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s_low)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    # "1 thg 10, 2026" / "Bắt đầu chạy vào 1 Thg 10, 2026"
    m = re.search(r"(\d{1,2})\s*thg\s*(\d{1,2}),?\s*(\d{4})", s_low)
    if m:
        return date(int(m[3]), int(m[2]), int(m[1]))
    # "Oct 1, 2026" / "Started running on Oct 1, 2026"
    m = re.search(r"([a-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})", s_low)
    if m and m[1] in EN_MONTHS:
        return date(int(m[3]), EN_MONTHS[m[1]], int(m[2]))
    # "1 Oct 2026"
    m = re.search(r"(\d{1,2})\s+([a-z]{3})[a-z]*\.?,?\s+(\d{4})", s_low)
    if m and m[2] in EN_MONTHS:
        return date(int(m[3]), EN_MONTHS[m[2]], int(m[1]))
    # dd/mm/yyyy (mặc định kiểu Việt Nam)
    m = re.match(r"(\d{1,2})[/.](\d{1,2})[/.](\d{4})", s_low)
    if m:
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        if mo > 12:  # chắc chắn là mm/dd
            d, mo = mo, d
        return date(y, mo, d)
    return None


def parse_bool(val) -> bool | None:
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in {"1", "true", "yes", "y", "active", "đang hoạt động", "dang hoat dong", "đang chạy"}:
        return True
    if s in {"0", "false", "no", "n", "inactive", "không hoạt động", "khong hoat dong", "đã dừng"}:
        return False
    return None


def parse_int(val, default=1) -> int:
    if val is None or val == "":
        return default
    m = re.search(r"\d+", str(val).replace(",", ""))
    return int(m[0]) if m else default


def classify_media(val, row) -> str:
    s = (str(val or "")).lower()
    if "video" in s:
        return "video"
    if "carousel" in s or "dco" in s or "multi" in s:
        return "carousel"
    if "image" in s or "photo" in s or "anh" in s:
        return "image"
    if pick(row, "video_url"):
        return "video"
    return "unknown"


def classify_landing(url: str | None, brand_domain: str | None) -> str:
    if not url:
        return "không rõ"
    try:
        u = urlparse(url if "://" in url else "https://" + url)
    except ValueError:
        return "không rõ"
    host = (u.hostname or "").lower().removeprefix("www.")
    path = (u.path or "/").lower()
    if any(x in host for x in ("facebook.com", "fb.me", "instagram.com", "m.me", "wa.me")):
        return "messenger/social"
    if brand_domain and host and brand_domain not in host:
        return "advertorial/presell (domain khác)"
    if "/products/" in path or re.search(r"/p/|/dp/|/item", path):
        return "PDP (thẳng trang sản phẩm)"
    if "/pages/" in path or "/blogs/" in path or any(
            k in path for k in ("advertorial", "article", "story", "review", "listicle", "reasons",
                                "presell", "lp", "offer")):
        return "advertorial/listicle/LP"
    if "quiz" in path:
        return "quiz"
    if "/collections/" in path:
        return "collection"
    if path in ("", "/"):
        return "homepage"
    return "khác"


def load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(text.splitlines()))
    if path.suffix.lower() == ".jsonl":
        return [json.loads(l) for l in text.splitlines() if l.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        for k in ("data", "ads", "results", "items"):
            if isinstance(data.get(k), list):
                return data[k]
        return [data]
    return data


def bar(n: int, scale: float) -> str:
    return "█" * max(0, round(n * scale))


def analyze(rows: list[dict], as_of: date, brand_domain: str | None, top_n: int) -> dict:
    ads = []
    skipped = 0
    for r in rows:
        sd = parse_date(pick(r, "start_date"))
        if not sd:
            skipped += 1
            continue
        ed = parse_date(pick(r, "end_date"))
        active = parse_bool(pick(r, "is_active"))
        if active is None:
            active = ed is None or ed >= as_of
        end_for_age = as_of if active else (ed or as_of)
        days = max(1, (end_for_age - sd).days + 1)
        dup = parse_int(pick(r, "duplicates"), 1)
        media = classify_media(pick(r, "media_type"), r)
        ads.append({
            "id": str(pick(r, "id") or f"row{len(ads)+1}"),
            "start_date": sd.isoformat(),
            "end_date": ed.isoformat() if ed else None,
            "active": active,
            "days_running": days,
            "duplicates": dup,
            "media_type": media,
            "landing_url": pick(r, "landing_url"),
            "landing_type": classify_landing(pick(r, "landing_url"), brand_domain),
            "video_url": pick(r, "video_url"),
            "body": (str(pick(r, "body") or "")[:180]).replace("\n", " "),
            # Winner score: chạy càng lâu + nhân bản càng nhiều = càng chắc là ad ra tiền
            "winner_score": round(days * (1 + math.log(max(dup, 1))), 1),
        })

    active_ads = [a for a in ads if a["active"]]
    starts = sorted(date.fromisoformat(a["start_date"]) for a in ads)

    def new_in(n):
        return sum(1 for d in starts if (as_of - d).days < n)

    # Histogram 12 tuần gần nhất (tuần kết thúc tại as_of)
    weeks = []
    for w in range(11, -1, -1):
        wk_end = as_of - timedelta(days=7 * w)
        wk_start = wk_end - timedelta(days=6)
        n = sum(1 for d in starts if wk_start <= d <= wk_end)
        weeks.append({"week_start": wk_start.isoformat(), "week_end": wk_end.isoformat(), "new_ads": n})
    last8 = weeks[-8:]
    weeks_with_launch = sum(1 for w in last8 if w["new_ads"] > 0)
    launch_counts = [w["new_ads"] for w in last8]
    mean8 = sum(launch_counts) / 8
    var8 = sum((c - mean8) ** 2 for c in launch_counts) / 8
    cv = math.sqrt(var8) / mean8 if mean8 else None

    uniq_days = sorted(set(starts))
    gaps = [(b - a).days for a, b in zip(uniq_days, uniq_days[1:])]
    median_gap = sorted(gaps)[len(gaps) // 2] if gaps else None
    last_launch = uniq_days[-1] if uniq_days else None
    days_since_last = (as_of - last_launch).days if last_launch else None

    if not ads:
        cadence = "không có dữ liệu"
    elif days_since_last is not None and days_since_last > 21:
        cadence = f"NGƯNG ra ad mới ({days_since_last} ngày chưa có ad mới), có thể đang vắt winner cũ hoặc bỏ sản phẩm"
    elif weeks_with_launch >= 6 and (cv is None or cv < 1.0):
        cadence = "RA AD ĐỀU: tuần nào cũng có ad mới, đang test creative liên tục (tín hiệu đang scale nghiêm túc)"
    elif weeks_with_launch >= 4:
        cadence = "RA AD THEO ĐỢT: launch từng batch, xen kẽ tuần nghỉ"
    else:
        cadence = "CHỮNG: ít ad mới trong 8 tuần gần đây"

    n_active = len(active_ads)
    if n_active >= 200:
        scale = "SCALE MẠNH (≥200 ad active)"
    elif n_active >= 50:
        scale = "ĐANG SCALE (50–199 ad active)"
    elif n_active >= 10:
        scale = "SCALE NHẸ / TEST RỘNG (10–49 ad active)"
    elif n_active > 0:
        scale = "ĐANG TEST (<10 ad active)"
    else:
        scale = "KHÔNG CÓ AD ACTIVE"

    age_buckets = Counter()
    for a in active_ads:
        d = a["days_running"]
        age_buckets["<7 ngày" if d < 7 else "7–30 ngày" if d <= 30 else "31–90 ngày" if d <= 90 else ">90 ngày"] += 1

    media_mix = Counter(a["media_type"] for a in active_ads or ads)
    landing_mix = Counter(a["landing_type"] for a in active_ads or ads)
    landing_urls = Counter((a["landing_url"] or "").split("?")[0] for a in active_ads or ads if a["landing_url"])

    ranked = sorted(ads, key=lambda a: (a["active"], a["winner_score"]), reverse=True)
    top_videos = [a for a in ranked if a["media_type"] == "video"][:top_n]

    return {
        "as_of": as_of.isoformat(),
        "total_ads": len(ads),
        "skipped_rows_no_date": skipped,
        "active_ads": n_active,
        "scale_verdict": scale,
        "new_ads": {"7d": new_in(7), "14d": new_in(14), "30d": new_in(30)},
        "weekly_launches": weeks,
        "weeks_with_launch_last8": weeks_with_launch,
        "launch_cv_last8": round(cv, 2) if cv is not None else None,
        "median_gap_days": median_gap,
        "days_since_last_launch": days_since_last,
        "cadence_verdict": cadence,
        "active_age_buckets": dict(age_buckets),
        "media_mix": dict(media_mix),
        "landing_mix": dict(landing_mix),
        "top_landing_urls": landing_urls.most_common(5),
        "top_ads": ranked[:15],
        "top_videos": top_videos,
    }


def to_md(r: dict) -> str:
    L = []
    L.append(f"# Scale & nhịp ra ad (tính đến {r['as_of']})\n")
    L.append(f"- **Mức scale:** {r['scale_verdict']}")
    L.append(f"- **Ad active / tổng đã thu thập:** {r['active_ads']} / {r['total_ads']}")
    L.append(f"- **Ad mới:** 7 ngày: {r['new_ads']['7d']} · 14 ngày: {r['new_ads']['14d']} · 30 ngày: {r['new_ads']['30d']}")
    L.append(f"- **Nhịp ra ad:** {r['cadence_verdict']}")
    L.append(f"- Tuần có ad mới (8 tuần gần nhất): {r['weeks_with_launch_last8']}/8 · "
             f"khoảng cách trung vị giữa 2 ngày launch: {r['median_gap_days']} ngày · "
             f"lần launch gần nhất cách đây: {r['days_since_last_launch']} ngày")
    if r["skipped_rows_no_date"]:
        L.append(f"- ⚠️ Bỏ qua {r['skipped_rows_no_date']} dòng không đọc được ngày bắt đầu")
    L.append("\n## Ad mới theo tuần (12 tuần)\n")
    L.append("```")
    mx = max([w["new_ads"] for w in r["weekly_launches"]] + [1])
    sc = 40 / mx
    for w in r["weekly_launches"]:
        L.append(f"{w['week_start']} → {w['week_end']} | {w['new_ads']:>4} {bar(w['new_ads'], sc)}")
    L.append("```")
    L.append("\n## Tuổi của ad đang active\n")
    for k in ["<7 ngày", "7–30 ngày", "31–90 ngày", ">90 ngày"]:
        L.append(f"- {k}: {r['active_age_buckets'].get(k, 0)}")
    L.append("\n> Ad active >30 ngày gần như chắc chắn đang có lãi, vì không ai đốt tiền 1 tháng cho ad lỗ.")
    L.append("\n## Media mix\n")
    for k, v in sorted(r["media_mix"].items(), key=lambda x: -x[1]):
        L.append(f"- {k}: {v}")
    L.append("\n## Landing page ad trỏ về\n")
    for k, v in sorted(r["landing_mix"].items(), key=lambda x: -x[1]):
        L.append(f"- {k}: {v}")
    if r["top_landing_urls"]:
        L.append("\nURL được trỏ nhiều nhất:")
        for u, n in r["top_landing_urls"]:
            L.append(f"- `{u}` ({n} ad)")
    L.append("\n## Ứng viên winner (xếp theo winner score = số ngày chạy × (1 + ln(số bản nhân)))\n")
    L.append("| # | ID | Active | Bắt đầu | Ngày chạy | Bản nhân | Loại | Score | Text |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, a in enumerate(r["top_ads"], 1):
        L.append(f"| {i} | {a['id']} | {'✅' if a['active'] else '—'} | {a['start_date']} | {a['days_running']} | "
                 f"{a['duplicates']} | {a['media_type']} | {a['winner_score']} | {a['body'][:70].replace('|', '/')} |")
    L.append("\n## 🎯 5 video top đề xuất để mổ angle\n")
    if not r["top_videos"]:
        L.append("_Không có ad video nào trong dữ liệu._")
    for i, a in enumerate(r["top_videos"], 1):
        L.append(f"{i}. **{a['id']}**: chạy {a['days_running']} ngày, {a['duplicates']} bản nhân, "
                 f"{'đang active' if a['active'] else 'đã tắt'} · video: {a['video_url'] or '(chưa có link)'}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", "-i", required=True, help="CSV/JSON/JSONL danh sách ad")
    ap.add_argument("--as-of", help="Ngày tham chiếu YYYY-MM-DD (mặc định hôm nay)")
    ap.add_argument("--brand-domain", help="Domain shop đối thủ, ví dụ brand.com (để phát hiện presell domain khác)")
    ap.add_argument("--top", type=int, default=5, help="Số video top cần chọn (mặc định 5)")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    a = ap.parse_args()

    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    bd = a.brand_domain.lower().removeprefix("www.") if a.brand_domain else None
    res = analyze(load_rows(Path(a.input)), as_of, bd, a.top)
    md = to_md(res)
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    if not a.out_md:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()

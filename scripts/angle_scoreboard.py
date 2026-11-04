#!/usr/bin/env python3
"""angle_scoreboard.py: Tìm angle / ad / bài MẠNH NHẤT của đối thủ trên Meta Ads + Instagram, chỉ bằng dữ liệu công khai.

Không ước tính CPC/ROAS (đối thủ không công khai). Mặc định --focus meta-ig: chỉ chấm bài Instagram/Facebook
và ad có placement Facebook/Instagram.

Tín hiệu META ADS (Ad Library, 50%):
  - ad active chạy lâu nhất · ad active + ad mới 30 ngày · tổng bản nhân (collation) · lượt tiếp cận EU (nếu có)
  - ad hợp tác creator (Paid partnership): đối thủ thuê creator chạy = angle đã đủ tin để đầu tư
Tín hiệu INSTAGRAM (organic, Reels, bài affiliate/UGC, 50%):
  - view/follower (reel vượt tập follower = angle lan tự nhiên) · tỉ lệ tương tác · % bình luận muốn mua
  - số creator khác nhau cùng đánh angle · view trung vị
Trừ điểm theo % bình luận chê/nghi ngờ (tối đa −50%).

Input:
  --posts        (lặp lại) posts.csv từ ig_collect.py (hoặc CSV cùng cột), hoặc slug:file.info.json
  --comments-dir 04-comments (comments.jsonl + labels)                      [tuỳ chọn]
  --ads          ads.json từ adlib_parse.py / ad_cadence (CSV/JSON)          [tuỳ chọn]
  --angle-map    CSV ad_id,angle[,angle_name]                                 [tuỳ chọn, cần cho tín hiệu Meta theo angle]
  --focus        meta-ig (mặc định) | all
  --assign 5 · --top 10

Output: scoreboard.md + scoreboard.json (test_readout.py --scoreboard đọc lại).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ad_cadence import load_rows, parse_bool, parse_date, parse_int, pick  # noqa: E402
from csvio import brief, parse_count, read_csv_rows  # noqa: E402

WEIGHTS = {
    "meta-ig": {
        # Meta Ads
        "ad_longevity": .15, "ad_volume": .10, "ad_dupes": .08, "eu_reach": .12, "partnership": .05,
        # Instagram
        "views_per_follower": .12, "engagement": .10, "buy_intent": .12, "spread": .08, "reach": .05, "share_rate": .03,
    },
    "all": {
        "ad_longevity": .15, "ad_volume": .10, "ad_dupes": .05, "eu_reach": .05, "partnership": .03,
        "views_per_follower": .07, "engagement": .15, "buy_intent": .15, "spread": .10, "reach": .07, "share_rate": .08,
    },
}
LABEL = {"ad_longevity": "ad sống lâu", "ad_volume": "số ad active + mới", "ad_dupes": "bản nhân", "eu_reach": "tiếp cận EU",
         "partnership": "hợp tác creator", "views_per_follower": "view/follower", "engagement": "tương tác",
         "buy_intent": "muốn mua", "spread": "số creator", "reach": "view trung vị", "share_rate": "share"}
META_PLATFORMS = ("instagram", "facebook")


def fnum(v):
    n = parse_count(v)
    return float(n) if n is not None else None


def truthy(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "y", "x")


def norm_url(u) -> str:
    return (u or "").split("?")[0].rstrip("/").lower()


def load_jsonl(p: Path) -> list[dict]:
    out = []
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    return out


def norm(vals: dict) -> dict | None:
    known = [v for v in vals.values() if v is not None]
    if not known or max(known) <= 0:
        return None
    mx = max(known)
    return {k: (v / mx if v is not None else 0.0) for k, v in vals.items()}


def norm_log(vals: dict) -> dict | None:
    """Min–max trên thang log: phân biệt được 100K với 1M view (chuẩn hoá theo max thì log nén mọi thứ về ~0.8–1)."""
    lv = {k: math.log10(v) for k, v in vals.items() if v and v > 0}
    if not lv:
        return None
    lo, hi = min(lv.values()), max(lv.values())
    return {k: ((lv[k] - lo) / (hi - lo) * .8 + .2 if hi > lo else 1.0) if k in lv else 0.0 for k in vals}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--posts", action="append", default=[])
    ap.add_argument("--comments-dir")
    ap.add_argument("--ads")
    ap.add_argument("--angle-map")
    ap.add_argument("--names")
    ap.add_argument("--focus", choices=list(WEIGHTS), default="meta-ig")
    ap.add_argument("--assign", type=int, default=5)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--as-of")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    if not a.posts and not a.ads:
        sys.exit("Cần ít nhất --posts hoặc --ads")
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    names: dict[str, str] = {}
    meta_only = a.focus == "meta-ig"

    # ---------- Bài đăng ----------
    posts = defaultdict(list)
    all_posts = []
    url2angle = {}
    skipped_platform = 0
    for spec in a.posts:
        slug, path = (spec.split(":", 1) if ":" in spec and not Path(spec).exists() else (None, spec))
        if path.endswith(".json"):
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            rows = [{"angle": slug, "platform": (d.get("extractor_key") or d.get("extractor") or "").lower(),
                     "url": d.get("webpage_url"), "creator": d.get("uploader") or d.get("channel"),
                     "views": d.get("view_count"), "likes": d.get("like_count"), "comments": d.get("comment_count"),
                     "shares": d.get("repost_count"), "followers": d.get("channel_follower_count")}]
        else:
            rows = read_csv_rows(path)
        for r in rows:
            plat = (r.get("platform") or "instagram").lower()
            if meta_only and not any(p in plat for p in META_PLATFORMS):
                skipped_platform += 1
                continue
            v = fnum(r.get("views"))
            ang = (r.get("angle") or slug or "").strip()
            p = {k: fnum(r.get(k)) or 0 for k in ("likes", "comments", "shares", "saves")}
            p.update(views=v, followers=fnum(r.get("followers")), creator=(r.get("creator") or "").strip().lower() or None,
                     platform=plat, url=r.get("url"), angle=ang or None, partnership=truthy(r.get("is_partnership")),
                     caption=(r.get("caption") or "")[:90])
            all_posts.append(p)
            if r.get("url") and ang:
                url2angle[norm_url(r["url"])] = ang
            if not ang or not v:
                continue
            if r.get("angle_name"):
                names[ang] = r["angle_name"]
            posts[ang].append(p)

    # ---------- Bình luận ----------
    cstat = defaultdict(lambda: {"n": 0, "buy": 0, "neg": 0})
    if a.comments_dir:
        cd = Path(a.comments_dir)
        from comments import load_labels  # đọc cả nhãn mã ngắn (labels.txt) lẫn JSON cũ
        comments = {c["id"]: c for c in load_jsonl(cd / "comments.jsonl")}
        raw = load_labels(cd)
        labels = []
        for cid, c in comments.items():       # bản gần trùng dùng nhãn của bản đại diện
            lab = raw.get(cid) or raw.get(c.get("rep"))
            if lab:
                labels.append({**lab, "id": cid})
        for l in labels:
            c = comments.get(l.get("id"))
            ang = url2angle.get(norm_url(c.get("source_url"))) if c else None
            if not ang:
                continue
            s = cstat[ang]
            s["n"] += 1
            t, topics = l.get("type"), l.get("topics") or []
            s["buy"] += t == "purchase_intent" or (t == "question" and "price" in topics)
            s["neg"] += t in ("complaint", "skeptic")

    # ---------- Ad Library ----------
    ads = defaultdict(lambda: {"ads": 0, "active": 0, "new30": 0, "max_days": 0, "dups": 0, "reach": 0,
                               "reach_n": 0, "partner": 0, "ig": 0, "plat_known": 0})
    all_ads = []
    amap = {}
    if a.angle_map:
        for r in read_csv_rows(a.angle_map):
            if r.get("ad_id") and r.get("angle"):
                amap[str(r["ad_id"]).strip()] = r["angle"].strip()
                if r.get("angle_name"):
                    names.setdefault(r["angle"].strip(), r["angle_name"].strip())
    if a.ads:
        for r in load_rows(Path(a.ads)):
            sd = parse_date(pick(r, "start_date"))
            if not sd:
                continue
            plats = str(pick(r, "platforms") or "").lower()
            if meta_only and plats and not any(p in plats for p in META_PLATFORMS):
                continue
            ed = parse_date(pick(r, "end_date"))
            act = parse_bool(pick(r, "is_active"))
            act = (ed is None or ed >= as_of) if act is None else act
            days = max(1, ((as_of if act else (ed or as_of)) - sd).days + 1)
            dup = parse_int(pick(r, "duplicates"), 1)
            reach = parse_int(pick(r, "eu_reach"), 0)
            partner = bool(parse_bool(pick(r, "partnership"))) or "paid partnership" in str(pick(r, "body") or "").lower()
            aid = str(pick(r, "id") or "")
            ang = amap.get(aid)
            ad = {"id": aid, "angle": ang, "active": act, "days": days, "dups": dup, "reach": reach or None,
                  "partner": partner, "platforms": plats or None, "body": str(pick(r, "body") or "")[:90].replace("\n", " "),
                  "video_url": pick(r, "video_url"), "start": sd.isoformat()}
            all_ads.append(ad)
            if not ang:
                continue
            x = ads[ang]
            x["ads"] += 1
            x["dups"] += dup
            x["new30"] += (as_of - sd).days < 30
            x["partner"] += partner
            if plats:
                x["plat_known"] += 1
                x["ig"] += "instagram" in plats
            if reach:
                x["reach"] += reach
                x["reach_n"] += 1
            if act:
                x["active"] += 1
                x["max_days"] = max(x["max_days"], days)
    if a.names:
        for r in read_csv_rows(a.names):
            names[r["angle"].strip()] = r["angle_name"].strip()

    angles = sorted(set(posts) | set(ads))
    if not angles:
        n_unassigned = sum(1 for p in all_posts if not p["angle"])
        print(f"⚠️ Chưa có angle nào để chấm: {n_unassigned} bài và {len(all_ads)} ad chưa được gán angle "
              f"(cột angle trong posts.csv / file --angle-map). Vẫn xuất Top ad/bài bên dưới.", file=sys.stderr)
    m = {}
    for k in angles:
        ps = posts.get(k, [])
        V = sum(p["views"] for p in ps)
        inter = sum(p["likes"] + p["comments"] + p["shares"] + p["saves"] for p in ps)
        vf = [p["views"] / p["followers"] for p in ps if p["followers"]]
        cs, ad = cstat.get(k), ads.get(k)
        m[k] = {
            "posts": len(ps), "creators": len({p["creator"] for p in ps if p["creator"]}) or len(ps),
            "views_total": int(V), "views_median": int(st.median([p["views"] for p in ps])) if ps else None,
            "engagement_rate": round(inter / V * 100, 2) if V else None,
            "share_rate": round(sum(p["shares"] for p in ps) / V * 100, 3) if V and any(p["shares"] for p in ps) else None,
            "views_per_follower": round(st.median(vf), 2) if vf else None,
            "partnership_posts": sum(p["partnership"] for p in ps),
            "comments_labeled": cs["n"] if cs else 0,
            "buy_intent_pct": round(cs["buy"] / cs["n"] * 100, 1) if cs and cs["n"] else None,
            "negative_pct": round(cs["neg"] / cs["n"] * 100, 1) if cs and cs["n"] else None,
            "ads": ad["ads"] if ad else None, "ads_active": ad["active"] if ad else None,
            "ads_new_30d": ad["new30"] if ad else None, "ad_max_days_active": ad["max_days"] if ad else None,
            "ad_duplicates": ad["dups"] if ad else None,
            "eu_reach_total": ad["reach"] if ad and ad["reach_n"] else None,
            "partnership_ads": ad["partner"] if ad else None,
            "instagram_ads_pct": round(ad["ig"] / ad["plat_known"] * 100) if ad and ad["plat_known"] else None,
        }

    comp = {
        "ad_longevity": norm({k: min(m[k]["ad_max_days_active"], 120) if m[k]["ad_max_days_active"] else None for k in angles}),
        "ad_volume": norm({k: math.log1p(m[k]["ads_active"] + m[k]["ads_new_30d"]) if m[k]["ads"] else None for k in angles}),
        "ad_dupes": norm({k: math.log1p(m[k]["ad_duplicates"]) if m[k]["ad_duplicates"] else None for k in angles}),
        "eu_reach": norm_log({k: m[k]["eu_reach_total"] for k in angles}),
        "partnership": norm({k: ((m[k]["partnership_ads"] or 0) + m[k]["partnership_posts"]) or None for k in angles}),
        "views_per_follower": norm({k: m[k]["views_per_follower"] for k in angles}),
        "engagement": norm({k: m[k]["engagement_rate"] for k in angles}),
        "buy_intent": norm({k: m[k]["buy_intent_pct"] for k in angles}),
        "spread": norm({k: m[k]["creators"] or None for k in angles}),
        "reach": norm_log({k: m[k]["views_median"] for k in angles}),
        "share_rate": norm({k: m[k]["share_rate"] for k in angles}),
    }
    used = {c: w for c, w in WEIGHTS[a.focus].items() if comp[c] is not None}
    tw = sum(used.values()) or 1

    out = []
    for k in angles:
        raw = sum(comp[c][k] * w for c, w in used.items()) / tw
        neg = (m[k]["negative_pct"] or 0) / 100
        score = round(100 * raw * (1 - 0.5 * min(neg, 1)))
        strengths = sorted(((comp[c][k] * w, c) for c, w in used.items() if comp[c][k] >= .8), reverse=True)
        evidence = sum([m[k]["posts"] >= 3, m[k]["views_total"] >= 100_000, m[k]["comments_labeled"] >= 50,
                        (m[k]["ads_active"] or 0) > 0, bool(m[k]["eu_reach_total"])])
        out.append({"angle": k, "angle_name": names.get(k, k), **m[k], "signal_score": score,
                    "strengths": [LABEL[c] for _, c in strengths[:3]],
                    "confidence": "Cao" if evidence >= 3 else "TB" if evidence == 2 else "Thấp"})
    out.sort(key=lambda x: -x["signal_score"])
    for i, x in enumerate(out):
        x["test_code"] = f"A{i+1}" if i < a.assign else None

    # ---------- Top ad / top bài ----------
    max_reach = max([x["reach"] for x in all_ads if x["reach"]] + [0])
    for x in all_ads:
        x["strength"] = round((x["days"] if x["active"] else x["days"] * .5) * (1 + math.log(max(x["dups"], 1)))
                              * (1 + (x["reach"] / max_reach if max_reach and x["reach"] else 0)) * (1.15 if x["partner"] else 1), 1)
    top_ads = sorted(all_ads, key=lambda x: -x["strength"])[: a.top]
    vp = [p for p in all_posts if p["views"]]
    mx_v = max([math.log10(p["views"]) for p in vp] + [1])
    vpfs = [p["views"] / p["followers"] for p in vp if p["followers"]]
    mx_vpf = max(vpfs + [1])
    ers = [(p["likes"] + p["comments"] + p["shares"] + p["saves"]) / p["views"] for p in vp]
    mx_er = max(ers + [1e-9])
    for p in vp:
        er = (p["likes"] + p["comments"] + p["shares"] + p["saves"]) / p["views"]
        vpf = p["views"] / p["followers"] if p["followers"] else None
        p["strength"] = round(100 * (.45 * math.log10(p["views"]) / mx_v + .35 * (min(vpf, mx_vpf) / mx_vpf if vpf else 0) + .20 * er / mx_er))
        p["vpf"] = round(vpf, 2) if vpf else None
        p["er"] = round(er * 100, 2)
    top_posts = sorted(vp, key=lambda p: -p["strength"])[: a.top]

    def f(v, suf=""):
        return "—" if v is None else f"{v:,}{suf}" if isinstance(v, int) else f"{v}{suf}"

    L = [f"# Angle mạnh nhất trên {'Meta Ads + Instagram' if meta_only else 'mọi nền tảng'}\n",
         "Chỉ dùng số công khai (Ad Library + bài Instagram/Facebook). Không ước tính CPC/ROAS của đối thủ.\n",
         "- Trọng số: " + ", ".join(f"{LABEL[c]} {w/tw:.0%}" for c, w in used.items()) + " · trừ điểm theo % bình luận chê/nghi ngờ"]
    if skipped_platform:
        L.append(f"- Bỏ qua {skipped_platform} bài ngoài Facebook/Instagram (dùng --focus all để tính cả)")
    L.append("")
    L.append("| Mã | Angle | Điểm | Ad active · lâu nhất | Bản nhân | Tiếp cận EU | % ad IG | Hợp tác | Bài IG · creator | View/follower | Tương tác | Muốn mua | Chê | Tin cậy |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for x in out:
        adcol = f"{x['ads_active']} · {x['ad_max_days_active']} ngày" if x["ads"] else "—"
        part = (x["partnership_ads"] or 0) + x["partnership_posts"]
        L.append(f"| {x['test_code'] or ''} | {x['angle_name']} | **{x['signal_score']}** | {adcol} | {f(x['ad_duplicates'])} | "
                 f"{f(x['eu_reach_total'])} | {f(x['instagram_ads_pct'], '%')} | {part or '—'} | {x['posts']} · {x['creators']} | "
                 f"{f(x['views_per_follower'], '×')} | {f(x['engagement_rate'], '%')} | {f(x['buy_intent_pct'], '%')} | "
                 f"{f(x['negative_pct'], '%')} | {x['confidence']} |")

    L.append(f"\n## 🏆 Top {len(top_ads)} ad mạnh nhất trên Meta\n")
    if top_ads:
        L.append("Điểm = số ngày chạy × (1 + ln bản nhân) × (1 + tiếp cận EU tương đối) × 1.15 nếu hợp tác creator; ad đã tắt tính nửa số ngày.\n")
        L.append("| # | Ad ID | Angle | Active | Ngày | Bản nhân | Tiếp cận EU | IG | Hợp tác | Điểm | Nội dung |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for i, x in enumerate(top_ads, 1):
            ig = ("✅" if "instagram" in x["platforms"] else "—") if x["platforms"] else "?"
            L.append(f"| {i} | {x['id']} | {names.get(x['angle'], x['angle']) or '_chưa gán_'} | {'✅' if x['active'] else '—'} | {x['days']} | "
                     f"{x['dups']} | {f(x['reach'])} | {ig} | {'✅' if x['partner'] else ''} | {x['strength']} | {x['body'].replace('|', '/')} |")
    else:
        L.append("_Chưa có dữ liệu ad (--ads)._")
    L.append(f"\n## 📸 Top {len(top_posts)} bài Instagram mạnh nhất\n")
    if top_posts:
        L.append("Điểm = 45% view (log) + 35% view/follower + 20% tỉ lệ tương tác.\n")
        L.append("| # | Bài | Creator | Angle | View | View/follower | Tương tác | Hợp tác | Điểm |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for i, p in enumerate(top_posts, 1):
            L.append(f"| {i} | {p['url'] or '—'} | {p['creator'] or '—'} | {names.get(p['angle'], p['angle']) or '_chưa gán_'} | "
                     f"{int(p['views']):,} | {f(p['vpf'], '×')} | {p['er']}% | {'✅' if p['partnership'] else ''} | {p['strength']} |")
    else:
        L.append("_Chưa có dữ liệu bài (--posts)._")

    L.append("\n## → Đưa sang bước test angle\n")
    for x in out[: a.assign]:
        why = list(x["strengths"])
        if x["negative_pct"] and x["negative_pct"] >= 25:
            why.append(f"⚠️ {x['negative_pct']}% bình luận chê, cần xử lý objection trong video")
        L.append(f"- **{x['test_code']}: {x['angle_name']}** (điểm {x['signal_score']}, tin cậy {x['confidence']})"
                 + (": mạnh ở " + ", ".join(why) if why else ""))
    L.append("\nVideo tham chiếu cho mỗi angle: ưu tiên ad mạnh nhất của angle đó trong bảng Top ad, không có thì lấy bài IG mạnh nhất. "
             f"Ngân sách test **chia đều** {min(a.assign, len(out))} angle.")
    md = "\n".join(L) + "\n"
    res = {"as_of": as_of.isoformat(), "focus": a.focus, "weights": used, "angles": out,
           "top_ads": top_ads, "top_posts": [{k: v for k, v in p.items()} for p in top_posts]}
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
        tops = [f"Top ad: " + " · ".join(f"{x['id']} ({x['days']}d, {x['dups']} bản)" for x in top_ads[:3]),
                f"Top bài IG: " + " · ".join(f"{p['url']} ({int(p['views']):,} view)" for p in top_posts[:3])]
        print(brief(md, a.out_md, 6 + min(len(out), 8)) + "\n" + "\n".join(tops))
    else:
        print(md)


if __name__ == "__main__":
    main()

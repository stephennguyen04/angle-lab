#!/usr/bin/env python3
"""angle_scoreboard.py: Chấm điểm ANGLE của đối thủ CHỈ bằng dữ liệu công khai trên mạng xã hội → chọn A1–A5 để test.

Không ước tính CPC/ROAS (đối thủ không công khai). Chỉ dùng thứ nhìn thấy được:
  Bài đăng (TikTok / Instagram / Facebook / YouTube, organic, Spark, affiliate):
    - view, like, comment, share, save · số creator khác nhau đăng cùng angle · view so với follower
  Bình luận (từ /angle-lab:comments, nối theo URL bài):
    - % muốn mua (purchase_intent + hỏi giá/link) · % chê + nghi ngờ
  Ad Library (công khai, tuỳ chọn):
    - số ad, ad active, ad chạy lâu nhất, ad mới 30 ngày

Input:
  --posts        (lặp lại) CSV angle,platform,url,creator,views,likes,comments,shares,saves,followers,date
                 hoặc slug:file.info.json (yt-dlp: view_count, like_count, comment_count, repost_count, uploader…)
  --comments-dir 04-comments (comments.jsonl + labels.jsonl / labels/*.jsonl)  [tuỳ chọn]
  --ads + --angle-map (ad_id,angle[,angle_name])                              [tuỳ chọn]
  --names        CSV angle,angle_name                                           [tuỳ chọn]
  --assign 5     gán A1..An cho n angle điểm cao nhất

Output: scoreboard.md + scoreboard.json (test_readout.py --scoreboard đọc lại để so dự đoán vs thực tế).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ad_cadence import load_rows, parse_bool, parse_date, parse_int, pick  # noqa: E402

WEIGHTS = {  # tổng 1.0, tự chuẩn hoá lại nếu thiếu dữ liệu
    "share_rate": .20,     # share/view: người xem thấy "đúng mình", gửi cho người khác → angle chạm nỗi đau thật
    "engagement": .15,     # (like+comment+share+save)/view
    "reach": .15,          # median view/bài (log)
    "buy_intent": .15,     # % bình luận muốn mua / hỏi giá, link
    "spread": .10,         # số creator khác nhau cùng đánh angle (affiliate/UGC copy = angle bán được)
    "ad_longevity": .15,   # ad active chạy lâu nhất (Ad Library)
    "ad_volume": .10,      # ad active + ad mới 30 ngày (Ad Library)
}


def fnum(v):
    if v in (None, ""):
        return None
    try:
        s = str(v).replace(",", "").strip().lower()
        mult = 1000 if s.endswith("k") else 1_000_000 if s.endswith("m") else 1
        return float(s.rstrip("km")) * mult
    except ValueError:
        return None


def read_csv(p: str) -> list[dict]:
    return list(csv.DictReader(Path(p).read_text(encoding="utf-8-sig").splitlines()))


def norm_url(u: str | None) -> str:
    return (u or "").split("?")[0].rstrip("/").lower()


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def norm(vals: dict) -> dict | None:
    known = [v for v in vals.values() if v is not None]
    if not known:
        return None
    mx = max(known)
    return {k: (v / mx if mx and v is not None else 0.0) for k, v in vals.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--posts", action="append", default=[], required=True)
    ap.add_argument("--comments-dir")
    ap.add_argument("--ads")
    ap.add_argument("--angle-map")
    ap.add_argument("--names")
    ap.add_argument("--assign", type=int, default=5)
    ap.add_argument("--as-of")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    names: dict[str, str] = {}

    # ---- Bài đăng ----
    posts = defaultdict(list)
    url2angle = {}
    for spec in a.posts:
        slug, path = (spec.split(":", 1) if ":" in spec and not Path(spec).exists() else (None, spec))
        if path.endswith(".json"):
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            rows = [{"angle": slug, "platform": d.get("extractor_key") or d.get("extractor"), "url": d.get("webpage_url"),
                     "creator": d.get("uploader") or d.get("channel"), "views": d.get("view_count"), "likes": d.get("like_count"),
                     "comments": d.get("comment_count"), "shares": d.get("repost_count"), "saves": d.get("save_count"),
                     "followers": d.get("channel_follower_count"), "date": d.get("upload_date")}]
        else:
            rows = read_csv(path)
        for r in rows:
            ang = (r.get("angle") or slug or "").strip()
            v = fnum(r.get("views"))
            if not ang or not v:
                continue
            if r.get("angle_name"):
                names[ang] = r["angle_name"]
            p = {k: fnum(r.get(k)) or 0 for k in ("likes", "comments", "shares", "saves")}
            p.update(views=v, followers=fnum(r.get("followers")), creator=(r.get("creator") or "").strip().lower() or None,
                     platform=(r.get("platform") or "").lower(), url=r.get("url"))
            posts[ang].append(p)
            if r.get("url"):
                url2angle[norm_url(r["url"])] = ang

    # ---- Bình luận (đã gắn nhãn) ----
    cstat = defaultdict(lambda: {"n": 0, "buy": 0, "neg": 0})
    if a.comments_dir:
        cd = Path(a.comments_dir)
        comments = {c["id"]: c for c in load_jsonl(cd / "comments.jsonl")}
        labels = load_jsonl(cd / "labels.jsonl")
        for lf in sorted((cd / "labels").glob("*.jsonl")) if (cd / "labels").exists() else []:
            labels += load_jsonl(lf)
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

    # ---- Ad Library ----
    ads = defaultdict(lambda: {"ads": 0, "active": 0, "new30": 0, "max_days": 0})
    if a.ads and a.angle_map:
        amap = {}
        for r in read_csv(a.angle_map):
            if r.get("ad_id") and r.get("angle"):
                amap[str(r["ad_id"]).strip()] = r["angle"].strip()
                if r.get("angle_name"):
                    names.setdefault(r["angle"].strip(), r["angle_name"].strip())
        for r in load_rows(Path(a.ads)):
            ang, sd = amap.get(str(pick(r, "id") or "")), parse_date(pick(r, "start_date"))
            if not ang or not sd:
                continue
            ed = parse_date(pick(r, "end_date"))
            act = parse_bool(pick(r, "is_active"))
            act = (ed is None or ed >= as_of) if act is None else act
            x = ads[ang]
            x["ads"] += 1
            x["new30"] += (as_of - sd).days < 30
            if act:
                x["active"] += 1
                x["max_days"] = max(x["max_days"], (as_of - sd).days + 1)
    if a.names:
        for r in read_csv(a.names):
            names[r["angle"].strip()] = r["angle_name"].strip()

    angles = sorted(set(posts) | set(ads))
    if not angles:
        sys.exit("Không có dữ liệu bài đăng nào khớp angle.")

    m = {}
    for k in angles:
        ps = posts.get(k, [])
        V = sum(p["views"] for p in ps)
        inter = sum(p["likes"] + p["comments"] + p["shares"] + p["saves"] for p in ps)
        vf = [p["views"] / p["followers"] for p in ps if p["followers"]]
        cs = cstat.get(k)
        ad = ads.get(k)
        m[k] = {
            "posts": len(ps), "platforms": sorted({p["platform"] for p in ps if p["platform"]}),
            "creators": len({p["creator"] for p in ps if p["creator"]}) or (len(ps) if ps else 0),
            "views_total": int(V), "views_median": int(st.median([p["views"] for p in ps])) if ps else None,
            "engagement_rate": round(inter / V * 100, 2) if V else None,
            "share_rate": round(sum(p["shares"] for p in ps) / V * 100, 3) if V else None,
            "save_rate": round(sum(p["saves"] for p in ps) / V * 100, 3) if V and any(p["saves"] for p in ps) else None,
            "views_per_follower": round(st.median(vf), 2) if vf else None,
            "comments_labeled": cs["n"] if cs else 0,
            "buy_intent_pct": round(cs["buy"] / cs["n"] * 100, 1) if cs and cs["n"] else None,
            "negative_pct": round(cs["neg"] / cs["n"] * 100, 1) if cs and cs["n"] else None,
            "ads": ad["ads"] if ad else None, "ads_active": ad["active"] if ad else None,
            "ads_new_30d": ad["new30"] if ad else None, "ad_max_days_active": ad["max_days"] if ad else None,
        }

    comp = {
        "share_rate": norm({k: m[k]["share_rate"] for k in angles}),
        "engagement": norm({k: m[k]["engagement_rate"] for k in angles}),
        "reach": norm({k: math.log10(m[k]["views_median"]) if m[k]["views_median"] else None for k in angles}),
        "buy_intent": norm({k: m[k]["buy_intent_pct"] for k in angles}),
        "spread": norm({k: m[k]["creators"] or None for k in angles}),
        "ad_longevity": norm({k: min(m[k]["ad_max_days_active"], 120) if m[k]["ad_max_days_active"] is not None else None for k in angles}),
        "ad_volume": norm({k: math.log1p(m[k]["ads_active"] + m[k]["ads_new_30d"]) if m[k]["ads"] is not None else None for k in angles}),
    }
    used = {c: w for c, w in WEIGHTS.items() if comp[c] is not None}
    tw = sum(used.values())

    out = []
    for k in angles:
        raw = sum(comp[c][k] * w for c, w in used.items()) / tw
        neg = (m[k]["negative_pct"] or 0) / 100
        score = round(100 * raw * (1 - 0.5 * min(neg, 1)))   # angle bị chê nhiều → trừ điểm
        evidence = sum([m[k]["posts"] >= 3, m[k]["views_total"] >= 100_000, m[k]["comments_labeled"] >= 50,
                        (m[k]["ads_active"] or 0) > 0])
        out.append({"angle": k, "angle_name": names.get(k, k), **m[k], "signal_score": score,
                    "confidence": "Cao" if evidence >= 3 else "TB" if evidence == 2 else "Thấp"})
    out.sort(key=lambda x: -x["signal_score"])
    for i, x in enumerate(out):
        x["test_code"] = f"A{i+1}" if i < a.assign else None

    def f(v, suf=""):
        return "—" if v is None else f"{v:,}{suf}" if isinstance(v, int) else f"{v}{suf}"

    L = ["# Bảng điểm angle (dữ liệu công khai trên mạng xã hội)\n",
         "Chỉ dùng số nhìn thấy được: view, like, comment, share, save, số creator, bình luận, Ad Library. "
         "Không ước tính CPC/ROAS của đối thủ.\n",
         "- Trọng số: " + ", ".join(f"{c} {w/tw:.0%}" for c, w in used.items()) + " · trừ điểm theo % bình luận chê/nghi ngờ\n"]
    L.append("| Mã test | Angle | Điểm | Bài · creator | View trung vị | Tương tác | Share | Muốn mua | Chê | Ad active · lâu nhất | Tin cậy |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for x in out:
        adcol = f"{x['ads_active']} · {x['ad_max_days_active']} ngày" if x["ads"] is not None else "—"
        L.append(f"| {x['test_code'] or ''} | {x['angle_name']} | **{x['signal_score']}** | {x['posts']} · {x['creators']} | "
                 f"{f(x['views_median'])} | {f(x['engagement_rate'], '%')} | {f(x['share_rate'], '%')} | {f(x['buy_intent_pct'], '%')} | "
                 f"{f(x['negative_pct'], '%')} | {adcol} | {x['confidence']} |")
    L.append("\n## → Đưa sang bước test angle\n")
    for x in out[: a.assign]:
        why = []
        if x["share_rate"] is not None and comp["share_rate"] and comp["share_rate"][x["angle"]] >= .8:
            why.append("share cao")
        if x["buy_intent_pct"] and comp["buy_intent"] and comp["buy_intent"][x["angle"]] >= .8:
            why.append("nhiều bình luận muốn mua")
        if x["creators"] >= 3:
            why.append(f"{x['creators']} creator cùng đánh")
        if x["ad_max_days_active"] and x["ad_max_days_active"] >= 30:
            why.append(f"ad sống {x['ad_max_days_active']} ngày")
        if x["negative_pct"] and x["negative_pct"] >= 25:
            why.append(f"⚠️ {x['negative_pct']}% chê, cần xử lý objection trong video")
        L.append(f"- **{x['test_code']}: {x['angle_name']}** (điểm {x['signal_score']}, tin cậy {x['confidence']})"
                 + (": " + ", ".join(why) if why else ""))
    L.append("\nNgân sách test **chia đều** 5 angle. Điểm dùng để chọn angle vào test, không dùng để chia tiền.")
    md = "\n".join(L) + "\n"
    if a.out_json:
        Path(a.out_json).write_text(json.dumps({"as_of": as_of.isoformat(), "weights": used, "angles": out},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()

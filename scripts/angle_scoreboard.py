#!/usr/bin/env python3
"""angle_scoreboard.py: Bảng điểm ANGLE của đối thủ: proof score, CPC ước tính, ROAS sàn suy ra → chọn A1–A5 để test.

⚠️ CPC/ROAS thật của đối thủ KHÔNG công khai (Ad Library không có chi tiêu/click/doanh thu).
Script này chỉ đưa ra con số CÓ CĂN CỨ và ghi rõ nguồn + độ tin cậy:
  - ROAS sàn suy ra : angle có ad active ≥30 ngày ⇒ gần như chắc ROAS ≥ ROAS hoà vốn (không ai đốt tiền 1 tháng cho ad lỗ).
                      ROAS hoà vốn = AOV / (AOV − giá vốn − ship − phí%). Dùng giá vốn của CHÍNH BẠN cho sản phẩm này làm proxy.
  - CPC ước tính    : CPC chuẩn (--bench-cpc: CPC tài khoản bạn hoặc benchmark ngành) ÷ chỉ số tương tác của angle (kẹp 0.6–1.6).
  - Tool spy        : nếu có file ước tính (PiPiAds/Minea/…: est_spend, est_cpc, est_roas) thì lấy trung vị theo angle, ghi nguồn.

Input:
  --ads        ads_raw.json/CSV (cùng định dạng ad_cadence.py)
  --angle-map  CSV: ad_id,angle[,angle_name]  (AI gắn mỗi ad đối thủ vào 1 angle, slug ngắn)
  --posts      (tuỳ chọn, lặp lại) slug:file.info.json (yt-dlp) hoặc CSV angle,views,likes,comments,shares
  --spy-tool   (tuỳ chọn) CSV ad_id,est_spend,est_cpc,est_roas
  --aov --cogs --shipping --fees-pct  để tính ROAS hoà vốn
  --bench-cpc  CPC chuẩn
  --assign 5   gán mã A1..An cho n angle điểm cao nhất

Output: scoreboard.md + scoreboard.json (đọc lại được bởi test_readout.py --scoreboard).
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


def read_csv(p: str) -> list[dict]:
    return list(csv.DictReader(Path(p).read_text(encoding="utf-8-sig").splitlines()))


def fnum(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def norm(vals: dict) -> dict:
    mx = max([v for v in vals.values() if v is not None] + [0])
    return {k: (v / mx if mx and v is not None else 0.0) for k, v in vals.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ads", required=True)
    ap.add_argument("--angle-map", required=True)
    ap.add_argument("--posts", action="append", default=[])
    ap.add_argument("--spy-tool")
    ap.add_argument("--aov", type=float)
    ap.add_argument("--cogs", type=float, default=0)
    ap.add_argument("--shipping", type=float, default=0)
    ap.add_argument("--fees-pct", type=float, default=3)
    ap.add_argument("--bench-cpc", type=float)
    ap.add_argument("--assign", type=int, default=5)
    ap.add_argument("--as-of")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()

    amap, names = {}, {}
    for r in read_csv(a.angle_map):
        aid = str(r.get("ad_id") or r.get("id") or "").strip()
        ang = (r.get("angle") or "").strip()
        if aid and ang:
            amap[aid] = ang
            if r.get("angle_name"):
                names[ang] = r["angle_name"].strip()

    per = defaultdict(lambda: {"ads": 0, "active": 0, "new30": 0, "days_active": [], "dups": 0})
    unmapped = 0
    for r in load_rows(Path(a.ads)):
        aid = str(pick(r, "id") or "")
        ang = amap.get(aid)
        sd = parse_date(pick(r, "start_date"))
        if not ang or not sd:
            unmapped += 1
            continue
        ed = parse_date(pick(r, "end_date"))
        act = parse_bool(pick(r, "is_active"))
        act = (ed is None or ed >= as_of) if act is None else act
        days = max(1, ((as_of if act else (ed or as_of)) - sd).days + 1)
        p = per[ang]
        p["ads"] += 1
        p["dups"] += parse_int(pick(r, "duplicates"), 1)
        p["new30"] += (as_of - sd).days < 30
        if act:
            p["active"] += 1
            p["days_active"].append(days)

    # Tương tác từ bài organic / Spark cùng creative
    eng = defaultdict(lambda: {"views": 0, "inter": 0, "shares": 0, "posts": 0})
    for spec in a.posts:
        if ":" in spec and not Path(spec).exists():
            slug, path = spec.split(":", 1)
        else:
            slug, path = None, spec
        if path.endswith(".json"):
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            rows = [{"angle": slug, "views": d.get("view_count"), "likes": d.get("like_count"),
                     "comments": d.get("comment_count"), "shares": d.get("repost_count")}]
        else:
            rows = read_csv(path)
        for r in rows:
            ang = r.get("angle") or slug
            v = fnum(r.get("views"))
            if not ang or not v:
                continue
            e = eng[ang]
            e["views"] += v
            e["inter"] += sum(fnum(r.get(k)) or 0 for k in ("likes", "comments", "shares"))
            e["shares"] += fnum(r.get("shares")) or 0
            e["posts"] += 1

    spy = defaultdict(lambda: defaultdict(list))
    if a.spy_tool:
        for r in read_csv(a.spy_tool):
            ang = amap.get(str(r.get("ad_id") or "").strip())
            if not ang:
                continue
            for k in ("est_spend", "est_cpc", "est_roas"):
                v = fnum(r.get(k))
                if v is not None:
                    spy[ang][k].append(v)

    be_roas = None
    if a.aov:
        margin = a.aov - a.cogs - a.shipping - a.aov * a.fees_pct / 100
        be_roas = round(a.aov / margin, 2) if margin > 0 else None

    angles = list(per)
    if not angles:
        sys.exit("Không ad nào khớp angle-map. Kiểm tra cột ad_id trùng với id trong file ads.")
    er = {k: (eng[k]["inter"] / eng[k]["views"] if eng[k]["views"] else None) for k in angles}
    er_known = [v for v in er.values() if v]
    er_med = st.median(er_known) if er_known else None
    eng_idx = {k: (er[k] / er_med if er[k] and er_med else None) for k in angles}

    comp = {
        "longevity": norm({k: min(max(per[k]["days_active"] or [0]), 120) for k in angles}),
        "investment": norm({k: math.log1p(per[k]["active"] + per[k]["dups"]) for k in angles}),
        "freshness": norm({k: per[k]["new30"] for k in angles}),
        "engagement": norm({k: eng_idx[k] for k in angles}) if er_known else None,
        "spend": norm({k: (sum(spy[k]["est_spend"]) if spy[k]["est_spend"] else None) for k in angles})
        if any(spy[k]["est_spend"] for k in angles) else None,
    }
    weights = {"longevity": .35, "investment": .25, "freshness": .15, "engagement": .15, "spend": .10}
    used = {k: w for k, w in weights.items() if comp[k] is not None}
    tot_w = sum(used.values())

    out = []
    for k in angles:
        p = per[k]
        score = round(100 * sum(comp[c][k] * w for c, w in used.items()) / tot_w)
        max_days = max(p["days_active"] or [0])
        # ROAS sàn suy ra từ độ bền
        if not p["active"]:
            roas_floor, roas_note = None, "đã tắt hết: có thể không lãi"
        elif max_days >= 60 and (p["new30"] or p["dups"] > p["ads"]):
            roas_floor, roas_note = be_roas, "≥ hoà vốn, nhiều khả năng cao hơn (chạy ≥60 ngày + vẫn nhân bản)"
        elif max_days >= 30:
            roas_floor, roas_note = be_roas, "≥ hoà vốn (có ad active ≥30 ngày)"
        else:
            roas_floor, roas_note = None, "chưa đủ lâu để suy ra"
        # CPC ước tính
        cpc_src = None
        if spy[k]["est_cpc"]:
            c = st.median(spy[k]["est_cpc"])
            cpc = (round(c * .85, 2), round(c * 1.15, 2))
            cpc_src = "tool spy"
        elif a.bench_cpc:
            idx = min(1.6, max(0.6, eng_idx[k])) if eng_idx[k] else 1.0
            c = a.bench_cpc / idx
            cpc = (round(c * .75, 2), round(c * 1.25, 2))
            cpc_src = "benchmark × tương tác" if eng_idx[k] else "benchmark (chưa có tương tác)"
        else:
            cpc = None
        spy_roas = round(st.median(spy[k]["est_roas"]), 2) if spy[k]["est_roas"] else None
        evidence = sum([max_days >= 30, p["ads"] >= 3, eng_idx[k] is not None, any(spy[k].values())])
        conf = "Cao" if evidence >= 3 else "TB" if evidence == 2 else "Thấp"
        out.append({
            "angle": k, "angle_name": names.get(k, k), "ads": p["ads"], "active": p["active"], "new_30d": p["new30"],
            "max_days_active": max_days, "median_days_active": int(st.median(p["days_active"])) if p["days_active"] else 0,
            "duplicates": p["dups"], "engagement_rate": round(er[k] * 100, 2) if er[k] else None,
            "engagement_index": round(eng_idx[k], 2) if eng_idx[k] else None, "posts": eng[k]["posts"],
            "proof_score": score, "cpc_est": cpc, "cpc_source": cpc_src,
            "roas_floor": roas_floor, "roas_note": roas_note, "roas_spy_tool": spy_roas, "confidence": conf,
        })
    out.sort(key=lambda x: -x["proof_score"])
    for i, x in enumerate(out):
        x["test_code"] = f"A{i+1}" if i < a.assign else None

    L = ["# Bảng điểm angle đối thủ\n",
         "> ⚠️ CPC/ROAS của đối thủ **không công khai**. Đây là con số **suy ra / ước tính**, xem cột nguồn & độ tin cậy. "
         "CPC/ROAS thật chỉ có sau khi bạn test (`test_readout.py --scoreboard`).\n"]
    if be_roas:
        L.append(f"- ROAS hoà vốn (theo AOV {a.aov} và giá vốn của bạn): **{be_roas}**")
    if a.bench_cpc:
        L.append(f"- CPC chuẩn dùng để ước tính: **{a.bench_cpc}**")
    L.append(f"- Trọng số proof score: " + ", ".join(f"{c} {w:.0%}" for c, w in used.items()) +
             (f" · bỏ qua {unmapped} ad chưa gắn angle" if unmapped else "") + "\n")
    L.append("| Mã test | Angle | Proof | Ad (active) | Mới 30d | Chạy lâu nhất | Bản nhân | Tương tác | CPC ước tính | ROAS sàn suy ra | ROAS tool spy | Tin cậy |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for x in out:
        cpc = f"{x['cpc_est'][0]}–{x['cpc_est'][1]} ({x['cpc_source']})" if x["cpc_est"] else "— (cần --bench-cpc)"
        rf = (f"≥ {x['roas_floor']}" if x["roas_floor"] else "—") + f" · {x['roas_note']}"
        L.append(f"| {x['test_code'] or ''} | {x['angle_name']} | **{x['proof_score']}** | {x['ads']} ({x['active']}) | {x['new_30d']} | "
                 f"{x['max_days_active']} ngày | {x['duplicates']} | {str(x['engagement_rate']) + '%' if x['engagement_rate'] else '—'} | "
                 f"{cpc} | {rf} | {x['roas_spy_tool'] or '—'} | {x['confidence']} |")
    L.append("\n## → Đưa sang bước test angle\n")
    for x in out[: a.assign]:
        kpi = []
        if x["cpc_est"]:
            kpi.append(f"CPC kỳ vọng ≤ {x['cpc_est'][1]}")
        if be_roas:
            kpi.append(f"ROAS mục tiêu ≥ {be_roas}")
        L.append(f"- **{x['test_code']}: {x['angle_name']}** (proof {x['proof_score']}, tin cậy {x['confidence']}). " + " · ".join(kpi))
    L.append("\nNgân sách test vẫn **chia đều** cho 5 angle, vì chia lệch thì angle nhiều tiền tự nhiên thắng và test không còn sạch. "
             "Proof score dùng để chọn angle nào vào test và đặt kỳ vọng, không dùng để chia tiền.")
    md = "\n".join(L) + "\n"
    res = {"as_of": as_of.isoformat(), "be_roas": be_roas, "bench_cpc": a.bench_cpc, "weights": used, "angles": out}
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()

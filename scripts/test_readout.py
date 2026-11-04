#!/usr/bin/env python3
"""test_readout.py: Đọc kết quả test angle từ file export Ads Manager (Meta/TikTok) → quyết định KILL / GIỮ / WINNER.

Dùng:
  python3 test_readout.py --input export.csv --price 49.99 --cogs 12 --shipping 5 --fees-pct 5 \
      [--angle-regex "A(\\d+)"] [--out-md readout.md] [--out-json readout.json]
  hoặc truyền thẳng --breakeven-cpa 25

Mỗi dòng CSV = 1 ad (export level Ad). Tên cột EN/VN đều nhận (xem ALIASES).
Ad được gom theo ANGLE dựa vào tên ad (mặc định bắt "A1", "A2"… theo naming convention của plugin).

Quy tắc mặc định (chỉnh bằng flag):
  - KILL sớm (creative): ≥ --min-impr lượt hiển thị mà hook rate < --kill-hook (mặc định 15%)
  - KILL: chi ≥ 1.5×BE CPA mà 0 đơn; hoặc chi ≥ 1×BE, 0 ATC và CTR link < 0.7%
  - KILL: có đơn nhưng CPA > 1.5×BE sau khi chi ≥ 3×BE
  - WINNER: ≥ --winner-min-purchases đơn (mặc định 3) và CPA ≤ BE
  - TIỀM NĂNG: có đơn, CPA ≤ BE nhưng chưa đủ số đơn → giữ chạy thêm
  - BORDERLINE: CPA trong khoảng BE–1.5×BE → giữ 1–2 ngày rồi xem lại
  - CHƯA ĐỦ DATA: chi chưa tới 1×BE
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csvio import brief, read_csv_rows  # noqa: E402

ALIASES = {
    "name": ["ad name", "tên quảng cáo", "ad_name", "creative name", "tên ad"],
    "spend": ["amount spent", "số tiền đã chi tiêu", "spend", "cost", "chi phí", "chi tiêu"],
    "impr": ["impressions", "lượt hiển thị", "impression"],
    "clicks": ["link clicks", "lượt click vào liên kết", "clicks (destination)", "clicks"],
    "v3s": ["3-second video plays", "lượt phát video 3 giây", "video views (3s)", "2-second video views", "video views", "6-second video views"],
    "thru": ["thruplays", "thruplay", "video plays at 100%", "lượt thruplay", "video views at 100%"],
    "atc": ["adds to cart", "lượt thêm vào giỏ hàng", "add to cart", "website adds to cart", "atc"],
    "ic": ["checkouts initiated", "lượt bắt đầu thanh toán", "initiate checkout", "website checkouts initiated"],
    "purch": ["purchases", "lượt mua", "website purchases", "complete payment", "results"],
    "rev": ["purchases conversion value", "giá trị chuyển đổi mua hàng", "purchase value", "conversion value", "total complete payment value", "website purchases conversion value"],
}


def num(v) -> float:
    if v is None:
        return 0.0
    s = str(v).strip().replace(" ", "")
    if s in ("", "-", "—"):
        return 0.0
    s = re.sub(r"[^\d,.\-]", "", s)
    if s.count(".") > 1 and not s.count(","):          # 1.500.000 (VND)
        s = s.replace(".", "")
    elif s.count(",") > 1 and not s.count("."):        # 1,500,000
        s = s.replace(",", "")
    elif s.count(".") == 1 and not s.count(",") and re.fullmatch(r"[1-9]\d{0,2}\.\d{3}", s):  # 900.000
        s = s.replace(".", "")
    elif s.count(",") and s.count("."):
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif s.count(",") == 1 and len(s.split(",")[1]) != 3:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def map_cols(header: list[str]) -> dict:
    low = {h: h.strip().lower() for h in header}
    m = {}
    for key, al in ALIASES.items():
        best = None
        for a in al:  # ưu tiên khớp chính xác, sau đó khớp tiền tố (bỏ phần "(USD)")
            for h, l in low.items():
                if l == a:
                    best = h
                    break
            if best:
                break
        if not best:
            for a in al:
                for h, l in low.items():
                    if l.startswith(a) and not (key == "purch" and "value" in l) and not (key == "purch" and "giá trị" in l):
                        best = h
                        break
                if best:
                    break
        if best:
            m[key] = best
    return m


def metrics(d: dict) -> dict:
    s, i, c = d["spend"], d["impr"], d["clicks"]
    p = d["purch"]
    return {
        **{k: round(v, 2) for k, v in d.items() if isinstance(v, float)},
        "cpm": round(s / i * 1000, 2) if i else None,
        "ctr_link": round(c / i * 100, 2) if i else None,
        "cpc": round(s / c, 2) if c else None,
        "hook_rate": round(d["v3s"] / i * 100, 1) if i and d["v3s"] else None,
        "hold_rate": round(d["thru"] / d["v3s"] * 100, 1) if d["v3s"] and d["thru"] else None,
        "atc_rate": round(d["atc"] / c * 100, 1) if c else None,
        "cvr": round(p / c * 100, 2) if c else None,
        "cost_per_atc": round(s / d["atc"], 2) if d["atc"] else None,
        "cpa": round(s / p, 2) if p else None,
        "roas": round(d["rev"] / s, 2) if s and d["rev"] else None,
        "aov": round(d["rev"] / p, 2) if p and d["rev"] else None,
    }


def decide(m: dict, be: float, a) -> tuple[str, str]:
    s, p, atc = m["spend"], m["purch"], m["atc"]
    if m["impr"] >= a.min_impr and m["hook_rate"] is not None and m["hook_rate"] < a.kill_hook and p == 0:
        return "KILL", f"hook rate {m['hook_rate']}% < {a.kill_hook}% sau {int(m['impr'])} hiển thị → 3s đầu không giữ được người xem"
    if p == 0:
        if s >= 1.5 * be:
            return "KILL", f"chi {s:.2f} ≥ 1.5×BE ({1.5*be:.2f}) mà 0 đơn"
        if s >= be and atc == 0 and (m["ctr_link"] or 0) < 0.7:
            return "KILL", f"chi ≥ 1×BE, 0 ATC, CTR {m['ctr_link']}% thấp"
        return "CHƯA ĐỦ DATA", f"chi {s:.2f} / cần ~{1.5*be:.2f} mới kết luận" + (f", đã có {int(atc)} ATC (tín hiệu tốt)" if atc else "")
    cpa = m["cpa"]
    if cpa <= be and p >= a.winner_min_purchases:
        return "WINNER", f"{int(p)} đơn, CPA {cpa} ≤ BE {be:.2f}"
    if cpa <= be:
        return "TIỀM NĂNG", f"{int(p)} đơn, CPA {cpa} ≤ BE nhưng chưa đủ {a.winner_min_purchases} đơn → chạy thêm"
    if cpa > 1.5 * be and s >= 3 * be:
        return "KILL", f"CPA {cpa} > 1.5×BE sau khi chi ≥ 3×BE"
    if cpa > 1.5 * be:
        return "BORDERLINE", f"CPA {cpa} > 1.5×BE nhưng mới chi {s:.2f} (< 3×BE), chạy thêm nếu hook/CTR tốt, không thì kill"
    return "BORDERLINE", f"CPA {cpa} trong khoảng BE–1.5×BE, xem lại sau 1–2 ngày"


ORDER = {"WINNER": 0, "TIỀM NĂNG": 1, "BORDERLINE": 2, "CHƯA ĐỦ DATA": 3, "KILL": 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", "-i", required=True)
    ap.add_argument("--breakeven-cpa", type=float)
    ap.add_argument("--price", type=float, help="Giá bán trung bình / AOV")
    ap.add_argument("--cogs", type=float, default=0)
    ap.add_argument("--shipping", type=float, default=0)
    ap.add_argument("--fees-pct", type=float, default=3, help="%% phí cổng thanh toán + app")
    ap.add_argument("--angle-regex", default=r"(?:^|[_\-\s])(A\d+)(?:[_\-\s]|$)", help="regex có 1 group bắt mã angle từ tên ad")
    ap.add_argument("--min-impr", type=int, default=3000)
    ap.add_argument("--kill-hook", type=float, default=15.0)
    ap.add_argument("--winner-min-purchases", type=int, default=3)
    ap.add_argument("--scoreboard", help="scoreboard.json từ angle_scoreboard.py để so điểm mạng xã hội với kết quả thật")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()

    if a.breakeven_cpa:
        be = a.breakeven_cpa
    elif a.price:
        be = a.price - a.cogs - a.shipping - a.price * a.fees_pct / 100
    else:
        sys.exit("Cần --breakeven-cpa hoặc --price (+ --cogs --shipping) để tính CPA hoà vốn")
    if be <= 0:
        sys.exit(f"CPA hoà vốn ≤ 0 ({be:.2f}): sản phẩm lỗ ngay cả khi ads miễn phí, xem lại giá/giá vốn")

    rows = read_csv_rows(a.input)
    if not rows:
        sys.exit("File rỗng")
    cols = map_cols(list(rows[0].keys()))
    missing = [k for k in ("name", "spend", "impr") if k not in cols]
    if missing:
        sys.exit(f"Không tìm thấy cột: {missing}. Cột hiện có: {list(rows[0].keys())}")
    rx = re.compile(a.angle_regex, re.I)

    per_ad, per_angle = [], defaultdict(lambda: defaultdict(float))
    for r in rows:
        name = (r.get(cols["name"]) or "").strip()
        if not name or name.lower().startswith(("total", "tổng")):
            continue
        d = {k: num(r.get(cols[k])) if k in cols else 0.0 for k in ALIASES if k != "name"}
        mm = rx.search(name)
        angle = mm.group(1).upper() if mm else "?"
        m = metrics(d)
        dec, why = decide(m, be, a)
        per_ad.append({"ad": name, "angle": angle, **m, "decision": dec, "why": why})
        for k, v in d.items():
            per_angle[angle][k] += v
        per_angle[angle]["ads"] += 1

    angles = []
    for ang, d in per_angle.items():
        n_ads = int(d.pop("ads"))
        m = metrics(dict(d))
        dec, why = decide(m, be, a)
        angles.append({"angle": ang, "ads": n_ads, **m, "decision": dec, "why": why})
    angles.sort(key=lambda x: (ORDER[x["decision"]], x["cpa"] or 1e9, -(x["hook_rate"] or 0)))
    per_ad.sort(key=lambda x: (ORDER[x["decision"]], x["cpa"] or 1e9, -(x["hook_rate"] or 0)))

    def f(v, suf=""):
        return "—" if v is None else f"{v}{suf}"

    be_roas = round(a.price / be, 2) if a.price else None
    L = [f"# Kết quả test angle\n", f"- CPA hoà vốn (BE): **{be:.2f}**" + (f" · ROAS hoà vốn: **{be_roas}**" if be_roas else "")
         + f" · rule winner: ≥{a.winner_min_purchases} đơn & CPA ≤ BE\n"]
    L.append("## Theo ANGLE\n")
    L.append("| Angle | Ads | Chi | Hook% | Hold% | CTR% | CPC | ATC | Đơn | CPA | ROAS | Quyết định | Lý do |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for x in angles:
        L.append(f"| {x['angle']} | {x['ads']} | {x['spend']:.2f} | {f(x['hook_rate'])} | {f(x['hold_rate'])} | {f(x['ctr_link'])} | {f(x['cpc'])} | "
                 f"{int(x['atc'])} | {int(x['purch'])} | {f(x['cpa'])} | {f(x['roas'])} | **{x['decision']}** | {x['why']} |")
    L.append("\n## Theo từng AD\n")
    L.append("| Ad | Angle | Chi | Hook% | Hold% | CTR% | ATC | Đơn | CPA | Quyết định |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for x in per_ad:
        L.append(f"| {x['ad']} | {x['angle']} | {x['spend']:.2f} | {f(x['hook_rate'])} | {f(x['hold_rate'])} | {f(x['ctr_link'])} | "
                 f"{int(x['atc'])} | {int(x['purch'])} | {f(x['cpa'])} | **{x['decision']}** |")
    pred_rows = []
    if a.scoreboard:
        sb = {x["test_code"]: x for x in json.loads(Path(a.scoreboard).read_text(encoding="utf-8"))["angles"] if x.get("test_code")}
        actual_rank = {x["angle"]: i + 1 for i, x in enumerate(angles)}
        pred_rank = {k: i + 1 for i, k in enumerate(sorted(sb, key=lambda k: -sb[k]["signal_score"]))}
        shares = sorted(v["share_rate"] for v in sb.values() if v.get("share_rate") is not None)
        share_med = shares[len(shares) // 2] if shares else None
        L.append("\n## Dự đoán từ mạng xã hội vs kết quả thật\n")
        L.append("| Angle | Tên | Điểm MXH (hạng) | Hạng thật | Quyết định | Hook% | CPC thật | ROAS thật | Nhận xét |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for code in sorted(sb, key=lambda k: pred_rank[k]):
            p = sb[code]
            x = next((y for y in angles if y["angle"] == code), None)
            if not x:
                L.append(f"| {code} | {p['angle_name']} | {p['signal_score']} (#{pred_rank[code]}) | chưa chạy | | | | | |")
                continue
            notes = []
            diff = actual_rank[code] - pred_rank[code]
            if diff <= -2:
                notes.append("bất ngờ: tốt hơn dự đoán")
            elif diff >= 2:
                notes.append("bất ngờ: kém hơn dự đoán, xem lại cách dựng/hook trước khi bỏ angle")
            else:
                notes.append("đúng dự đoán")
            if share_med is not None and (p.get("share_rate") or 0) > share_med and x["hook_rate"] is not None and x["hook_rate"] < a.kill_hook:
                notes.append("organic share tốt nhưng hook ad yếu → 3s đầu của mình chưa bằng bản gốc")
            pred_rows.append({"angle": code, "pred_rank": pred_rank[code], "actual_rank": actual_rank[code], "notes": notes})
            L.append(f"| {code} | {p['angle_name']} | {p['signal_score']} (#{pred_rank[code]}) | #{actual_rank[code]} | {x['decision']} | "
                     f"{f(x['hook_rate'])} | {f(x['cpc'])} | {f(x['roas'])} | {'; '.join(notes)} |")
        L.append("\n> Angle được mạng xã hội chuộng mà ad của mình thua → thường do **thực thi** (hook, dựng, offer/LP), chưa chắc angle sai. "
                 "Angle thắng ngoài dự đoán → đáng giá nhất, vì đối thủ chưa khai thác.")

    win = [x for x in angles if x["decision"] == "WINNER"]
    pot = [x for x in angles if x["decision"] == "TIỀM NĂNG"]
    L.append("\n## Kết luận\n")
    if win:
        best = win[0]
        L.append(f"🏆 **Angle kim chỉ nam ứng viên: {best['angle']}** (CPA {best['cpa']}, {int(best['purch'])} đơn). "
                 f"Chạy `/angle-lab:winner` để mổ video thắng của angle này.")
        if len(win) > 1:
            L.append(f"\nCó {len(win)} angle đạt WINNER. Chọn angle CPA thấp nhất làm kim chỉ nam, angle còn lại để dành cho đợt sau.")
    elif pot:
        L.append(f"⏳ Chưa có winner chắc chắn. Angle tiềm năng: {', '.join(x['angle'] for x in pot)}. Chạy thêm 1–2 ngày.")
    else:
        L.append("❌ Chưa angle nào ra tiền. Xem lại: offer/giá, landing page, hoặc test lứa angle mới từ báo cáo spy.")
    L.append("\n> ⚠️ Mẫu nhỏ (vài đơn) dao động mạnh. Winner thật phải giữ CPA khi tăng ngân sách/nhân bản.")
    md = "\n".join(L) + "\n"
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    if a.out_json:
        Path(a.out_json).write_text(json.dumps({"breakeven_cpa": round(be, 2), "breakeven_roas": be_roas, "spy_vs_actual": pred_rows, "angles": angles, "ads": per_ad, "column_map": cols},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(brief(md, a.out_md, 7 + len(angles)) + ("\n" + "\n".join(l for l in md.splitlines() if l.startswith(("🏆", "⏳", "❌"))) if a.out_md else ""))


if __name__ == "__main__":
    main()

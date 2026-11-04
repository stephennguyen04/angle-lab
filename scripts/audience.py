#!/usr/bin/env python3
"""audience.py: Đọc PERSONA mà đối thủ thực sự tiếp cận, theo từng angle và từng ad, từ dữ liệu minh bạch EU/UK (DSA).

Input: ads_raw.json (adlib_parse.py, từ API ads_archive hoặc HAR có mở "See ad details") + angle_map.csv (tuỳ chọn).
Dùng trường reach_breakdown = age_country_gender_reach_breakdown:
  [{"country": "DE", "age_gender_breakdowns": [{"age_range": "25-34", "male": 120, "female": 480, "unknown": 3}, …]}, …]
và target khai báo (target_ages, target_gender, target_locations).

Output: audience.md + audience.json, gồm:
  - theo angle: % nữ / nam, nhóm tuổi chính, quốc gia chính, ô persona lớn nhất (vd "Nữ 35–44: 31%"), 1 câu persona
  - theo ad (top theo tiếp cận): persona của từng ad mạnh, nhân vật nên chọn khi nhân bản
  - target khai báo vs người thực sự xem (Advantage+ thường lệch target → thấy được thuật toán tìm ra ai)

Dùng: python3 audience.py --ads ads_raw.json [--angle-map angle_map.csv] --out-md audience.md --out-json audience.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csvio import read_csv_rows  # noqa: E402

AGE_ORDER = ["13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
G_VI = {"female": "Nữ", "male": "Nam", "unknown": "Không rõ"}


def num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def cells(bd) -> list[tuple[str, str, str, float]]:
    """→ [(country, age, gender, reach)]. Chấp nhận vài biến thể cấu trúc."""
    out = []
    if isinstance(bd, str):
        try:
            bd = json.loads(bd)
        except json.JSONDecodeError:
            return out
    for c in bd or []:
        if not isinstance(c, dict):
            continue
        country = c.get("country") or c.get("country_code") or "?"
        for ag in c.get("age_gender_breakdowns") or c.get("breakdowns") or []:
            age = str(ag.get("age_range") or ag.get("age") or "?").replace("–", "-")
            for g in ("female", "male", "unknown"):
                v = num(ag.get(g))
                if v:
                    out.append((country, age, g, v))
    return out


def summarize(cs: list[tuple[str, str, str, float]]) -> dict | None:
    tot = sum(c[3] for c in cs)
    if not tot:
        return None
    gender, age, country, cell = Counter(), Counter(), Counter(), Counter()
    for co, ag, g, v in cs:
        gender[g] += v
        age[ag] += v
        country[co] += v
        cell[(g, ag)] += v
    pct = lambda c: {k: round(v / tot * 100, 1) for k, v in c.most_common()}  # noqa: E731
    # dải tuổi liền nhau NGẮN NHẤT chiếm ≥ 60% lượt tiếp cận
    ages_sorted = sorted(age, key=lambda x: AGE_ORDER.index(x) if x in AGE_ORDER else 99)
    best = None
    for i in range(len(ages_sorted)):
        acc = 0.0
        for j in range(i, len(ages_sorted)):
            acc += age[ages_sorted[j]]
            if acc / tot >= .6:
                if best is None or (j - i) < best[3]:
                    best = (ages_sorted[i], ages_sorted[j], acc / tot, j - i)
                break
    known = gender["female"] + gender["male"]
    g_main = max(("female", "male"), key=lambda x: gender[x])
    g_share = gender[g_main] / known if known else 0
    (cg, ca), cv = cell.most_common(1)[0]
    who = f"{G_VI[g_main]} ({g_share:.0%})" if g_share >= .6 else "cả nam và nữ"
    if best:
        lo, hi = best[0].split("-")[0], best[1].split("-")[-1]
        span = f"{lo}–{hi}" if lo != hi else lo
        age_txt = f"tuổi {span} ({best[2]:.0%} lượt tiếp cận)"
    else:
        age_txt = "tuổi phân tán"
    sentence = (f"Chủ yếu {who}, {age_txt}; nhóm lớn nhất: {G_VI[cg]} {ca} ({cv / tot:.0%}); quốc gia chính: "
                + ", ".join(f"{k} {v / tot:.0%}" for k, v in country.most_common(3)))
    return {"reach": int(tot), "gender_pct": pct(gender), "age_pct": dict(sorted(pct(age).items(), key=lambda kv: AGE_ORDER.index(kv[0]) if kv[0] in AGE_ORDER else 99)),
            "country_pct": dict(list(pct(country).items())[:8]), "top_cell": f"{G_VI[cg]} {ca}", "top_cell_pct": round(cv / tot * 100, 1),
            "persona": sentence}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ads", required=True)
    ap.add_argument("--angle-map")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    data = json.loads(Path(a.ads).read_text(encoding="utf-8"))
    ads = data if isinstance(data, list) else data.get("data") or data.get("ads") or []
    amap, names = {}, {}
    if a.angle_map:
        for r in read_csv_rows(a.angle_map):
            if r.get("ad_id") and r.get("angle"):
                amap[str(r["ad_id"]).strip()] = r["angle"].strip()
                if r.get("angle_name"):
                    names[r["angle"].strip()] = r["angle_name"].strip()

    per_angle = defaultdict(list)
    per_ad = []
    no_bd = 0
    for ad in ads:
        cs = cells(ad.get("reach_breakdown"))
        if not cs:
            no_bd += 1
            continue
        s = summarize(cs)
        ang = amap.get(str(ad.get("id")))
        per_angle[ang or "_chưa gán angle_"].extend(cs)
        per_ad.append({"id": ad.get("id"), "angle": ang, "body": (ad.get("body") or "")[:80], "summary": s,
                       "target": {"ages": ad.get("target_ages"), "gender": ad.get("target_gender"),
                                  "locations": [l.get("name") if isinstance(l, dict) else l for l in (ad.get("target_locations") or [])][:5]}})
    angles = {k: summarize(v) for k, v in per_angle.items()}
    per_ad.sort(key=lambda x: -x["summary"]["reach"])

    L = ["# Persona đối thủ đang tiếp cận (dữ liệu minh bạch EU/UK)\n"]
    if not per_ad:
        L.append(f"_Không có ad nào kèm cơ cấu tuổi/giới ({no_bd} ad không có). Dữ liệu này chỉ có với ad phân phối ở EU/UK: "
                 "lấy bằng adlib_api.py (country EU/UK) hoặc mở \"See ad details\" khi lưu HAR._")
    else:
        L.append(f"- {len(per_ad)} ad có cơ cấu tiếp cận · {no_bd} ad không có\n")
        L.append("## Theo angle\n")
        L.append("| Angle | Tiếp cận | Nữ | Nam | Nhóm lớn nhất | Tuổi chính | Quốc gia | Persona |")
        L.append("|---|---|---|---|---|---|---|---|")
        for k, s in sorted(angles.items(), key=lambda kv: -kv[1]["reach"]):
            top_ages = ", ".join(f"{ag} {p}%" for ag, p in sorted(s["age_pct"].items(), key=lambda kv: -kv[1])[:2])
            L.append(f"| {names.get(k, k)} | {s['reach']:,} | {s['gender_pct'].get('female', 0)}% | {s['gender_pct'].get('male', 0)}% | "
                     f"{s['top_cell']} ({s['top_cell_pct']}%) | {top_ages} | {', '.join(list(s['country_pct'])[:3])} | {s['persona']} |")
        L.append(f"\n## Top {min(a.top, len(per_ad))} ad theo tiếp cận: persona & target khai báo\n")
        L.append("| Ad | Angle | Tiếp cận | Persona thực tế | Target khai báo |")
        L.append("|---|---|---|---|---|")
        for x in per_ad[: a.top]:
            t = x["target"]
            ages = "–".join(map(str, t["ages"])) if isinstance(t["ages"], list) else t["ages"]
            tgt = " · ".join(filter(None, [f"tuổi {ages}" if ages else "", f"giới {t['gender']}" if t["gender"] else "",
                                           ", ".join(filter(None, t["locations"])) if t["locations"] else ""])) or "—"
            L.append(f"| {x['id']} | {names.get(x['angle'], x['angle']) or '—'} | {x['summary']['reach']:,} | {x['summary']['persona']} | {tgt} |")
        L.append("\n> Target khai báo rộng (vd 18–65+, mọi giới) mà người xem thực tế dồn vào 1 nhóm → thuật toán Meta đã tự tìm ra persona mua. "
                 "Đó là nhân vật nên chọn khi dựng video test / nhân bản.")
    md = "\n".join(L) + "\n"
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8")
    if a.out_json:
        Path(a.out_json).write_text(json.dumps({"angles": angles, "ads": per_ad, "ads_without_breakdown": no_bd},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()

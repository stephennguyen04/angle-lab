#!/usr/bin/env python3
"""monitor.py: Theo dõi đối thủ theo thời gian: chụp snapshot ad + trang sản phẩm rồi báo thay đổi.

Lệnh:
  snapshot --dir research/<slug>/monitor --ads ads_raw.json [--product product.json] [--date 2026-11-04]
           → lưu bản sao vào monitor/<ngày>/
  diff     --dir research/<slug>/monitor [--from 2026-11-01 --to 2026-11-04] [--out alert.md]
           → so 2 snapshot gần nhất (hoặc 2 ngày chỉ định)

Báo:
  🆕 ad mới · ⛔ ad đã tắt · 🏆 ad vừa vượt mốc 30 / 60 ngày (thành Performer / Long-Runner)
  📈 ad tăng bản nhân mạnh (≥2× và +3) · 🌍 tiếp cận EU tăng ≥50%
  💲 trang sản phẩm: đổi giá / giá gạch / thêm-bớt variant (bundle) / bật app bundle, guarantee, countdown…
Lên lịch chạy hằng ngày: xem skill /angle-lab:monitor.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ad_cadence import load_rows, parse_bool, parse_date, parse_int, pick  # noqa: E402


def ads_index(path: Path, as_of: date) -> dict:
    out = {}
    if not path.exists():
        return out
    for r in load_rows(path):
        aid = str(pick(r, "id") or "")
        sd = parse_date(pick(r, "start_date"))
        if not aid or not sd:
            continue
        ed = parse_date(pick(r, "end_date"))
        act = parse_bool(pick(r, "is_active"))
        act = (ed is None or ed >= as_of) if act is None else act
        out[aid] = {"active": act, "days": (as_of - sd).days + 1, "dups": parse_int(pick(r, "duplicates"), 1),
                    "reach": parse_int(pick(r, "eu_reach"), 0), "body": str(pick(r, "body") or "")[:80].replace("\n", " "),
                    "start": sd.isoformat()}
    return out


def snapshots(d: Path) -> list[Path]:
    return sorted(p for p in d.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == "-") if d.exists() else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["snapshot", "diff"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--ads")
    ap.add_argument("--product")
    ap.add_argument("--date")
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to")
    ap.add_argument("--out")
    a = ap.parse_args()
    root = Path(a.dir)

    if a.cmd == "snapshot":
        day = a.date or date.today().isoformat()
        dst = root / day
        dst.mkdir(parents=True, exist_ok=True)
        if a.ads:
            shutil.copy(a.ads, dst / ("ads" + Path(a.ads).suffix))
        if a.product:
            shutil.copy(a.product, dst / "product.json")
        print(f"→ snapshot {dst}")
        return

    snaps = snapshots(root)
    if a.frm and a.to:
        old, new = root / a.frm, root / a.to
    elif len(snaps) >= 2:
        old, new = snaps[-2], snaps[-1]
    else:
        sys.exit("Cần ít nhất 2 snapshot (chạy snapshot mỗi ngày).")
    d_old, d_new = date.fromisoformat(old.name), date.fromisoformat(new.name)
    f_old = next(iter(sorted(old.glob("ads.*"))), None)
    f_new = next(iter(sorted(new.glob("ads.*"))), None)
    A = ads_index(f_old, d_old) if f_old else {}
    B = ads_index(f_new, d_new) if f_new else {}
    L = [f"# Thay đổi đối thủ: {old.name} → {new.name}\n"]
    alerts = 0

    newads = [k for k in B if k not in A and B[k]["active"]]
    stopped = [k for k in A if A[k]["active"] and (k not in B or not B[k]["active"])]
    crossed = [(k, m) for k in B for m in (30, 60) if B[k]["active"] and k in A and A[k]["days"] < m <= B[k]["days"]]
    dup_up = [k for k in B if k in A and B[k]["dups"] >= max(2 * A[k]["dups"], A[k]["dups"] + 3)]
    reach_up = [k for k in B if k in A and A[k]["reach"] and B[k]["reach"] >= 1.5 * A[k]["reach"]]

    def line(k, extra=""):
        x = B.get(k) or A.get(k)
        return f"- `{k}` · {x['days']} ngày · {x['dups']} bản nhân{extra} · {x['body']}"

    if A or B:
        L.append(f"Ad active: {sum(1 for x in A.values() if x['active'])} → **{sum(1 for x in B.values() if x['active'])}**\n")
    for title, items, fmt in (("🆕 Ad mới", newads, lambda k: line(k)),
                              ("🏆 Vừa vượt mốc (ad sống lâu = đang có lãi)", crossed, lambda km: line(km[0], f" · **vượt {km[1]} ngày**")),
                              ("📈 Tăng bản nhân mạnh (đang scale creative này)", dup_up, lambda k: line(k, f" (trước {A[k]['dups']})")),
                              ("🌍 Tiếp cận EU tăng ≥50%", reach_up, lambda k: line(k, f" · reach {A[k]['reach']:,} → {B[k]['reach']:,}")),
                              ("⛔ Ad đã tắt", stopped, lambda k: line(k))):
        if items:
            alerts += len(items)
            L.append(f"## {title}: {len(items)}\n")
            L += [fmt(x) for x in items[:25]]
            if len(items) > 25:
                L.append(f"- … và {len(items) - 25} ad khác")
            L.append("")

    po, pn = old / "product.json", new / "product.json"
    if po.exists() and pn.exists():
        P, Q = json.loads(po.read_text(encoding="utf-8")), json.loads(pn.read_text(encoding="utf-8"))
        ch = []
        vp = {v["title"]: v for v in P.get("variants", [])}
        vq = {v["title"]: v for v in Q.get("variants", [])}
        for t in vq:
            if t not in vp:
                ch.append(f"- Thêm variant **{t}** ({vq[t].get('price')})")
            elif (vp[t].get("price"), vp[t].get("compare_at")) != (vq[t].get("price"), vq[t].get("compare_at")):
                ch.append(f"- **{t}**: giá {vp[t].get('price')} → {vq[t].get('price')} · giá gạch {vp[t].get('compare_at')} → {vq[t].get('compare_at')}")
            elif vp[t].get("available") != vq[t].get("available"):
                ch.append(f"- **{t}**: {'hết hàng' if not vq[t].get('available') else 'có hàng lại'}")
        ch += [f"- Bỏ variant **{t}**" for t in vp if t not in vq]
        for k, v in (Q.get("markers") or {}).items():
            if v != (P.get("markers") or {}).get(k):
                ch.append(f"- {'Bật' if v else 'Tắt'} **{k}**")
        if (P.get("product") or {}).get("title") != (Q.get("product") or {}).get("title"):
            ch.append(f"- Đổi tên sản phẩm: {(P.get('product') or {}).get('title')} → {(Q.get('product') or {}).get('title')}")
        if ch:
            alerts += len(ch)
            L.append(f"## 💲 Trang sản phẩm / offer: {len(ch)} thay đổi\n")
            L += ch
            L.append("")
    if not alerts:
        L.append("_Không có thay đổi đáng chú ý._")
    md = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()

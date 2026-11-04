#!/usr/bin/env python3
"""variant_matrix.py: Sinh ma trận biến thể để NHÂN BẢN creative, khoá chặt 1 angle.

Input: angle.json (do skill /angle-lab:winner tạo), gồm:
  {
    "angle_id": "A3",
    "angle_name": "...",
    "invariants": ["nỗi đau X", "cơ chế Y", "lời hứa Z", "bằng chứng kiểu W", ...],
    "control": {"hook": "H0", "character": "C0", "setting": "S0"},
    "hooks":      [{"id": "H0", "text": "...", "type": "..."}, ...],
    "characters": [{"id": "C0", "desc": "..."}, ...],
    "settings":   [{"id": "S0", "desc": "..."}, ...]
  }

Chế độ (--mode):
  staged (mặc định): Vòng 1 chỉ đổi HOOK (rẻ nhất, tác động mạnh nhất) → Vòng 2 đổi NHÂN VẬT → Vòng 3 đổi BỐI CẢNH.
                     Mỗi biến thể chỉ khác control đúng 1 biến → đọc số biết ngay biến nào ăn.
  one-change       : tất cả biến thể đổi đúng 1 biến (gộp 3 vòng thành 1 lần)
  combo            : kết hợp hook × nhân vật × bối cảnh (cho giai đoạn scale, khi đã biết hook/nhân vật thắng)

Output CSV: variant_id, round, ad_name, hook_id, hook_text, character, setting, changed, angle_lock_checklist
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from datetime import date
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--angle", required=True, help="angle.json")
    ap.add_argument("--mode", choices=["staged", "one-change", "combo"], default="staged")
    ap.add_argument("--round", type=int, choices=[1, 2, 3], help="staged: chỉ xuất 1 vòng")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--prefix", default=date.today().strftime("%y%m%d"))
    ap.add_argument("--out", default="variants.csv")
    a = ap.parse_args()

    spec = json.loads(Path(a.angle).read_text(encoding="utf-8"))
    aid = spec["angle_id"]
    H = {h["id"]: h for h in spec.get("hooks", [])}
    C = {c["id"]: c for c in spec.get("characters", [])}
    S = {s["id"]: s for s in spec.get("settings", [])}
    ctrl = spec.get("control") or {}
    h0 = ctrl.get("hook") or next(iter(H), None)
    c0 = ctrl.get("character") or next(iter(C), None)
    s0 = ctrl.get("setting") or next(iter(S), None)
    if not (h0 and c0 and s0):
        sys.exit("angle.json cần ít nhất 1 hook, 1 character, 1 setting (và nên có control)")
    checklist = " | ".join(f"[ ] {x}" for x in spec.get("invariants", []))

    combos = []  # (round, h, c, s, changed)
    if a.mode in ("staged", "one-change"):
        combos.append((0, h0, c0, s0, "CONTROL"))
        combos += [(1, h, c0, s0, "hook") for h in H if h != h0]
        combos += [(2, h0, c, s0, "character") for c in C if c != c0]
        combos += [(3, h0, c0, s, "setting") for s in S if s != s0]
        if a.mode == "staged" and a.round:
            combos = [x for x in combos if x[0] in (0, a.round)]
        if a.mode == "one-change":
            combos = [(1 if r else 0, h, c, s, ch) for r, h, c, s, ch in combos]
    else:
        for h, c, s in itertools.product(H, C, S):
            changed = "+".join(n for n, v, v0 in (("hook", h, h0), ("character", c, c0), ("setting", s, s0)) if v != v0) or "CONTROL"
            combos.append((1, h, c, s, changed))
        combos.sort(key=lambda x: x[4].count("+"))

    combos = combos[: a.max]
    out = Path(a.out)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "round", "ad_name", "hook_id", "hook_type", "hook_text", "character_id", "character",
                    "setting_id", "setting", "changed", "angle_lock_checklist", "status"])
        for i, (rnd, h, c, s, ch) in enumerate(combos):
            vid = f"V{i:02d}"
            name = f"{a.prefix}_{aid}_{vid}_{h}_{c}_{s}"
            w.writerow([vid, rnd, name, h, H[h].get("type", ""), H[h].get("text", ""), c, C[c].get("desc", ""),
                        s, S[s].get("desc", ""), ch, checklist, "brief"])
    print(f"Đã tạo {len(combos)} biến thể ({a.mode}) → {out}")
    rounds = {}
    for r, *_ in combos:
        rounds[r] = rounds.get(r, 0) + 1
    print("Phân bổ theo vòng:", ", ".join(f"vòng {k}: {v}" for k, v in sorted(rounds.items())))


if __name__ == "__main__":
    main()

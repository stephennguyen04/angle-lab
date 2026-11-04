#!/usr/bin/env python3
"""hooks_library.py: Thư viện hook dùng chung cho MỌI sản phẩm: hook đã chứng minh (đối thủ chạy lâu / mình test thắng).

Mỗi hook: text, type, angle, pain, product, niche, platform, source (competitor|own), evidence, status (proven|tested|idea).
File thư viện: --lib (mặc định ./hooks-library/hooks.jsonl, hoặc biến môi trường ANGLE_LAB_HOOKS).

Lệnh:
  add       --text "…" --type "callout nỗi đau" --angle … --niche … [--product …] [--source competitor] [--days 95 --dupes 6]
  add-file  <hooks.jsonl|json>             # AI ghi hook khi mổ video: research/<slug>/03-videos/hooks.jsonl
  harvest   --root research                # gom mọi research/*/03-videos/hooks.jsonl + creative/hooks.jsonl
  results   --readout creative/readout.json --variants creative/04-variants.csv --product … --niche …
            # gắn kết quả test THẬT của mình (hook rate, CTR, CPA, quyết định) vào từng hook
  search    [--q từ khoá] [--type …] [--niche …] [--status proven] [--top 20]
  report    [--out hooks-library/README.md]
Hook được xếp theo điểm bằng chứng: mình test WINNER > đối thủ Long-Runner + nhân bản nhiều > ý tưởng.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csvio import read_csv_rows  # noqa: E402

DEFAULT_LIB = os.environ.get("ANGLE_LAB_HOOKS", "hooks-library/hooks.jsonl")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower().replace("đ", "d"))
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def hid(text: str, product: str | None) -> str:
    return hashlib.sha1(f"{fold(text)}|{fold(product or '')}".encode()).hexdigest()[:10]


def load(lib: Path) -> dict[str, dict]:
    out = {}
    if lib.exists():
        for l in lib.read_text(encoding="utf-8").splitlines():
            if l.strip():
                try:
                    h = json.loads(l)
                    out[h["id"]] = h
                except (json.JSONDecodeError, KeyError):
                    continue
    return out


def save(lib: Path, hooks: dict[str, dict]):
    lib.parent.mkdir(parents=True, exist_ok=True)
    with lib.open("w", encoding="utf-8") as f:
        for h in sorted(hooks.values(), key=lambda h: -score(h)):
            f.write(json.dumps(h, ensure_ascii=False) + "\n")


def score(h: dict) -> float:
    e = h.get("evidence") or {}
    s = 0.0
    dec = (e.get("decision") or "").upper()
    s += {"WINNER": 100, "TIỀM NĂNG": 55, "BORDERLINE": 25, "KILL": -20}.get(dec, 0)
    if e.get("hook_rate"):
        s += float(e["hook_rate"]) * 1.5
    if e.get("days_running"):
        s += min(float(e["days_running"]), 180) / 2
    if e.get("duplicates"):
        s += math.log(max(float(e["duplicates"]), 1)) * 10
    if e.get("eu_reach"):
        s += math.log10(max(float(e["eu_reach"]), 1)) * 4
    if e.get("views"):
        s += math.log10(max(float(e["views"]), 1)) * 3
    return round(s, 1)


def status_of(h: dict) -> str:
    e = h.get("evidence") or {}
    if (e.get("decision") or "").upper() == "WINNER" or (e.get("days_running") or 0) >= 60:
        return "proven"
    if e.get("decision") or e.get("days_running"):
        return "tested"
    return "idea"


def upsert(hooks: dict, h: dict) -> str:
    text = (h.get("text") or h.get("hook") or "").strip()
    if not text:
        return "skip"
    h = {**h, "text": unicodedata.normalize("NFC", text)}
    h.setdefault("added", date.today().isoformat())
    key = hid(text, h.get("product"))
    h["id"] = key
    if key in hooks:
        old = hooks[key]
        ev = {**(old.get("evidence") or {}), **{k: v for k, v in (h.get("evidence") or {}).items() if v not in (None, "")}}
        old.update({k: v for k, v in h.items() if v not in (None, "", []) and k != "evidence"})
        old["evidence"] = ev
        old["status"] = status_of(old)
        old["score"] = score(old)
        return "update"
    h["evidence"] = h.get("evidence") or {}
    h["status"] = status_of(h)
    h["score"] = score(h)
    hooks[key] = h
    return "new"


def read_items(p: Path) -> list[dict]:
    raw = p.read_text(encoding="utf-8-sig")
    if p.suffix == ".jsonl":
        return [json.loads(l) for l in raw.splitlines() if l.strip()]
    d = json.loads(raw)
    return d if isinstance(d, list) else d.get("hooks", [d])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "add-file", "harvest", "results", "search", "report"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--lib", default=DEFAULT_LIB)
    for k in ("text", "type", "angle", "pain", "product", "niche", "platform", "source", "visual", "q", "status", "out", "root", "readout", "variants", "ad_id"):
        ap.add_argument(f"--{k.replace('_', '-')}", dest=k)
    ap.add_argument("--days", type=float)
    ap.add_argument("--dupes", type=float)
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    lib = Path(a.lib)
    hooks = load(lib)
    stats = {"new": 0, "update": 0, "skip": 0}

    if a.cmd == "add":
        stats[upsert(hooks, {"text": a.text, "type": a.type, "angle": a.angle, "pain": a.pain, "product": a.product, "niche": a.niche,
                             "platform": a.platform, "source": a.source or "competitor", "visual": a.visual, "ad_id": a.ad_id,
                             "evidence": {"days_running": a.days, "duplicates": a.dupes}})] += 1
    elif a.cmd in ("add-file", "harvest"):
        files = [Path(f) for f in a.files]
        if a.cmd == "harvest":
            root = Path(a.root or "research")
            files = sorted(root.glob("*/03-videos/hooks.jsonl")) + sorted(root.glob("*/creative/hooks.jsonl"))
        for f in files:
            product = f.parts[-3] if a.cmd == "harvest" else a.product
            for it in read_items(f):
                it.setdefault("product", product)
                it.setdefault("source", "competitor" if f.parent.name == "03-videos" else "own")
                if a.niche:
                    it.setdefault("niche", a.niche)
                ev = it.get("evidence") or {}
                for k in ("days_running", "duplicates", "eu_reach", "views", "hook_rate"):
                    if k in it:
                        ev.setdefault(k, it.pop(k))
                it["evidence"] = ev
                stats[upsert(hooks, it)] += 1
        print(f"Đọc {len(files)} file", file=sys.stderr)
    elif a.cmd == "results":
        if not (a.readout and a.variants):
            sys.exit("Cần --readout readout.json và --variants 04-variants.csv")
        ro = json.loads(Path(a.readout).read_text(encoding="utf-8"))
        perf = {x["ad"]: x for x in ro.get("ads", [])}
        for v in read_csv_rows(a.variants):
            x = perf.get(v.get("ad_name"))
            if not x or not v.get("hook_text"):
                continue
            stats[upsert(hooks, {"text": v["hook_text"], "type": v.get("hook_type"), "product": a.product, "niche": a.niche,
                                 "source": "own", "ad_id": v.get("ad_name"), "angle": a.angle,
                                 "evidence": {"decision": x["decision"], "hook_rate": x.get("hook_rate"), "ctr": x.get("ctr_link"),
                                              "cpa": x.get("cpa"), "spend": x.get("spend"), "tested_on": date.today().isoformat()}})] += 1

    if a.cmd in ("search", "report"):
        sel = list(hooks.values())
        if a.q:
            q = fold(a.q)
            sel = [h for h in sel if q in fold(" ".join(str(h.get(k) or "") for k in ("text", "angle", "pain", "product", "niche", "type")))]
        for k in ("type", "niche", "status"):
            if getattr(a, k):
                sel = [h for h in sel if fold(getattr(a, k)) in fold(str(h.get(k) or ""))]
        sel.sort(key=lambda h: -score(h))
        L = [f"# Thư viện hook ({len(hooks)} hook · hiển thị {min(len(sel), a.top)})\n",
             "| # | Hook | Kiểu | Angle / nỗi đau | Sản phẩm · ngách | Nguồn | Bằng chứng | Trạng thái | Điểm |",
             "|---|---|---|---|---|---|---|---|---|"]
        for i, h in enumerate(sel[: a.top], 1):
            e = h.get("evidence") or {}
            ev = " · ".join(filter(None, [e.get("decision"), f"hook {e['hook_rate']}%" if e.get("hook_rate") else "",
                                          f"CPA {e['cpa']}" if e.get("cpa") else "", f"{int(e['days_running'])} ngày" if e.get("days_running") else "",
                                          f"{int(e['duplicates'])} bản nhân" if e.get("duplicates") else ""]))
            L.append(f"| {i} | {h['text'].replace('|', '/')} | {h.get('type') or ''} | {h.get('angle') or ''}{' / ' + h['pain'] if h.get('pain') else ''} | "
                     f"{h.get('product') or ''} · {h.get('niche') or ''} | {h.get('source') or ''} | {ev or '—'} | {h.get('status')} | {score(h)} |")
        md = "\n".join(L) + "\n"
        if a.cmd == "report":
            outp = Path(a.out or lib.parent / "README.md")
            outp.write_text(md, encoding="utf-8")
            print(f"→ {outp}", file=sys.stderr)
        print(md)
        return
    save(lib, hooks)
    print(f"→ {lib}: +{stats['new']} mới · {stats['update']} cập nhật · tổng {len(hooks)} hook")


if __name__ == "__main__":
    main()

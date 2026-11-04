#!/usr/bin/env python3
"""comments.py: Pipeline đào bình luận đa nền tảng: chuẩn hoá → AI gắn nhãn → tổng hợp rủi ro/cơ hội.

Bước 1  prep   : gom mọi file bình luận (yt-dlp .info.json, CSV, JSON, JSONL, TXT) → comments.jsonl
                 + chia batch để AI gắn nhãn (batches/batch_001.jsonl …), kèm "hint" gợi ý nhãn bằng từ khoá.
    python3 comments.py prep --out-dir research/x/comments \
        --input tiktok:tiktok_post1.info.json --input amazon:amazon_reviews.csv --input fb:fb_comments.txt

Bước 2  (AI)   : đọc từng batch, ghi labels.jsonl, mỗi dòng:
    {"id":"c00012","type":"complaint","topics":["shipping"],"severity":2,"buyer":true,"note":"giao 3 tuần chưa tới"}
    type    : praise | complaint | question | purchase_intent | skeptic | tag_friend | other
    topics  : efficacy, quality, price, shipping, sizing, usage, safety, scam_trust, support_refund,
              design, smell_taste, durability, competitor, packaging, other
    severity: 0–3 (chỉ cho complaint/skeptic). 3 = scam/không nhận hàng/hại sức khoẻ/hỏng ngay
    buyer   : true nếu lời người đã mua (đã nhận, đã dùng), false nếu chưa mua, null nếu không rõ

Bước 3  report : python3 comments.py report --out-dir research/x/comments
                 → report.md + report.json (tỉ lệ khen/chê/hỏi theo nền tảng, top chê, FAQ, risk score, quote)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csvio import norm_key, parse_count, read_csv_rows  # noqa: E402

TEXT_KEYS = ["text", "comment", "content", "body", "review", "message", "comment_text", "review_text", "noi_dung", "binh_luan"]
LIKE_KEYS = ["like_count", "likes", "digg_count", "reactions", "helpful", "helpful_votes", "upvotes", "score", "luot_thich"]
DATE_KEYS = ["timestamp", "date", "created_at", "create_time", "time", "published_at", "ngay"]
URL_KEYS = ["source_url", "post_url", "url", "video_url", "link"]
PLATFORM_KEYS = ["platform", "source", "nen_tang"]
RATING_KEYS = ["rating", "stars", "star", "so_sao"]
AUTHOR_KEYS = ["author", "author_id", "user", "username", "name", "nickname"]

TYPES = ["praise", "complaint", "question", "purchase_intent", "skeptic", "tag_friend", "other"]
TYPE_VI = {"praise": "Khen", "complaint": "Chê", "question": "Hỏi", "purchase_intent": "Muốn mua",
           "skeptic": "Nghi ngờ", "tag_friend": "Tag bạn", "other": "Khác"}
TOPIC_VI = {"efficacy": "Hiệu quả", "quality": "Chất lượng", "price": "Giá", "shipping": "Giao hàng",
            "sizing": "Size/kích thước", "usage": "Cách dùng", "safety": "An toàn/tác dụng phụ",
            "scam_trust": "Lừa đảo/uy tín", "support_refund": "CSKH/đổi trả", "design": "Thiết kế/ngoại hình",
            "smell_taste": "Mùi/vị", "durability": "Độ bền", "competitor": "So sánh đối thủ",
            "packaging": "Đóng gói", "other": "Khác"}

# Gợi ý nhãn bằng từ khoá. AI vẫn là người quyết định cuối cùng.
HINTS = {
    "question": r"\?|how much|bao nhiêu|giá sao|ship .*không|có .* không|có ship|where (can|do) i|link\b|size nào|dùng sao|có hiệu quả không|is (it|this) (legit|real)|does it work",
    "purchase_intent": r"\b(need this|want this|ordered|just ordered|take my money|mua liền|chốt|đặt rồi|cần cái này|muốn mua)\b",
    "praise": r"\b(love|amazing|works|worked|great|best|recommend|game ?changer|obsessed|tốt|đỉnh|xịn|ưng|thích|hiệu quả|đáng tiền|recommend|10/10)\b",
    "complaint": r"\b(never (arrived|received)|didn'?t work|doesn'?t work|waste|broke|broken|refund|return|cheap|garbage|trash|fake|scam|tệ|dỏm|lừa|hỏng|không (hiệu quả|nhận được)|chưa nhận|hoàn tiền|phí tiền|kém)\b",
    "skeptic": r"\b(scam|fake|bot|ai generated|too good to be true|dropship|temu|aliexpress|shein|lừa đảo|hàng tàu|hàng chợ)\b",
    "tag_friend": r"^(\s*@[\w.]+\s*)+$",
}
TOPIC_HINTS = {
    "shipping": r"ship|deliver|arriv|tracking|giao|vận chuyển|nhận hàng",
    "price": r"price|expensive|cheap|\$|giá|đắt|rẻ",
    "efficacy": r"work|result|effect|hiệu quả|tác dụng|kết quả",
    "quality": r"quality|cheap|flimsy|chất lượng|kém|xịn",
    "safety": r"rash|burn|allerg|side effect|safe|kích ứng|dị ứng|rát|an toàn",
    "scam_trust": r"scam|fake|legit|lừa|uy tín|temu|aliexpress|dropship",
    "sizing": r"size|fit|small|large|nhỏ|rộng|chật",
    "support_refund": r"refund|return|customer service|support|hoàn tiền|đổi trả|cskh",
    "usage": r"how (to|do)|use it|cách dùng|dùng sao|hướng dẫn",
    "durability": r"broke|last|durab|bền|hỏng",
    "competitor": r"amazon|temu|aliexpress|cheaper|other brand|hãng khác",
}

SEVERITY_WEIGHT = {0: 0.5, 1: 1, 2: 3, 3: 8}


def nk(k: str) -> str:
    return norm_key(k)


def first(d: dict, keys):
    nd = {nk(k): v for k, v in d.items()}
    for k in keys:
        if k in nd and nd[k] not in (None, ""):
            return nd[k]
    return None


def norm_text(t: str) -> str:
    t = unicodedata.normalize("NFC", str(t)).replace("\r", " ").strip()
    return re.sub(r"\s+", " ", t)


def dedupe_key(platform: str, t: str) -> str:
    base = re.sub(r"[^\w]+", "", t.lower())
    return hashlib.md5(f"{platform}|{base}".encode()).hexdigest()


def to_int(v) -> int:
    return parse_count(v) or 0


def read_any(path: Path) -> list[dict]:
    suf = path.suffix.lower()
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if suf in (".csv", ".tsv"):
        return read_csv_rows(path)
    if suf == ".jsonl":
        return [json.loads(l) for l in raw.splitlines() if l.strip()]
    if suf == ".json":
        data = json.loads(raw)
        if isinstance(data, dict):
            # yt-dlp info.json
            if isinstance(data.get("comments"), list):
                url = data.get("webpage_url") or data.get("original_url")
                return [{**c, "source_url": url, "is_reply": c.get("parent") not in (None, "root")} for c in data["comments"]]
            for k in ("data", "comments", "reviews", "items", "results"):
                if isinstance(data.get(k), list):
                    return data[k]
            return [data]
        return data
    # TXT: mỗi bình luận cách nhau bởi dòng trống; nếu không có dòng trống thì mỗi dòng 1 bình luận
    blocks = [b for b in re.split(r"\n\s*\n", raw) if b.strip()]
    if len(blocks) <= 1:
        blocks = [l for l in raw.splitlines() if l.strip()]
    return [{"text": b} for b in blocks]


def hint(text: str) -> dict:
    low = text.lower()
    types = [t for t, p in HINTS.items() if re.search(p, low)]
    topics = [t for t, p in TOPIC_HINTS.items() if re.search(p, low)]
    return {"types": types, "topics": topics}


def cmd_prep(a):
    out = Path(a.out_dir)
    (out / "batches").mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    stats = Counter()
    for spec in a.input:
        platform, _, p = spec.partition(":") if ":" in spec and not Path(spec).exists() else ("unknown", "", spec)
        path = Path(p)
        if not path.exists():
            print(f"[warn] không thấy file {path}", file=sys.stderr)
            continue
        for r in read_any(path):
            if not isinstance(r, dict):
                r = {"text": str(r)}
            t = first(r, TEXT_KEYS)
            if not t:
                stats["empty"] += 1
                continue
            t = norm_text(t)
            plat = str(first(r, PLATFORM_KEYS) or platform).lower()
            if len(re.sub(r"[\W_]+", "", t)) < 2:
                stats["emoji_or_too_short"] += 1
                continue
            k = dedupe_key(plat, t)
            if k in seen:
                stats["duplicate"] += 1
                continue
            seen.add(k)
            author = first(r, AUTHOR_KEYS)
            rows.append({
                "id": f"c{len(rows)+1:05d}",
                "platform": plat,
                "source_url": first(r, URL_KEYS),
                "text": t[: a.max_chars],
                "likes": to_int(first(r, LIKE_KEYS)),
                "rating": first(r, RATING_KEYS),
                "date": str(first(r, DATE_KEYS) or "") or None,
                "is_reply": bool(r.get("is_reply")),
                # chỉ giữ mã băm tác giả, không lưu tên
                "author_hash": hashlib.sha1(str(author).encode()).hexdigest()[:8] if author else None,
                "hint": hint(t),
            })
    rows.sort(key=lambda x: (x["platform"], -x["likes"]))
    with open(out / "comments.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for old in (out / "batches").glob("batch_*.jsonl"):
        old.unlink()
    n_batches = 0
    for i in range(0, len(rows), a.batch_size):
        n_batches += 1
        with open(out / "batches" / f"batch_{n_batches:03d}.jsonl", "w", encoding="utf-8") as f:
            for r in rows[i:i + a.batch_size]:
                slim = {k: r[k] for k in ("id", "platform", "text", "likes", "rating", "hint")}
                f.write(json.dumps(slim, ensure_ascii=False) + "\n")
    per_plat = Counter(r["platform"] for r in rows)
    summary = {"total": len(rows), "per_platform": dict(per_plat), "dropped": dict(stats), "batches": n_batches,
               "batch_size": a.batch_size}
    (out / "prep_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n→ Gắn nhãn các file trong {out/'batches'}/ rồi ghi vào {out/'labels.jsonl'} (1 dòng JSON / bình luận).")


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        l = l.strip()
        if not l:
            continue
        try:
            out.append(json.loads(l))
        except json.JSONDecodeError:
            print(f"[warn] {p.name}:{i} không phải JSON hợp lệ, bỏ qua", file=sys.stderr)
    return out


def cmd_report(a):
    out = Path(a.out_dir)
    comments = {c["id"]: c for c in load_jsonl(out / "comments.jsonl")}
    labels = {}
    for lf in [out / "labels.jsonl", *sorted((out / "labels").glob("*.jsonl"))] if (out / "labels").exists() else [out / "labels.jsonl"]:
        for l in load_jsonl(lf):
            if l.get("id") in comments:
                labels[l["id"]] = l
    if not (out / "comments.jsonl").exists():
        sys.exit("Chưa có comments.jsonl. Chạy prep trước.")
    if not comments:
        sys.exit("comments.jsonl có 0 bình luận (file nguồn rỗng hoặc toàn emoji/trùng). Kiểm tra lại file đầu vào của prep.")
    unlabeled = [cid for cid in comments if cid not in labels]

    rows = []
    for cid, lab in labels.items():
        c = comments[cid]
        t = lab.get("type", "other")
        t = t if t in TYPES else "other"
        topics = [x for x in (lab.get("topics") or ["other"]) if x in TOPIC_VI] or ["other"]
        sev = int(lab.get("severity") or 0) if t in ("complaint", "skeptic") else 0
        rows.append({**c, "type": t, "topics": topics, "severity": max(0, min(3, sev)),
                     "buyer": lab.get("buyer"), "note": lab.get("note")})

    def wt(r):  # bình luận nhiều like = nhiều người đồng tình
        return 1 + math.log1p(r["likes"])

    by_plat = defaultdict(Counter)
    for r in rows:
        by_plat[r["platform"]][r["type"]] += 1
    topic_type = defaultdict(Counter)
    topic_weight = defaultdict(float)
    for r in rows:
        for tp in r["topics"]:
            topic_type[tp][r["type"]] += 1
            if r["type"] in ("complaint", "skeptic"):
                topic_weight[tp] += SEVERITY_WEIGHT[r["severity"]] * wt(r) * (1.5 if r["buyer"] else 1)

    n = len(rows) or 1
    total_types = Counter(r["type"] for r in rows)
    neg = total_types["complaint"] + total_types["skeptic"]
    pos = total_types["praise"] + total_types["purchase_intent"]
    buyer_rows = [r for r in rows if r["buyer"]]
    buyer_neg = sum(1 for r in buyer_rows if r["type"] in ("complaint", "skeptic"))
    sev3 = [r for r in rows if r["severity"] == 3]
    # Risk index = trung bình trọng số nghiêm trọng / bình luận (người đã mua ×1.5). 0 = sạch; ~0.05 = vài lời cằn nhằn;
    # ≥1 ≈ cứ ~8 bình luận có 1 vụ nghiêm trọng của người đã mua.
    risk_raw = sum(SEVERITY_WEIGHT[r["severity"]] * (1.5 if r["buyer"] else 1)
                   for r in rows if r["type"] in ("complaint", "skeptic")) / n
    if risk_raw >= 1.0 or len(sev3) / n >= 0.05 or (buyer_rows and buyer_neg / len(buyer_rows) >= 0.35):
        risk = "🔴 ĐỎ: rủi ro sản phẩm cao, phải xử lý điểm chê trước khi chạy"
    elif risk_raw >= 0.3 or len(sev3) / n >= 0.02:
        risk = "🟡 VÀNG: có vấn đề lặp lại, cần chủ động chặn trong PDP/ad/CSKH"
    else:
        risk = "🟢 XANH: phản hồi chủ yếu tích cực, rủi ro thấp"

    def top(kind_filter, k=8, key=None):
        sel = [r for r in rows if kind_filter(r)]
        sel.sort(key=key or (lambda r: (-r["severity"], -r["likes"])))
        return sel[:k]

    def quote(r):
        t = r["text"] if len(r["text"]) <= 220 else r["text"][:217] + "…"
        return f"> “{t}”  \n> _{r['platform']} · 👍 {r['likes']}{' · đã mua' if r['buyer'] else ''}{' · sev ' + str(r['severity']) if r['severity'] else ''}_"

    L = ["# Phân tích bình luận đa nền tảng\n"]
    L.append(f"- Đã gắn nhãn: **{len(rows)}** / {len(comments)} bình luận" + (f" (⚠️ còn {len(unlabeled)} chưa gắn nhãn)" if unlabeled else ""))
    L.append(f"- Tích cực (khen + muốn mua): **{pos/n:.0%}** · Tiêu cực (chê + nghi ngờ): **{neg/n:.0%}** · Hỏi: **{total_types['question']/n:.0%}**")
    if buyer_rows:
        L.append(f"- Riêng người ĐÃ MUA: {len(buyer_rows)} bình luận, tiêu cực **{buyer_neg/len(buyer_rows):.0%}**")
    L.append(f"- Bình luận mức nghiêm trọng 3 (scam/không nhận hàng/hại sức khoẻ/hỏng ngay): **{len(sev3)}**")
    L.append(f"- **Mức rủi ro: {risk}** (risk index {risk_raw:.2f})\n")

    L.append("## Theo nền tảng\n")
    L.append("| Nền tảng | Tổng | " + " | ".join(TYPE_VI[t] for t in TYPES) + " |")
    L.append("|---|---|" + "---|" * len(TYPES))
    for p, c in sorted(by_plat.items(), key=lambda x: -sum(x[1].values())):
        tot = sum(c.values())
        L.append(f"| {p} | {tot} | " + " | ".join(f"{c[t]} ({c[t]/tot:.0%})" for t in TYPES) + " |")

    L.append("\n## Chủ đề × loại phản hồi\n")
    L.append("| Chủ đề | Khen | Chê | Nghi ngờ | Hỏi | Điểm rủi ro |")
    L.append("|---|---|---|---|---|---|")
    for tp, c in sorted(topic_type.items(), key=lambda x: -topic_weight.get(x[0], 0)):
        L.append(f"| {TOPIC_VI[tp]} | {c['praise']} | {c['complaint']} | {c['skeptic']} | {c['question']} | {topic_weight.get(tp, 0):.1f} |")

    L.append("\n## 🔴 Chê gì (xếp theo mức nghiêm trọng × lượt like)\n")
    for r in top(lambda r: r["type"] in ("complaint", "skeptic"), a.quotes):
        L.append(f"**[{', '.join(TOPIC_VI[t] for t in r['topics'])}]** {r.get('note') or ''}\n{quote(r)}\n")
    L.append("\n## ❓ Hỏi gì (FAQ cần trả lời sẵn trên PDP / trong ad)\n")
    q_topics = Counter(tp for r in rows if r["type"] == "question" for tp in r["topics"])
    L.append(", ".join(f"{TOPIC_VI[t]}: {n_}" for t, n_ in q_topics.most_common()) or "_Không có_")
    L.append("")
    for r in top(lambda r: r["type"] == "question", a.quotes, key=lambda r: -r["likes"]):
        L.append(f"**[{', '.join(TOPIC_VI[t] for t in r['topics'])}]** {r.get('note') or ''}\n{quote(r)}\n")
    L.append("\n## 🟢 Khen gì (đạn cho creative & proof)\n")
    for r in top(lambda r: r["type"] == "praise", a.quotes, key=lambda r: (-(r["buyer"] or 0), -r["likes"])):
        L.append(f"**[{', '.join(TOPIC_VI[t] for t in r['topics'])}]** {r.get('note') or ''}\n{quote(r)}\n")

    res = {"labeled": len(rows), "total": len(comments), "unlabeled_ids": unlabeled[:50], "type_share": {t: round(total_types[t]/n, 3) for t in TYPES},
           "per_platform": {p: dict(c) for p, c in by_plat.items()}, "topic_type": {t: dict(c) for t, c in topic_type.items()},
           "topic_risk_weight": {t: round(w, 2) for t, w in topic_weight.items()}, "risk_index": round(risk_raw, 3),
           "risk_level": risk, "severity3_count": len(sev3),
           "buyer_negative_share": round(buyer_neg / len(buyer_rows), 3) if buyer_rows else None}
    (out / "report.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("--input", "-i", action="append", required=True,
                   help="platform:path (vd tiktok:post1.info.json). Lặp lại nhiều lần.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--batch-size", type=int, default=150)
    p.add_argument("--max-chars", type=int, default=600)
    p.set_defaults(fn=cmd_prep)
    r = sub.add_parser("report")
    r.add_argument("--out-dir", required=True)
    r.add_argument("--quotes", type=int, default=8)
    r.set_defaults(fn=cmd_report)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

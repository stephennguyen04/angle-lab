#!/usr/bin/env python3
"""shopify_product.py: Lấy cấu trúc giá / variant / bundle của 1 trang sản phẩm (ưu tiên Shopify).

Dùng:
  python3 shopify_product.py "https://brand.com/products/handle" [--out product.json]

Với Shopify: đọc /products/<handle>.js (công khai) → variants, giá, compare-at (giá gạch), options
(thường lộ ra bundle kiểu "1 Pack / 2 Pack / 3 Pack"). Đồng thời quét HTML tìm dấu hiệu
quantity-break app, upsell, review app, bảo hành, freeship.
Không phải Shopify: vẫn trả về các marker từ HTML để AI đọc tiếp.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from urllib.parse import urlparse

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

MARKERS = {
    "quantity_break_app": r"kaching|bundler|quantity[-_ ]?break|volume[-_ ]?discount|fast[-_ ]?bundle|bundle[-_ ]?deals",
    "upsell_app": r"reconvert|zipify|aftersell|one[-_ ]?click[-_ ]?upsell|frequently bought together|selleasy|candy rack",
    "review_app": r"judge\.me|loox|okendo|yotpo|stamped\.io|reviews\.io|trustpilot",
    "subscription": r"subscribe (&|and) save|recharge|skio|appstle|subscription",
    "guarantee": r"money[- ]back|guarantee|risk[- ]free|hoàn tiền|đổi trả",
    "free_shipping": r"free shipping|miễn phí vận chuyển|freeship",
    "countdown_scarcity": r"countdown|hurry|only \d+ left|selling fast|sắp hết|chỉ còn",
    "bnpl": r"klarna|afterpay|shop pay installments|sezzle|zip pay",
    "most_popular_badge": r"most popular|best value|best seller|phổ biến nhất|bán chạy",
    "free_gift": r"free gift|quà tặng|tặng kèm",
}


def fetch(url: str, timeout=30) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        print(f"[warn] {url}: {e}", file=sys.stderr)
        return 0, ""


def money(cents):
    return None if cents is None else round(cents / 100, 2)


def analyze(url: str) -> dict:
    u = urlparse(url)
    base = f"{u.scheme}://{u.netloc}"
    m = re.search(r"/products/([^/?#]+)", u.path)
    out = {"url": url, "platform": "unknown", "product": None, "variants": [], "markers": {}, "bundle_guess": None}

    status, html = fetch(url)
    out["http_status"] = status
    low = html.lower()
    if "cdn.shopify.com" in low or "shopify" in low[:20000]:
        out["platform"] = "shopify"
    out["markers"] = {k: bool(re.search(p, low)) for k, p in MARKERS.items()}
    tiers = re.findall(r"(buy\s*\d+\s*get\s*\d+[^<]{0,40}|mua\s*\d+\s*tặng\s*\d+[^<]{0,40}|\b\d\s*(?:pack|pcs|bottles?|units?|hộp|chai|bộ)\b[^<]{0,40}save[^<]{0,20})", low)
    out["offer_text_snippets"] = sorted(set(t.strip()[:80] for t in tiers))[:15]

    if m:
        st, js = fetch(f"{base}/products/{m[1]}.js")
        if st == 200 and js.strip().startswith("{"):
            out["platform"] = "shopify"
            p = json.loads(js)
            out["product"] = {
                "title": p.get("title"), "vendor": p.get("vendor"), "type": p.get("type"),
                "tags": p.get("tags"), "options": [o.get("name") if isinstance(o, dict) else o for o in p.get("options", [])],
                "price_min": money(p.get("price_min")), "price_max": money(p.get("price_max")),
                "compare_at_min": money(p.get("compare_at_price_min")), "images": len(p.get("images", [])),
                "created_at": p.get("created_at"), "published_at": p.get("published_at"),
            }
            for v in p.get("variants", []):
                price, cap = money(v.get("price")), money(v.get("compare_at_price"))
                qty = None
                mq = re.search(r"(\d+)\s*(x|pack|pcs|bottles?|units?|hộp|chai|bộ|set)", (v.get("title") or "").lower())
                if mq:
                    qty = int(mq[1])
                out["variants"].append({
                    "title": v.get("title"), "price": price, "compare_at": cap,
                    "discount_pct": round((1 - price / cap) * 100) if price and cap and cap > price else None,
                    "available": v.get("available"), "qty_in_title": qty,
                    "unit_price": round(price / qty, 2) if price and qty else None,
                })
            qv = [v for v in out["variants"] if v["qty_in_title"]]
            if len(qv) >= 2:
                out["bundle_guess"] = "Bundle theo số lượng nằm trong variant: " + " | ".join(
                    f"{v['title']}: {v['price']} ({v['unit_price']}/cái)" for v in sorted(qv, key=lambda x: x["qty_in_title"]))
            elif out["markers"].get("quantity_break_app"):
                out["bundle_guess"] = "Có app quantity-break (giá bậc thang hiển thị bằng widget, không nằm trong variant). Xem screenshot."
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = analyze(a.url)
    s = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(s)
    print(s)


if __name__ == "__main__":
    main()

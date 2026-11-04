#!/usr/bin/env python3
"""apify_fetch.py: Chạy actor Apify (bình luận Facebook/Instagram, bài IG, ad Meta) rồi tải kết quả về đúng định dạng angle-lab.

Cần token Apify: đặt biến môi trường APIFY_TOKEN (Apify Console → Settings → API & Integrations).
Token KHÔNG được ghi vào file, log hay repo.

Preset (actor mặc định, đổi được bằng --actor nếu bạn dùng actor khác):
  fb-comments  apify~facebook-comments-scraper   URL bài/ad Facebook      → comments/*.json  (đọc bằng comments.py prep)
  ig-comments  apify~instagram-comment-scraper   URL bài/reel Instagram   → comments/*.json
  ig-posts     apify~instagram-scraper           URL profile/bài/hashtag  → items.json (đưa vào ig_collect.py import)
  fb-ads       apify~facebook-ads-scraper        URL Ad Library           → items.json (đưa vào adlib_parse.py)

Dùng:
  APIFY_TOKEN=… python3 apify_fetch.py fb-comments <url1> <url2> … --limit 500 --out-dir research/x/04-comments/raw/apify
  APIFY_TOKEN=… python3 apify_fetch.py ig-comments <reel_url> … --limit 300 --out-dir …
  APIFY_TOKEN=… python3 apify_fetch.py ig-posts https://www.instagram.com/brand/ --limit 80 --out-dir research/x/01-scale/apify
  python3 apify_fetch.py dataset <datasetId | runId> --kind fb-comments --out-dir …     # tải kết quả run đã chạy trên Console
  python3 apify_fetch.py file <items.json> --kind ig-comments --out-dir …                # file đã tải tay từ Apify

Chi phí: actor Apify tính phí theo lượng kết quả. Đặt --limit vừa đủ; script in số item trước khi ghi.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

API = os.environ.get("APIFY_API_BASE", "https://api.apify.com/v2")

PRESETS = {
    "fb-comments": {"actor": "apify~facebook-comments-scraper",
                    "input": lambda urls, n: {"startUrls": [{"url": u} for u in urls], "resultsLimit": n, "includeNestedComments": True}},
    "ig-comments": {"actor": "apify~instagram-comment-scraper",
                    "input": lambda urls, n: {"directUrls": urls, "resultsLimit": n, "includeNestedComments": True}},
    "ig-posts": {"actor": "apify~instagram-scraper",
                 "input": lambda urls, n: {"directUrls": urls, "resultsType": "posts", "resultsLimit": n, "addParentData": True}},
    "fb-ads": {"actor": "apify~facebook-ads-scraper",
               "input": lambda urls, n: {"startUrls": [{"url": u} for u in urls], "resultsLimit": n}},
}


def token() -> str:
    t = os.environ.get("APIFY_TOKEN", "").strip()
    if not t:
        sys.exit("Thiếu APIFY_TOKEN. Lấy ở Apify Console → Settings → API & Integrations, rồi: export APIFY_TOKEN=…")
    return t


def call(method: str, path: str, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method,
                                 headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            sys.exit("Apify từ chối token (401). Kiểm tra lại APIFY_TOKEN.")
        if e.code == 402:
            sys.exit("Tài khoản Apify hết credit / cần nâng gói (402).")
        sys.exit(f"Apify lỗi {e.code}: {msg}")


def run_actor(actor: str, inp: dict, wait_max: int) -> str:
    run = call("POST", f"/acts/{actor}/runs", inp)["data"]
    rid = run["id"]
    print(f"▶ đã chạy {actor} · run {rid}", file=sys.stderr)
    t0 = time.time()
    while True:
        st = call("GET", f"/actor-runs/{rid}")["data"]
        status = st["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
        if time.time() - t0 > wait_max:
            sys.exit(f"Quá {wait_max}s chưa xong. Run vẫn chạy trên Apify; tải sau bằng: apify_fetch.py dataset {rid} --kind …")
        print(f"  … {status} ({int(time.time() - t0)}s)", file=sys.stderr)
        time.sleep(float(os.environ.get("APIFY_POLL_SECONDS", "8")))
    if status != "SUCCEEDED":
        sys.exit(f"Run {rid} kết thúc với trạng thái {status}. Xem log trên Apify Console.")
    return st["defaultDatasetId"]


def try_call(path: str):
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {token()}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("Apify từ chối token (401). Kiểm tra lại APIFY_TOKEN.")
        return None


def dataset_items(ds_or_run: str) -> list:
    """Nhận dataset id hoặc run id (thử run trước, không phải thì coi là dataset)."""
    info = try_call(f"/actor-runs/{ds_or_run}")
    ds = info["data"]["defaultDatasetId"] if info and info.get("data") else ds_or_run
    items, offset = [], 0
    while True:
        req = urllib.request.Request(f"{API}/datasets/{ds}/items?format=json&clean=true&offset={offset}&limit=1000",
                                     headers={"Authorization": f"Bearer {token()}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            page = json.loads(r.read().decode("utf-8"))
        items += page
        if len(page) < 1000:
            return items
        offset += 1000


# ---------- chuẩn hoá ----------
def g(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return None


def platform_of(url: str | None, kind: str) -> str:
    u = (url or "").lower()
    if "instagram.com" in u:
        return "instagram"
    if "facebook.com" in u or "fb.com" in u or "fb.watch" in u:
        return "facebook"
    return "instagram" if kind.startswith("ig") else "facebook"


def flatten_comment(c: dict, depth=0):
    yield c, depth
    for r in c.get("replies") or c.get("childComments") or []:
        if isinstance(r, dict):
            yield from flatten_comment(r, depth + 1)


def comments_to_files(items: list, kind: str, out: Path, fallback_urls: list[str]) -> dict:
    """Gom bình luận theo bài → comments/<id>.json dạng {webpage_url, platform, comments[]} (comments.py đọc thẳng)."""
    by_post = defaultdict(list)
    for it in items:
        if not isinstance(it, dict):
            continue
        # actor bài IG có thể trả kèm latestComments
        nested = it.get("latestComments") if isinstance(it.get("latestComments"), list) else None
        src = nested if nested is not None else [it]
        post_url = g(it, "postUrl", "facebookUrl", "inputUrl", "url", "postURL", "post_url") if nested is not None else None
        for c in src:
            # trả lời lồng thừa hưởng URL bài của bình luận gốc
            root_url = post_url or g(c, "postUrl", "facebookUrl", "inputUrl", "post_url", "url") or (fallback_urls[0] if len(fallback_urls) == 1 else None)
            for cc, depth in flatten_comment(c):
                text = g(cc, "text", "commentText", "message", "content")
                if not text:
                    continue
                url = g(cc, "postUrl", "facebookUrl", "inputUrl", "post_url") or root_url
                url = re.sub(r"[?#].*$", "", str(url)) if url else "unknown"
                depth = depth or int(g(cc, "threadingDepth", "depth") or 0) or (1 if g(cc, "replyToCommentId", "parentId", "parent_id") else 0)
                by_post[url].append({"text": text, "like_count": g(cc, "likesCount", "likes", "reactionsCount", "likeCount") or 0,
                                     "author": g(cc, "profileName", "ownerUsername", "username", "authorName"),
                                     "timestamp": g(cc, "date", "timestamp", "createdAt", "created_time"),
                                     "parent": "reply" if depth else "root"})
    cdir = out / "comments"
    cdir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for url, cs in by_post.items():
        code = re.sub(r"\W+", "_", url.split("//")[-1])[-60:].strip("_") or "post"
        (cdir / f"{code}.json").write_text(json.dumps({"webpage_url": url, "platform": platform_of(url, kind), "comments": cs},
                                                      ensure_ascii=False), encoding="utf-8")
        summary[url] = len(cs)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=[*PRESETS, "dataset", "file"])
    ap.add_argument("targets", nargs="+", help="URL (preset) · datasetId/runId (dataset) · file json (file)")
    ap.add_argument("--kind", choices=list(PRESETS), help="với dataset/file: loại dữ liệu")
    ap.add_argument("--actor", help="đổi actor (vd ten-ban~actor-khac)")
    ap.add_argument("--input", help="file JSON input tuỳ chỉnh cho actor (ghi đè input mặc định)")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--wait", type=int, default=1800, help="chờ tối đa (giây)")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if a.mode in PRESETS:
        kind = a.mode
        p = PRESETS[kind]
        inp = json.loads(Path(a.input).read_text(encoding="utf-8")) if a.input else p["input"](a.targets, a.limit)
        items = dataset_items(run_actor(a.actor or p["actor"], inp, a.wait))
        urls = a.targets
    else:
        if not a.kind:
            sys.exit("Cần --kind (fb-comments | ig-comments | ig-posts | fb-ads)")
        kind = a.kind
        if a.mode == "dataset":
            items = dataset_items(a.targets[0])
        else:
            items = []
            for f in a.targets:
                d = json.loads(Path(f).read_text(encoding="utf-8-sig"))
                items += d if isinstance(d, list) else d.get("items") or [d]
        urls = []
    print(f"Nhận {len(items)} item từ Apify", file=sys.stderr)
    (out / "items.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

    if kind in ("fb-comments", "ig-comments") or (kind == "ig-posts" and any(isinstance(i, dict) and i.get("latestComments") for i in items)):
        summ = comments_to_files(items, kind, out, urls)
        n = sum(summ.values())
        print(f"→ {n} bình luận / {len(summ)} bài → {out}/comments/")
        plat = "facebook" if kind == "fb-comments" else "instagram"
        print("Bước tiếp: python3 comments.py prep --out-dir <04-comments> " + " ".join(f"-i {plat}:{out}/comments/{f.name}" for f in sorted((out / 'comments').glob('*.json'))[:3]) + " …")
    if kind == "ig-posts":
        print(f"Bài IG: python3 ig_collect.py import {out}/items.json --out-dir <01-scale/ig>")
    if kind == "fb-ads":
        print(f"Ad Meta: python3 adlib_parse.py -i {out}/items.json -o <01-scale/ads_raw.json>")


if __name__ == "__main__":
    main()

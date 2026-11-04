#!/usr/bin/env python3
"""ig_collect.py: Thu thập bài/reel Instagram công khai (số liệu + bình luận) cho bảng điểm angle.

Nguồn (chọn 1):
  A. Trực tiếp bằng instaloader (pip install instaloader). Nên đăng nhập 1 lần: `instaloader -l <user>` để có session,
     rồi truyền --login <user>. Không đăng nhập thì Instagram chặn rất nhanh.
       python3 ig_collect.py profile <username>  [--reels-only] [--limit 60] [--since 2026-08-01] [--comments 200]
       python3 ig_collect.py tagged  <username>                 # bài người khác tag brand (UGC, affiliate)
       python3 ig_collect.py hashtag <tag>                       # cần đăng nhập
       python3 ig_collect.py urls    <url1> <url2> …             # từng bài/reel cụ thể (vd lấy từ ad hợp tác)
  B. Từ file có sẵn (không cần đăng nhập):
       python3 ig_collect.py import <file.json|.jsonl|.csv> …    # yt-dlp .info.json, export Apify (Instagram scraper), CSV

Output trong --out-dir (mặc định ig/):
  posts.csv            : angle,angle_name,platform,url,creator,views,likes,comments,shares,saves,followers,date,
                         is_video,is_partnership,sponsors,hashtags,caption,video_url  (angle để trống cho AI gán)
  comments/<code>.json : {"webpage_url", "comments":[{text, like_count, author, timestamp}]} → đọc thẳng bằng comments.py prep

Lưu ý: chỉ lấy dữ liệu công khai, giữ --limit vừa phải, có độ trễ giữa các request. Tôn trọng điều khoản Instagram.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csvio import parse_count, read_csv_rows  # noqa: E402

FIELDS = ["angle", "angle_name", "platform", "url", "creator", "views", "likes", "comments", "shares", "saves", "followers",
          "date", "is_video", "is_partnership", "sponsors", "hashtags", "caption", "video_url"]

# Tên trường của các nguồn export phổ biến (Apify Instagram scraper, yt-dlp, tự export)
ALIASES = {
    "url": ["url", "webpage_url", "post_url", "link", "inputUrl"],
    "shortcode": ["shortCode", "shortcode", "code", "id"],
    "creator": ["ownerUsername", "owner_username", "uploader", "uploader_id", "channel", "username", "author"],
    "views": ["videoPlayCount", "video_play_count", "playCount", "videoViewCount", "video_view_count", "view_count", "views", "plays"],
    "likes": ["likesCount", "like_count", "likes", "likes_count"],
    "comments": ["commentsCount", "comment_count", "comments_count", "comments"],
    "shares": ["sharesCount", "reshareCount", "repost_count", "shares"],
    "saves": ["savesCount", "saves"],
    "followers": ["ownerFollowersCount", "followersCount", "channel_follower_count", "followers"],
    "date": ["timestamp", "taken_at", "upload_date", "date", "date_utc"],
    "caption": ["caption", "description", "title", "text"],
    "is_video": ["isVideo", "is_video", "type", "productType", "product_type"],
    "is_partnership": ["isPaidPartnership", "paidPartnership", "is_paid_partnership", "isSponsored", "is_sponsored", "branded_content"],
    "sponsors": ["sponsors", "sponsor_users", "coauthorProducers", "taggedUsers"],
    "video_url": ["videoUrl", "video_url", "url_video"],
}


def first(d: dict, key: str):
    for k in ALIASES[key]:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return None


def num(v):
    return parse_count(v)


def iso(v):
    if v in (None, ""):
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, (int, float)) or str(v).isdigit():
        n = float(v)
        if 19000101 <= n <= 21001231:          # yt-dlp upload_date YYYYMMDD
            s = str(int(n))
            return f"{s[:4]}-{s[4:6]}-{s[6:]}"
        return datetime.fromtimestamp(n / 1000 if n > 1e11 else n, tz=timezone.utc).date().isoformat()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v))
    return m[1] if m else None


def truthy(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, list):
        return bool(v)
    return str(v).strip().lower() in ("1", "true", "yes", "video", "clips", "reel", "graphvideo")


def hashtags_of(caption: str | None, given=None):
    if isinstance(given, list):
        return ",".join(given)
    return ",".join(re.findall(r"#(\w+)", caption or ""))


def row_from_dict(d: dict) -> dict:
    """1 bài từ export (Apify/yt-dlp/CSV) → dòng posts.csv."""
    url = first(d, "url")
    sc = first(d, "shortcode")
    if not url and sc:
        url = f"https://www.instagram.com/p/{sc}/"
    cap = first(d, "caption")
    creator = first(d, "creator") or ""
    if isinstance(creator, dict):
        creator = creator.get("username") or ""
    sp = first(d, "sponsors")
    if isinstance(sp, list):
        sp = ",".join((x.get("username") or x.get("full_name") or "") if isinstance(x, dict) else str(x) for x in sp)
    return {
        "angle": d.get("angle", ""), "angle_name": d.get("angle_name", ""), "platform": "instagram",
        "url": url, "creator": creator,
        "views": num(first(d, "views")), "likes": num(first(d, "likes")), "comments": num(first(d, "comments")),
        "shares": num(first(d, "shares")), "saves": num(first(d, "saves")), "followers": num(first(d, "followers")),
        "date": iso(first(d, "date")), "is_video": truthy(first(d, "is_video")) or bool(first(d, "views")),
        "is_partnership": truthy(first(d, "is_partnership")) or bool(re.search(r"paid partnership|#ad\b|#sponsored|hợp tác có trả phí", cap or "", re.I)),
        "sponsors": sp or "", "hashtags": hashtags_of(cap, d.get("hashtags")), "caption": (cap or "")[:500].replace("\n", " "),
        "video_url": first(d, "video_url"),
    }


def comments_from_dict(d: dict) -> list[dict]:
    out = []
    src = d.get("latestComments") or (d.get("comments") if isinstance(d.get("comments"), list) else None) or []
    for c in src:
        if not isinstance(c, dict):
            continue
        out.append({"text": c.get("text"), "like_count": c.get("likesCount") or c.get("like_count") or 0,
                    "author": c.get("ownerUsername") or c.get("author"), "timestamp": c.get("timestamp")})
        for r in c.get("replies") or []:
            if isinstance(r, dict):
                out.append({"text": r.get("text"), "like_count": r.get("likesCount") or 0, "author": r.get("ownerUsername"),
                            "timestamp": r.get("timestamp"), "parent": "reply"})
    return [c for c in out if c.get("text")]


# ---------- instaloader ----------
def row_from_post(post, followers=None) -> dict:
    g = lambda name, default=None: getattr(post, name, default)  # noqa: E731
    views = None
    for attr in ("video_play_count", "video_view_count"):
        try:
            v = g(attr)
            if v:
                views = v
                break
        except Exception:  # noqa: BLE001
            continue
    sponsors = []
    try:
        sponsors = [getattr(s, "username", str(s)) for s in (g("sponsor_users") or [])]
    except Exception:  # noqa: BLE001
        pass
    cap = g("caption") or ""
    try:
        is_sp = bool(g("is_sponsored"))
    except Exception:  # noqa: BLE001
        is_sp = False
    return {
        "angle": "", "angle_name": "", "platform": "instagram", "url": f"https://www.instagram.com/p/{g('shortcode')}/",
        "creator": g("owner_username"), "views": num(views), "likes": num(g("likes")), "comments": num(g("comments")),
        "shares": None, "saves": None, "followers": followers, "date": iso(g("date_utc")), "is_video": bool(g("is_video")),
        "is_partnership": is_sp or bool(sponsors), "sponsors": ",".join(sponsors),
        "hashtags": ",".join(g("caption_hashtags") or []), "caption": cap[:500].replace("\n", " "),
        "video_url": g("video_url") if g("is_video") else None,
    }


def comments_from_post(post, limit: int) -> list[dict]:
    out = []
    try:
        for c in post.get_comments():
            out.append({"text": c.text, "like_count": getattr(c, "likes_count", 0), "author": getattr(c.owner, "username", None),
                        "timestamp": iso(getattr(c, "created_at_utc", None))})
            for r in getattr(c, "answers", []) or []:
                out.append({"text": r.text, "like_count": getattr(r, "likes_count", 0), "author": getattr(r.owner, "username", None),
                            "timestamp": iso(getattr(r, "created_at_utc", None)), "parent": "reply"})
            if len(out) >= limit:
                break
    except Exception as e:  # noqa: BLE001
        print(f"[warn] không lấy được bình luận {getattr(post, 'shortcode', '?')}: {e}", file=sys.stderr)
    return out[:limit]


def collect_instaloader(a) -> tuple[list[dict], dict]:
    try:
        import instaloader  # type: ignore
    except ImportError:
        sys.exit("Thiếu instaloader: pip install instaloader  (hoặc dùng `import` với file export có sẵn)")
    L = instaloader.Instaloader(download_pictures=False, download_videos=False, download_video_thumbnails=False,
                                download_geotags=False, download_comments=False, save_metadata=False,
                                compress_json=False, quiet=True)
    if a.login:
        try:
            L.load_session_from_file(a.login)
        except Exception as e:  # noqa: BLE001
            sys.exit(f"Không nạp được session '{a.login}'. Chạy trước: instaloader -l {a.login}  ({e})")
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc) if a.since else None
    followers_cache: dict[str, int | None] = {}

    def followers_of(post):
        u = getattr(post, "owner_username", None)
        if u not in followers_cache:
            try:
                followers_cache[u] = post.owner_profile.followers
            except Exception:  # noqa: BLE001
                followers_cache[u] = None
        return followers_cache[u]

    if a.mode == "urls":
        codes = [re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", u)[1] for u in a.targets if re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", u)]
        it = (instaloader.Post.from_shortcode(L.context, c) for c in codes)
    elif a.mode == "hashtag":
        h = instaloader.Hashtag.from_name(L.context, a.targets[0].lstrip("#"))
        it = h.get_posts_resumable() if hasattr(h, "get_posts_resumable") else h.get_top_posts()
    else:
        prof = instaloader.Profile.from_username(L.context, a.targets[0].lstrip("@"))
        followers_cache[prof.username] = prof.followers
        if a.mode == "tagged":
            it = prof.get_tagged_posts()
        elif a.reels_only and hasattr(prof, "get_reels"):
            it = prof.get_reels()
        else:
            it = prof.get_posts()

    rows, comments = [], {}
    for post in it:
        if since and getattr(post, "date_utc", None) and post.date_utc.replace(tzinfo=timezone.utc) < since:
            if a.mode == "profile":
                break            # profile trả theo thời gian giảm dần
            continue
        if a.reels_only and not getattr(post, "is_video", False):
            continue
        row = row_from_post(post, followers_of(post))
        rows.append(row)
        if a.comments:
            comments[post.shortcode] = {"webpage_url": row["url"], "comments": comments_from_post(post, a.comments)}
        print(f"  {row['url']}  view={row['views']} like={row['likes']} cmt={row['comments']}", file=sys.stderr)
        if len(rows) >= a.limit:
            break
        time.sleep(a.delay)
    return rows, comments


def collect_import(files: list[str]) -> tuple[list[dict], dict]:
    rows, comments = [], {}
    for f in files:
        p = Path(f)
        if p.suffix.lower() == ".csv":
            items = read_csv_rows(p)
        elif p.suffix.lower() == ".jsonl":
            items = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            items = data if isinstance(data, list) else data.get("items") or data.get("data") or [data]
        for d in items:
            if not isinstance(d, dict):
                continue
            # yt-dlp: extractor Instagram; Apify: có url/shortCode
            row = row_from_dict(d)
            if not row["url"]:
                continue
            rows.append(row)
            cs = comments_from_dict(d)
            if cs:
                code = re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", row["url"])
                comments[code[1] if code else str(len(comments))] = {"webpage_url": row["url"], "comments": cs}
    return rows, comments


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["profile", "tagged", "hashtag", "urls", "import"])
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--out-dir", default="ig")
    ap.add_argument("--login")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--since")
    ap.add_argument("--comments", type=int, default=0, help="số bình luận tối đa mỗi bài (0 = không lấy)")
    ap.add_argument("--reels-only", action="store_true")
    ap.add_argument("--delay", type=float, default=2.5)
    a = ap.parse_args()

    rows, comments = collect_import(a.targets) if a.mode == "import" else collect_instaloader(a)
    seen, uniq = set(), []
    for r in rows:
        k = (r["url"] or "").split("?")[0].rstrip("/").lower()
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    out = Path(a.out_dir)
    (out / "comments").mkdir(parents=True, exist_ok=True)
    path = out / "posts.csv"
    old = read_csv_rows(path) if path.exists() else []
    old_urls = {(r.get("url") or "").split("?")[0].rstrip("/").lower(): r for r in old}
    for r in uniq:  # giữ angle đã gán ở lần chạy trước
        prev = old_urls.pop((r["url"] or "").split("?")[0].rstrip("/").lower(), None)
        if prev and prev.get("angle"):
            r["angle"], r["angle_name"] = prev["angle"], prev.get("angle_name", "")
    merged = list(old_urls.values()) + uniq
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in merged:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in FIELDS})
    for code, c in comments.items():
        (out / "comments" / f"{code}.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    n_part = sum(1 for r in uniq if r["is_partnership"])
    print(f"→ {len(uniq)} bài mới ({len(merged)} tổng) · {n_part} bài hợp tác/được tài trợ · "
          f"{sum(len(c['comments']) for c in comments.values())} bình luận → {out}/")
    print("Bước tiếp: AI gán cột angle trong posts.csv; bình luận: comments.py prep -i instagram:" + str(out / "comments" / "<file>.json"))


if __name__ == "__main__":
    main()

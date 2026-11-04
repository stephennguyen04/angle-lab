# Cách lấy bình luận theo nền tảng (chỉ mở khi cần)

| Nguồn | Cách lấy |
|---|---|
| Facebook post/ad | `apify_fetch.py fb-comments <URL bài> --limit 500 --out-dir raw/apify_fb` (cần `APIFY_TOKEN`). Không có Apify: người dùng export (ExportComments, extension) ra CSV/JSON hoặc dán vào .txt. CSV Excel (dấu `;`, cột "Nội dung") đọc được trực tiếp |
| Instagram | `apify_fetch.py ig-comments <URL reel>` hoặc `ig_collect.py profile <brand> --reels-only --comments 300 --login <user>` (instaloader), `ig_collect.py tagged <brand>`, `ig_collect.py import <export Apify>.json` → `ig/comments/*.json` |
| TikTok / YouTube | `yt-dlp --skip-download --write-comments --write-info-json -o "raw/%(extractor)s_%(id)s" <url>` → `.info.json` |
| Amazon / Trustpilot / Shopee / Etsy | WebFetch trang review (lọc 1–3 sao và 5 sao) → CSV `text,rating,likes,date` |
| Reddit | thêm `.json` vào URL thread → `body` + `score` |
| Review trên PDP (Judge.me, Loox…) | từ `02-funnel/*.txt`; đặt `platform=pdp` để tách riêng vì có thể do shop tự đăng |

Định dạng `comments.py prep` nhận: yt-dlp `.info.json`, JSON/JSONL (kể cả item Apify), CSV (`,` `;` tab, BOM), TXT (mỗi bình luận cách nhau 1 dòng trống).

Nhãn JSON kiểu cũ vẫn đọc được: `{"id":"c00012","type":"complaint","topics":["shipping"],"severity":2,"buyer":true,"note":"…"}`.

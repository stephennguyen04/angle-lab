---
name: apify
description: Dùng Apify để lấy dữ liệu khó lấy ở Facebook và Instagram (bình luận bài/ad Facebook, bình luận reel/bài Instagram kèm trả lời lồng, bài/reel Instagram của profile hoặc hashtag, ad Meta Ad Library), rồi chuyển thẳng sang định dạng của angle-lab để phân tích. Dùng khi nói "lấy bình luận bằng Apify", "cào comment Facebook", "comment Instagram", "Apify", "không lấy được bình luận vì phải đăng nhập".
argument-hint: "<fb-comments | ig-comments | ig-posts | fb-ads | dataset> <URL…>"
---

# /angle-lab:apify: Lấy bình luận & dữ liệu FB/IG qua Apify

Facebook và Instagram ẩn phần lớn bình luận với người chưa đăng nhập. Các actor trên Apify xử lý được việc đó và trả về dữ liệu sạch.

## Cài một lần

1. Tạo tài khoản apify.com → Console → **Settings → API & Integrations** → copy API token.
2. `export APIFY_TOKEN=…` (chỉ đặt trong terminal / biến môi trường. **Không** ghi token vào file, repo hay chat).
3. Actor tính phí theo lượng kết quả: đặt `--limit` vừa đủ. Script in số item nhận được.

## Lệnh

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"
# Bình luận Facebook (bài, reel, post của ad): lấy cả trả lời lồng
python3 "$S/apify_fetch.py" fb-comments "<URL bài 1>" "<URL bài 2>" --limit 500 --out-dir research/<slug>/04-comments/raw/apify_fb
# Bình luận Instagram (reel/bài)
python3 "$S/apify_fetch.py" ig-comments "<URL reel>" … --limit 300 --out-dir research/<slug>/04-comments/raw/apify_ig
# Bài/reel Instagram của profile/hashtag (có số view, like, comment, follower)
python3 "$S/apify_fetch.py" ig-posts "https://www.instagram.com/<brand>/" --limit 80 --out-dir research/<slug>/01-scale/apify_ig
# Ad Meta Ad Library
python3 "$S/apify_fetch.py" fb-ads "<URL Ad Library>" --limit 300 --out-dir research/<slug>/01-scale/apify_ads
# Run đã chạy trên Apify Console / file đã tải tay
python3 "$S/apify_fetch.py" dataset <runId hoặc datasetId> --kind fb-comments --out-dir …
python3 "$S/apify_fetch.py" file <items.json> --kind ig-comments --out-dir …
```
- Actor mặc định: `apify~facebook-comments-scraper`, `apify~instagram-comment-scraper`, `apify~instagram-scraper`, `apify~facebook-ads-scraper`. Dùng actor khác thì thêm `--actor <owner~name>`. Input khác mặc định thì thêm `--input input.json`.
- Script chạy bất đồng bộ (không bị giới hạn 300 giây) và chờ tối đa `--wait` giây. Quá thời gian thì in run id để tải sau bằng `dataset`.
- Tên trường của mỗi actor có thể khác nhau; script tự nhận các tên phổ biến (`text`, `likesCount`, `profileName`/`ownerUsername`, `facebookUrl`/`postUrl`, `replies`, `threadingDepth`…).

## Đưa vào phân tích

- Bình luận → `comments/*.json` (mỗi bài 1 file, giữ URL bài, đánh dấu trả lời lồng):
  `comments.py prep --out-dir research/<slug>/04-comments -i facebook:<file> -i instagram:<file> …` rồi gắn nhãn theo `/angle-lab:comments`.
- Bài IG → `ig_collect.py import <out>/items.json --out-dir research/<slug>/01-scale/ig` → `/angle-lab:scoreboard`.
- Ad Meta → `adlib_parse.py -i <out>/items.json -o research/<slug>/01-scale/ads_raw.json` → `/angle-lab:ad-scale`.

## Lấy bình luận của chính ad đối thủ

Trên Ad Library, mở ad → bấm vào tên page/bài → copy URL bài (dạng `facebook.com/<page>/posts/…` hoặc `…/videos/…`). Đưa URL đó vào `fb-comments`. Ưu tiên ad sống lâu nhất và nhiều bản nhân nhất: đó là bài có nhiều bình luận của **người đã mua** nhất.

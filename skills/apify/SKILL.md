---
name: apify
description: Lấy qua Apify các dữ liệu khó lấy ở FB/IG (bình luận bài/ad Facebook, bình luận reel Instagram kèm trả lời, bài IG, ad Meta) rồi chuyển sang định dạng phân tích. Dùng khi "cào comment Facebook/Instagram", "Apify".
argument-hint: "<fb-comments | ig-comments | ig-posts | fb-ads | dataset> <URL…>"
---

# /angle-lab:apify

Cần `export APIFY_TOKEN=…` (Apify Console → Settings → API & Integrations; không ghi token vào file/repo/chat). Actor tính phí theo số kết quả: đặt `--limit` vừa đủ.
```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"
python3 "$S/apify_fetch.py" fb-comments "<URL bài/ad>" … --limit 500 --out-dir research/<slug>/04-comments/raw/apify_fb
python3 "$S/apify_fetch.py" ig-comments "<URL reel>" … --limit 300 --out-dir research/<slug>/04-comments/raw/apify_ig
python3 "$S/apify_fetch.py" ig-posts "https://www.instagram.com/<brand>/" --limit 80 --out-dir research/<slug>/01-scale/apify_ig
python3 "$S/apify_fetch.py" fb-ads "<URL Ad Library>" --limit 300 --out-dir research/<slug>/01-scale/apify_ads
python3 "$S/apify_fetch.py" dataset <runId|datasetId> --kind fb-comments --out-dir …     # run đã chạy trên Console
```
Đổi actor: `--actor owner~name`; input riêng: `--input input.json`. Script chạy bất đồng bộ (chờ tối đa `--wait` giây); quá giờ thì in run id để tải sau.

**Tiếp:** bình luận → `comments.py prep -i facebook:<raw>/comments/<file>.json …` · bài IG → `ig_collect.py import <out>/items.json` · ad → `adlib_parse.py -i <out>/items.json`. Không Read `items.json`.

Bình luận của ad đối thủ: mở ad trên Ad Library → bấm vào bài → copy URL bài vào `fb-comments`. Ưu tiên ad sống lâu nhất (nhiều người đã mua).

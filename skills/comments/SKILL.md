---
name: comments
description: Kiểm tra đối thủ bán trên những nền tảng nào (website, TikTok/TikTok Shop, Facebook, Instagram, YouTube, Amazon, Shopee/Lazada, Etsy, Trustpilot, Reddit…), rồi thu thập và đọc TỪNG bình luận/review trên các bài của họ để biết khách khen gì, chê gì, hỏi gì. Kết quả gồm rủi ro sản phẩm, FAQ/objection, proof cho creative, và điểm để làm tốt hơn đối thủ. Dùng khi nói "đọc bình luận", "khách phản hồi sao", "review đối thủ", "chê gì khen gì hỏi gì", "rủi ro sản phẩm", "họ bán trên nền tảng nào".
argument-hint: "<research/<slug> | brand + link>"
---

# /angle-lab:comments: Tiếng nói khách hàng đa nền tảng

> Phần này **rất quan trọng**: nó cho biết trước rủi ro sản phẩm và điểm để làm tốt hơn đối thủ. Đọc rộng (mọi nền tảng), đọc sâu (đọc từng bình luận, kể cả reply), đọc có hệ thống (gắn nhãn hết rồi mới kết luận).

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/comments.py`. Lưu vào `research/<slug>/04-comments/`.

## 1. Họ bán trên những nền tảng nào?

Tìm bằng WebSearch (chạy song song nhiều query), với `<brand>` và `<tên sản phẩm generic>`:
- `"<brand>" tiktok` · `"<brand>" site:tiktok.com` · `"<brand>" tiktok shop`
- `"<brand>" site:instagram.com` · `"<brand>" site:youtube.com` · `"<brand>" review`
- `"<brand>" site:amazon.com` (đổi theo thị trường: amazon.co.uk, .com.au…) · `"<tên SP>" amazon`
- `"<brand>" site:trustpilot.com` · `"<brand>" site:reddit.com` · `"<brand>" scam OR legit`
- Thị trường VN/SEA: `"<brand>" shopee` · `lazada` · `tiktok shop` · nhóm Facebook
- Sản phẩm generic (dropship): tìm cùng sản phẩm trên AliExpress/Temu/Amazon, vì review ở đó cho biết **chất lượng hàng gốc** dù khác brand.

Ghi `04-comments/platforms.md`: bảng nền tảng · link · có bán không · số follower/đánh giá · ghi chú. Chỉ tính là "có bán" khi thấy shop/listing thật, không phải repost.

## 2. Thu thập bình luận (càng nhiều càng tốt, ưu tiên bài/listing đông tương tác)

| Nguồn | Cách lấy |
|---|---|
| TikTok / YouTube | `yt-dlp --skip-download --write-comments --write-info-json -o "04-comments/raw/%(extractor)s_%(id)s" <url>` → file `.info.json` có sẵn `comments` |
| **Instagram** | `ig_collect.py profile <brand> --reels-only --comments 300 --login <user>` (instaloader, cần session) hoặc `ig_collect.py import <export Apify>.json` → `ig/comments/*.json` đọc thẳng bằng `comments.py prep -i instagram:<file>`. Lấy thêm `tagged <brand>` (UGC/affiliate tag brand) và `urls <link>` cho bài hợp tác creator |
| Facebook post & ad | Thường cần đăng nhập nên **nhờ người dùng export** (ExportComments, Apify, extension) ra CSV/JSON, hoặc copy-paste vào .txt. Với ad đang chạy: mở post của ad từ Ad Library → xem bình luận. CSV từ Excel (dấu `;`, cột tiếng Việt như "Nội dung") đọc được trực tiếp |
| Amazon / Trustpilot / Shopee / Etsy | WebFetch từng trang review (ưu tiên lọc 1–3 sao VÀ 5 sao), lưu thành CSV `text,rating,likes,date` |
| **Apify (khuyên dùng cho Facebook + Instagram)** | `APIFY_TOKEN=… apify_fetch.py fb-comments <URL bài/ad FB> … --limit 500 --out-dir 04-comments/raw/apify_fb` và `apify_fetch.py ig-comments <URL reel> …`. Lấy cả trả lời lồng; ra `comments/*.json` đọc thẳng bằng `comments.py prep -i facebook:<file>`. Run đã chạy trên Apify Console: `apify_fetch.py dataset <runId> --kind fb-comments`. Xem `/angle-lab:apify` |
| Reddit | Thêm `.json` vào cuối URL thread rồi WebFetch → lấy `body` + `score` |
| Review trên chính PDP (Judge.me/Loox…) | Từ text đã capture ở `02-funnel/*.txt`, nhưng **cảnh giác review do shop tự đăng**, nên đánh dấu `platform=pdp` để tách riêng |

Lưu file gốc vào `04-comments/raw/`. Ghi lại đã lấy từ bài nào, bao nhiêu bình luận, còn bỏ sót gì.

## 3. Chuẩn hoá & chia batch

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/comments.py" prep --out-dir research/<slug>/04-comments \
  -i tiktok:raw/tiktok_xxx.info.json -i youtube:raw/youtube_yyy.info.json \
  -i amazon:raw/amazon_reviews.csv -i facebook:raw/fb_ad_post.txt
```
Script dedupe, bỏ bình luận chỉ có emoji, băm tên tác giả (không lưu tên người), chia batch 150 dòng, gợi ý nhãn bằng từ khoá (`hint`), nhưng hint chỉ là gợi ý.

## 4. Gắn nhãn TỪNG bình luận (việc của AI, không lấy mẫu)

Đọc lần lượt `batches/batch_XXX.jsonl` và ghi vào `labels.jsonl` (hoặc `labels/batch_XXX.jsonl` khi nhiều agent chạy song song). Mỗi bình luận đúng 1 dòng:
```json
{"id":"c00012","type":"complaint","topics":["shipping","support_refund"],"severity":2,"buyer":true,"note":"3 tuần chưa nhận, nhắn shop không rep"}
```
- `type`: `praise` (khen) · `complaint` (chê) · `question` (hỏi) · `purchase_intent` (muốn mua/đã đặt) · `skeptic` (nghi scam/hàng Temu/"AI ad") · `tag_friend` · `other`
- `topics`: efficacy, quality, price, shipping, sizing, usage, safety, scam_trust, support_refund, design, smell_taste, durability, competitor, packaging, other
- `severity` (chê/nghi ngờ): 0 cằn nhằn nhẹ · 1 không hài lòng · 2 lỗi thật (hỏng, không hiệu quả, ship rất lâu) · **3 nghiêm trọng** (không nhận hàng/lừa đảo, kích ứng/hại sức khoẻ, hỏng ngay, bị từ chối hoàn tiền)
- `buyer`: true nếu rõ là người đã mua/dùng → **trọng số cao hơn** người chỉ lướt xem ad
- `note`: diễn giải ngắn bằng tiếng Việt, giữ chi tiết cụ thể (con số, bộ phận hỏng, thời gian)

Nhiều batch thì giao cho nhiều agent `angle-lab:comment-miner` song song, mỗi agent một nhóm batch, ghi ra `labels/batch_XXX.jsonl` riêng.
Chú ý: sarcasm ("great, another scam 🙄" là skeptic chứ không phải praise), bình luận seeding của shop (khen chung chung, tài khoản mới, lặp mẫu, nên ghi note "nghi seeding"), và reply của shop (xem shop xử lý khiếu nại thế nào).

## 5. Tổng hợp số liệu

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/comments.py" report --out-dir research/<slug>/04-comments
```
→ `report.md` / `report.json`: tỉ lệ khen/chê/hỏi theo nền tảng, chủ đề × loại, top chê theo severity × like, FAQ, top khen, risk index 🔴🟡🟢. Nếu báo còn bình luận chưa gắn nhãn thì quay lại bước 4.

## 6. Viết insight → `04-comments/insights.md`

1. **Tổng quan:** đã đọc bao nhiêu bình luận / bao nhiêu nền tảng / bao nhiêu bài. Cảm xúc chung. Nền tảng nào khác biệt (ví dụ TikTok khen, Amazon chê chất lượng → hàng không như video).
2. **CHÊ GÌ: rủi ro sản phẩm.** Mỗi vấn đề ghi tần suất · mức nghiêm trọng · đến từ người đã mua hay chưa · 1–2 quote nguyên văn. Phân loại: lỗi sản phẩm (không sửa được bằng marketing, có thể là lý do BỎ) · lỗi vận hành (ship, CSKH, đổi trả: mình làm tốt hơn được) · nghi ngờ uy tín (xử lý bằng proof/brand).
3. **HỎI GÌ: objection & FAQ.** Câu hỏi lặp lại = rào cản mua. Mỗi câu ghi cách trả lời trên PDP, trong ad (đưa vào script), và trong CSKH.
4. **KHEN GÌ: đạn cho creative.** Lợi ích khách thật sự quan tâm (thường khác thứ đối thủ đang quảng cáo!), từ ngữ khách dùng (dùng lại trong hook/copy), khoảnh khắc "wow".
5. **Ngôn ngữ của khách:** 10–20 cụm từ/câu nguyên văn đắt giá nhất để viết hook.
6. **Làm tốt hơn đối thủ:** bảng *Điểm chê/hỏi → Cách mình làm tốt hơn → Áp dụng ở đâu (sản phẩm/offer/PDP/ad/CSKH)*.
7. **Angle gợi ra từ bình luận:** nỗi đau/mong muốn khách nhắc mà đối thủ chưa khai thác.
8. **Verdict rủi ro:** 🔴 / 🟡 / 🟢 + 1 câu giải thích.

Quote giữ nguyên văn (ngôn ngữ gốc), có thể thêm bản dịch. Không đưa tên/username người bình luận vào báo cáo.

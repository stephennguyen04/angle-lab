---
name: ad-scale
description: Đo đối thủ đang scale tới đâu trên Meta Ad Library, gồm số ad active, tốc độ ra ad mới theo tuần (đều hay theo đợt hay ngưng), tuổi ad, ad nhân bản nhiều nhất, landing page trỏ về đâu, và chọn ra 5 video top (winner) để mổ. Dùng khi hỏi "họ chạy bao nhiêu ad", "scale tới đâu", "ra ad mới đều không", "ad nào là winner", "Ad Library của page này".
argument-hint: "<Page ID | tên brand | link Ad Library> [country]"
---

# /angle-lab:ad-scale: Đối thủ đang scale tới đâu?

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/` (nếu trống, xem cách tìm trong `/angle-lab:spy`). Lưu kết quả vào `research/<slug>/01-scale/`.

## 1. Thu thập ad Meta (chọn nguồn theo thứ tự ưu tiên)

Mục tiêu là có đủ các trường: ngày chạy, active, **số bản nhân (collation)**, **placement** (có chạy Instagram không), **lượt tiếp cận EU**, **ad hợp tác creator**, video, landing. Mọi nguồn đều đổ về `adlib_parse.py` → `01-scale/ads_raw.json`.

**A. File HAR (ít rủi ro nhất, dữ liệu đầy đủ nhất).** Nhờ người dùng:
1. Mở Ad Library của page đối thủ (`view_all_page_id=<PAGE_ID>`), quốc gia là thị trường chính. Thêm `&publisher_platforms[0]=instagram` nếu chỉ muốn ad chạy Instagram.
2. Mở DevTools → tab Network, cuộn hết danh sách; bấm "See ad details" ở các ad sống lâu nhất (để có EU reach).
3. Chuột phải trong tab Network → **Save all as HAR** → gửi file.
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_parse.py" -i <file>.har -o research/<slug>/01-scale/ads_raw.json [--page-id <PAGE_ID>]
```

**B. MCP Meta Ads (`ads_library_search`)**, nếu có connector META_ADS:
- Gọi với `page_ids=[<PAGE_ID>]` (ưu tiên) hoặc `search_terms`, `countries=[<CC>]`, `ad_active_status=ALL`, `limit=50`; gọi thêm 1 lần `ACTIVE` để ghi **estimated result count** (tổng ad active).
- Lưu kết quả JSON rồi chạy `adlib_parse.py -i <kết quả>.json -o …/ads_raw.json`. Tool giới hạn 50 ad/lần, đủ để đo nhịp gần đây.

**C. Scraper Playwright** (bắt response GraphQL, không đọc giao diện):
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_scrape.cjs" "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=<CC>&view_all_page_id=<PAGE_ID>&media_type=all" research/<slug>/01-scale/scrape.json --max 300 [--platform instagram] [--details 30]
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_parse.py" -i research/<slug>/01-scale/scrape.graphql.jsonl -o research/<slug>/01-scale/ads_raw.json
```
Gặp login wall/captcha thì chạy lại với `--headful` trên máy người dùng, hoặc chuyển sang cách A.

**D. Export từ tool spy / Apify** (Foreplay, Minea, PiPiAds, actor Meta Ad Library…): `adlib_parse.py` nhận JSON bất kỳ có `ad_archive_id`; CSV thì đưa thẳng cho `ad_cadence.py` (tự nhận tên cột EN/VN, dấu `,` hoặc `;`).

**Lượt tiếp cận EU** chỉ có với ad **có phân phối ở EU / UK / Brazil** (quy định minh bạch DSA). Đối thủ bán ở EU/UK thì chọn quốc gia đó trên Ad Library và mở "See ad details" để lấy. Đối thủ chỉ bán ở Mỹ/VN thì cột này trống, và đó là chuyện bình thường.

## 2. Tính toán

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ad_cadence.py" -i research/<slug>/01-scale/ads_raw.json --brand-domain <shop-domain> --top 5 \
  --out-md research/<slug>/01-scale/scale_auto.md --out-json research/<slug>/01-scale/scale.json
```
Script ra: mức scale, ad mới 7/14/30 ngày, histogram 12 tuần, verdict nhịp ra ad, tuổi ad active, media mix, phân bố landing, xếp hạng winner score, 5 video top.

## 3. Đọc & diễn giải → `01-scale/scale.md`

Đừng chỉ chép số. Diễn giải:
- **Giai đoạn sản phẩm:** đang test (ít ad, ad non) · đang lên (ad mới tăng dần theo tuần) · đỉnh (nhiều ad active, ra ad đều, nhiều ad >30 ngày) · đi xuống (ngưng ra ad mới, chỉ còn ad cũ).
- **Ra ad mới đều không?** Ra đều = có team creative đang test liên tục, đối thủ mạnh. Theo đợt = launch theo batch. Ngưng = có thể đang vắt winner hoặc bỏ sản phẩm.
- **Winner thật:** hạng Long-Runner (≥60 ngày) / Performer (30–59 ngày), nhất là ad có nhiều bản nhân ("N ads use this creative"), tiếp cận EU cao, hoặc được chạy dưới dạng **hợp tác creator** (đối thủ chịu trả tiền creator = đã tin angle).
- **Instagram:** % ad có placement Instagram. Cao → đối thủ coi IG là kênh chính, nên ưu tiên mổ Reels của họ.
- **Nhiều page:** cùng creative chạy trên nhiều page (Brand, Brand EU, Brand Deals…) là dấu hiệu scale mạnh.
- **Landing:** % ad về PDP vs advertorial/listicle → chuyển thông tin cho mảng funnel.
- **Nhiều page / nhiều store?** Nếu cùng creative xuất hiện ở page khác, ghi lại (đối thủ chạy đa page để scale).
- Kết luận 3 dòng: *đang scale tới đâu · tốc độ ra ad · ý nghĩa với mình (thị trường còn chỗ không)*.

Cuối file liệt kê **5 video top** (id, link video/snapshot, số ngày chạy, số bản nhân, lý do chọn), đây là input cho `/angle-lab:top-videos`. Ưu tiên ad active lâu nhất + nhân bản nhiều nhất; đa dạng angle nếu top bị trùng cùng 1 video.

> Ngưỡng "10/50/200 ad active" trong script là heuristic tham khảo, phải so với ngách: ngách nhỏ 30 ad active đã là mạnh.

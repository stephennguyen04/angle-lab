---
name: discover
description: Tự tìm đối thủ đáng spy từ từ khoá ngách trên Meta Ad Library, gom ad theo page rồi xếp hạng theo ad active, ad sống lâu nhất, ad mới 30 ngày, % Instagram; tự loại sàn TMĐT và brand lớn. Kèm link Ad Library từng page. Dùng khi nói "tìm đối thủ", "ai đang bán sản phẩm này", "tìm shop đang chạy ads", "tìm advertiser trong ngách", "chưa có link đối thủ".
argument-hint: "<từ khoá 1, từ khoá 2…> [quốc gia]"
---

# /angle-lab:discover: Tìm đối thủ từ từ khoá ngách

## 1. Chọn từ khoá

Tạo 5–10 từ khoá theo cách khách và quảng cáo thật sự viết, không theo tên kỹ thuật: tên sản phẩm generic ("posture corrector", "đai chống gù"), nỗi đau ("back pain office"), lợi ích, và cả tiếng bản địa của thị trường. Hỏi người dùng thị trường (quốc gia).

## 2. Lấy ad theo từng từ khoá (chọn nguồn)

- **MCP Meta Ads** `ads_library_search` với `search_terms=<từ khoá>`, `countries=[<CC>]`, `ad_active_status=ACTIVE`, `limit=50`. Lưu mỗi kết quả thành `research/_discover/<từ-khoá>.json`.
- **Scraper:** `node adlib_scrape.cjs "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=<CC>&q=<từ khoá>&search_type=keyword_unordered&media_type=all" research/_discover/<kw>.json --max 200`, rồi `adlib_parse.py` file `.graphql.jsonl`.
- **API chính thức** (thị trường EU/UK): `adlib_api.py --search "<từ khoá>" --countries DE -o …`.
- **Apify:** `apify_fetch.py fb-ads "<URL Ad Library có q=…>"`.

## 3. Xếp hạng

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/discover.py" -i research/_discover/*.json --country <CC> \
  [--exclude-domains brand-lon.com] --out-md research/_discover/competitors.md --out-json research/_discover/competitors.json
```
Điểm ưu tiên page có nhiều ad active, có ad sống >30 ngày, vẫn ra ad mới, và chạy Instagram. Sàn (Amazon, Temu, Shopee…) bị loại tự động.

## 4. Chọn đối thủ để spy

- Lấy 3–5 page đầu bảng, **mở link Ad Library** kiểm tra nhanh: có đúng sản phẩm không, có phải dropship/DTC giống mô hình của mình không.
- Page bán cùng sản phẩm nhưng khác angle: rất giá trị cho bước test angle.
- Chạy `/angle-lab:spy` với link Ad Library của page đã chọn.

---
name: discover
description: Tự tìm đối thủ từ từ khoá ngách trên Meta Ad Library, xếp hạng page đang chạy ads (ad active, ad sống lâu, ad mới, % IG), loại sàn TMĐT. Dùng khi "tìm đối thủ", "ai đang bán sản phẩm này", "chưa có link đối thủ".
argument-hint: "<từ khoá…> [quốc gia]"
---

# /angle-lab:discover

1. 5–10 từ khoá theo cách khách và quảng cáo thật sự viết: tên sản phẩm generic, nỗi đau, lợi ích, tiếng bản địa. Hỏi thị trường.
2. Mỗi từ khoá lấy ad → `research/_discover/<kw>.json`: MCP `ads_library_search(search_terms, countries, ACTIVE, limit=50)` · hoặc scraper URL `…/ads/library/?active_status=active&country=<CC>&q=<kw>&search_type=keyword_unordered` → `adlib_parse.py` · hoặc `adlib_api.py --search` (EU/UK) · hoặc `apify_fetch.py fb-ads`.
3. Xếp hạng:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/discover.py" -i research/_discover/*.json --country <CC> --out-md research/_discover/competitors.md
```
4. Mở link Ad Library của 3–5 page đầu, kiểm tra đúng sản phẩm và mô hình giống mình, rồi `/angle-lab:spy <link>`. Page cùng sản phẩm nhưng khác angle rất có giá trị cho bước test.

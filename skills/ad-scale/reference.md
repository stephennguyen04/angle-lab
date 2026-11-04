# Nguồn dữ liệu Ad Library (chỉ mở khi cần)

**A. HAR:** mở Ad Library của page (`view_all_page_id=<ID>`, quốc gia = thị trường chính; thêm `&publisher_platforms[0]=instagram` nếu chỉ muốn IG) → DevTools → Network → cuộn hết, bấm "See ad details" ở ad sống lâu (để có EU reach) → chuột phải → Save all as HAR.

**B. MCP:** `ads_library_search(page_ids=[ID], countries=[CC], ad_active_status=ALL, limit=50)`; gọi thêm `ACTIVE` để ghi estimated result count. Lưu JSON → `adlib_parse.py`.

**C. Scraper:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_scrape.cjs" "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=<CC>&view_all_page_id=<ID>&media_type=all" research/<slug>/01-scale/scrape.json --max 300 [--platform instagram] [--details 30]
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_parse.py" -i research/<slug>/01-scale/scrape.graphql.jsonl -o research/<slug>/01-scale/ads_raw.json
```
Gặp login wall/captcha: `--headful` trên máy người dùng, hoặc dùng cách A.

**D. Export:** Apify (`apify_fetch.py fb-ads <URL>`), Foreplay, Minea, PiPiAds… JSON có `ad_archive_id` → `adlib_parse.py`; CSV → đưa thẳng `ad_cadence.py` (tự nhận cột EN/VN, dấu `,` hoặc `;`).

**API chính thức (EU/UK):** `/angle-lab:audience`.

TikTok: ghi chú riêng (Creative Center Top Ads / TikTok Shop) và giới hạn dữ liệu.

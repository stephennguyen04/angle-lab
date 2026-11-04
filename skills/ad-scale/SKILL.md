---
name: ad-scale
description: Đo đối thủ đang scale tới đâu trên Meta Ad Library, gồm số ad active, tốc độ ra ad mới theo tuần (đều hay theo đợt hay ngưng), tuổi ad, ad nhân bản nhiều nhất, landing page trỏ về đâu, và chọn ra 5 video top (winner) để mổ. Dùng khi hỏi "họ chạy bao nhiêu ad", "scale tới đâu", "ra ad mới đều không", "ad nào là winner", "Ad Library của page này".
argument-hint: "<Page ID | tên brand | link Ad Library> [country]"
---

# /angle-lab:ad-scale: Đối thủ đang scale tới đâu?

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/` (nếu trống, xem cách tìm trong `/angle-lab:spy`). Lưu kết quả vào `research/<slug>/01-scale/`.

## 1. Thu thập ad (chọn nguồn theo thứ tự ưu tiên)

**A. MCP Meta Ads (`ads_library_search`)**, nếu có connector META_ADS:
- Gọi với `page_ids=[<PAGE_ID>]` (ưu tiên) hoặc `search_terms=<brand/sản phẩm>`, `countries=[<CC>]`, `ad_active_status=ALL`, `limit=50`.
- Gọi thêm 1 lần `ad_active_status=ACTIVE` để biết **tổng số ad active ước tính** (ghi lại con số "estimated result count").
- Lưu các ad trả về thành `01-scale/ads_raw.json` (list, mỗi ad giữ: id, start date, stop date, active, body, snapshot url, link url, media). Tool này giới hạn 50 ad/lần, đủ để đo nhịp gần đây. Tổng số ad active lấy từ estimated count.

**B. Scraper Playwright** (khi không có MCP, hoặc cần quét sâu hơn):
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_scrape.cjs" "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=<CC>&view_all_page_id=<PAGE_ID>&media_type=all" research/<slug>/01-scale/ads_raw.json --max 300
```
Gặp login wall/captcha thì bảo người dùng chạy lại với `--headful` trên máy họ.

**C. Người dùng tự export / dán** (từ công cụ spy như Foreplay, Minea, PiPiAds…): nhận CSV/JSON bất kỳ. `ad_cadence.py` tự nhận tên cột phổ biến.

Ngoài Meta: nếu họ chạy TikTok, ghi chú thêm (TikTok Creative Center Top Ads / TikTok Shop), vì không phải nơi nào cũng có thư viện đầy đủ, nên ghi rõ giới hạn dữ liệu.

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
- **Winner thật:** ad active >30 ngày, nhất là ad có nhiều bản nhân ("N ads use this creative"), là ad đang ra tiền.
- **Landing:** % ad về PDP vs advertorial/listicle → chuyển thông tin cho mảng funnel.
- **Nhiều page / nhiều store?** Nếu cùng creative xuất hiện ở page khác, ghi lại (đối thủ chạy đa page để scale).
- Kết luận 3 dòng: *đang scale tới đâu · tốc độ ra ad · ý nghĩa với mình (thị trường còn chỗ không)*.

Cuối file liệt kê **5 video top** (id, link video/snapshot, số ngày chạy, số bản nhân, lý do chọn), đây là input cho `/angle-lab:top-videos`. Ưu tiên ad active lâu nhất + nhân bản nhiều nhất; đa dạng angle nếu top bị trùng cùng 1 video.

> Ngưỡng "10/50/200 ad active" trong script là heuristic tham khảo, phải so với ngách: ngách nhỏ 30 ad active đã là mạnh.

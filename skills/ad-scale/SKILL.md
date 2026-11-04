---
name: ad-scale
description: Đo đối thủ scale tới đâu trên Meta Ad Library (ad active, nhịp ra ad mới, hạng ad sống lâu, % Instagram, EU reach, ad hợp tác creator, landing) và chọn 5 video top. Dùng khi "chạy bao nhiêu ad", "scale tới đâu", "ra ad mới đều không".
argument-hint: "<Page ID | brand | link Ad Library> [country]"
---

# /angle-lab:ad-scale

Script `${CLAUDE_PLUGIN_ROOT}/scripts/`; lưu vào `research/<slug>/01-scale/`. Không Read file HAR/JSON thô: để script đọc.

## 1. Lấy ad → `ads_raw.json` (mọi nguồn đều đi qua `adlib_parse.py`)
Thứ tự ưu tiên: **HAR** (người dùng tự lưu khi lướt Ad Library, ít rủi ro nhất) · **MCP `ads_library_search`** (page_ids, countries, ALL + 1 lần ACTIVE để lấy estimated count; tối đa 50 ad) · **scraper** `adlib_scrape.cjs` (bắt GraphQL) · **export Apify/tool spy**. Cách làm từng nguồn: `reference.md`.
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_parse.py" -i <file.har | scrape.graphql.jsonl | export.json> -o research/<slug>/01-scale/ads_raw.json
```
EU reach chỉ có với ad phân phối ở EU/UK/Brazil.

## 2. Tính
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ad_cadence.py" -i research/<slug>/01-scale/ads_raw.json --brand-domain <domain> --top 5 \
  --out-md research/<slug>/01-scale/scale_auto.md --out-json research/<slug>/01-scale/scale.json
```

## 3. Diễn giải → `scale.md` (ngắn, không chép lại bảng)
- **Giai đoạn:** đang test · đang lên · đỉnh · đi xuống.
- **Nhịp ra ad:** đều = team creative mạnh · theo đợt · ngưng = vắt winner hoặc bỏ sản phẩm.
- **Winner:** Long-Runner (≥60 ngày) / Performer (30–59 ngày), nhiều bản nhân, EU reach cao, ad hợp tác creator.
- **% Instagram** cao → ưu tiên mổ Reels. Cùng creative chạy trên nhiều page = scale mạnh.
- % landing PDP vs advertorial → chuyển cho bước funnel.
- Cuối file: **5 video top** (id, link, số ngày, bản nhân, lý do chọn). Đa dạng angle nếu top bị trùng.

Ngưỡng 10/50/200 ad active chỉ là heuristic, phải so với ngách.

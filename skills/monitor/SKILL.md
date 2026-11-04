---
name: monitor
description: Theo dõi đối thủ hằng ngày: ad mới, ad vượt 30/60 ngày, tăng bản nhân, EU reach tăng, ad tắt, đổi giá/bundle/variant/app; lên lịch tự động. Dùng khi "theo dõi đối thủ", "báo khi ra ad mới", "đối thủ đổi giá chưa".
argument-hint: "<research/<slug>>"
---

# /angle-lab:monitor

1. Lấy dữ liệu mới **cùng nguồn, cùng bộ lọc** như lần trước: ad → `adlib_parse.py` → `01-scale/ads_raw.json`; PDP → `shopify_product.py "<PDP>" --out 02-funnel/product.json`.
2. Snapshot + so:
```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"; R=research/<slug>
python3 "$S/monitor.py" snapshot --dir $R/monitor --ads $R/01-scale/ads_raw.json --product $R/02-funnel/product.json
python3 "$S/monitor.py" diff --dir $R/monitor --out $R/monitor/latest.md
```
3. Báo ngắn theo mức quan trọng: 🏆 ad vừa vượt 30/60 ngày và 📈 tăng bản nhân (angle đang ra tiền → mổ ngay, thêm vào thư viện hook) · 🆕 nhiều ad mới cùng angle (đang test lứa mới) · 💲 đổi giá/bundle (tối ưu AOV) · ⛔ tắt hàng loạt (bỏ sản phẩm hoặc bị khoá).

**Lịch:** `/loop 24h /angle-lab:monitor research/<slug>`, hoặc tạo routine hằng ngày khi người dùng muốn. Nhiều đối thủ: lặp qua `research/*`.

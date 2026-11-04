---
name: monitor
description: Theo dõi đối thủ hằng ngày hoặc hằng tuần, báo khi có ad mới, ad vừa vượt mốc 30/60 ngày (đang có lãi), ad tăng bản nhân mạnh (đang scale), tiếp cận EU tăng, ad bị tắt, và trang sản phẩm đổi giá/bundle/variant/app. Có hướng dẫn lên lịch chạy tự động. Dùng khi nói "theo dõi đối thủ", "báo khi đối thủ ra ad mới", "monitor", "check hằng ngày", "đối thủ đổi giá chưa".
argument-hint: "<research/<slug>> [setup | run]"
---

# /angle-lab:monitor: Theo dõi đối thủ theo thời gian

## Mỗi lần chạy (1 sản phẩm)

1. Lấy dữ liệu mới nhất, cùng cách và cùng bộ lọc với lần trước (cùng Page ID, quốc gia, placement):
   - Ad: theo `/angle-lab:ad-scale` → `adlib_parse.py` → `research/<slug>/01-scale/ads_raw.json`
   - Trang sản phẩm: `shopify_product.py "<PDP>" --out research/<slug>/02-funnel/product.json`
2. Chụp snapshot và so với lần trước:
   ```bash
   S="${CLAUDE_PLUGIN_ROOT}/scripts"
   python3 "$S/monitor.py" snapshot --dir research/<slug>/monitor --ads research/<slug>/01-scale/ads_raw.json --product research/<slug>/02-funnel/product.json
   python3 "$S/monitor.py" diff --dir research/<slug>/monitor --out research/<slug>/monitor/latest.md
   ```
3. Báo người dùng ngắn gọn, ưu tiên theo mức quan trọng:
   - 🏆 **Ad vừa vượt 30/60 ngày** và 📈 **ad tăng bản nhân mạnh:** angle đang ra tiền của đối thủ. Mổ ngay (`/angle-lab:top-videos`), thêm vào thư viện hook.
   - 🆕 **Nhiều ad mới cùng một angle:** đối thủ đang test lứa angle mới.
   - 💲 **Đổi giá, bundle, thêm variant, bật app bundle:** họ đang tối ưu AOV; cân nhắc offer của mình.
   - ⛔ **Tắt hàng loạt ad:** có thể đang bỏ sản phẩm hoặc bị khoá tài khoản.

## Lên lịch tự động

- Trong phiên Claude Code: `/loop 24h /angle-lab:monitor research/<slug>`.
- Chạy định kỳ không cần mở máy: tạo một routine (scheduled task) chạy hằng ngày với prompt "chạy /angle-lab:monitor cho research/<slug> và báo thay đổi". Khi người dùng muốn, Claude tạo routine này bằng tool lập lịch có trong phiên.
- Nhiều đối thủ: lặp qua từng thư mục trong `research/`.

Lưu ý: số liệu chỉ so được khi cách lấy giữ nguyên giữa các lần (cùng bộ lọc, cùng nguồn). Đổi nguồn thì ghi chú vào `monitor/latest.md`.

---
name: spy
description: Spy toàn diện 1 sản phẩm đối thủ (scale ads, funnel/bundle, 5 video top, bình luận đa nền tảng) → REPORT.md + verdict LÀM/BỎ. Dùng khi "spy sản phẩm", "phân tích đối thủ", dán link shop/sản phẩm/Ad Library.
argument-hint: "<link sản phẩm | shop | Ad Library | brand>"
---

# /angle-lab:spy

Mục tiêu: **có nên làm sản phẩm này không, đánh angle nào, làm tốt hơn đối thủ ở đâu**, bằng bằng chứng.

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/` (luôn ghi đường dẫn đầy đủ; mỗi lệnh Bash là shell mới). Chưa có link đối thủ thì chạy `/angle-lab:discover` trước.

**Tiết kiệm token (áp dụng cho mọi bước):** đọc output tóm tắt của script và các file `*_summary.md`, `hook_sheet.jpg`, `scenes_sheet.jpg`, `report.md`. Không `cat`/Read file JSON, HAR, `.txt` lớn. Chỉ mở khung hình lẻ hoặc ảnh toàn trang khi cần kiểm tra một chi tiết.

## 1. Hồ sơ
Xác định link PDP, domain, Page ID (`view_all_page_id=`), thị trường (ISO-2). Thiếu gì không tự tìm được thì hỏi. Workspace `research/<slug>/` gồm `00-input.md 01-scale/ 02-funnel/ 03-videos/ 04-comments/ creative/`. Đã có workspace thì chỉ làm phần còn thiếu.

## 2. Phân tích (song song)
Gửi 3 agent trong 1 message, mỗi agent nhận hồ sơ + đường dẫn workspace:
- `angle-lab:ad-scale-analyst` → `01-scale/scale.md` + 5 video top
- `angle-lab:funnel-analyst` → `02-funnel/funnel.md`
- `angle-lab:comment-miner` → `04-comments/insights.md` (**phần quan trọng nhất**: đọc mọi bình luận trên mọi nền tảng)

Sau khi có 5 video top: 5 agent `angle-lab:video-angle-analyst` song song → `03-videos/videos.md`. Rồi chạy `/angle-lab:scoreboard` (Meta Ads + Instagram → Top ad, Top bài, A1–A5). Không có Agent tool thì làm tuần tự theo từng skill.

## 3. REPORT.md
Viết theo `${CLAUDE_PLUGIN_ROOT}/templates/spy-report.md`: verdict + 3 lý do · scale · funnel/offer · 5 angle (angle nhân bản nhiều nhất = đã được thị trường xác nhận) · tiếng nói khách hàng (rủi ro 🔴🟡🟢) · rủi ro · làm tốt hơn ở đâu · bảng mạnh nhất Meta/IG · A1–A5. Mỗi số liệu ghi file nguồn; thiếu dữ liệu thì ghi "chưa có + cách lấy".

## 4. Kết thúc
- Đối thủ bán ở EU/UK → `/angle-lab:audience` (persona thực tế).
- `hooks_library.py harvest --root research --niche "<ngách>"`.
- Gợi ý bật `/angle-lab:monitor`.
- Trả lời: verdict, 5 phát hiện chính, đường dẫn REPORT.md, bước tiếp `/angle-lab:angle-test research/<slug>`.

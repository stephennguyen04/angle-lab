---
name: top-videos
description: Mổ 5 video ad top của đối thủ: angle, nỗi đau, persona, hook 0–3s (hình + chữ có dấu + lời), beat, proof, format; so sánh để tìm angle được nhân bản nhiều nhất. Dùng khi "phân tích video đối thủ", "hook 3s đầu", "họ đánh vào nỗi đau gì".
argument-hint: "<research/<slug> | link video…>"
---

# /angle-lab:top-videos

**ANGLE** = ai + nỗi đau/mong muốn + cơ chế (lý do mua). **HOOK** = cách mở 0–3s đưa angle vào mắt. **FORMAT** = cách quay. Hai video khác hook/format vẫn có thể cùng 1 angle. Luôn tách 3 lớp này.

## 1. Chuẩn bị mỗi video
Nguồn video: Top ad / Top bài trong `01-scale/scoreboard.md`, hoặc `scale.md`, hoặc link người dùng đưa.
```bash
ASR_LANG=vi bash "${CLAUDE_PLUGIN_ROOT}/scripts/video_prep.sh" "<video|url>" research/<slug>/03-videos/v1
```
**Đọc theo thứ tự (tiết kiệm token):** `ocr.txt` (chữ trên màn hình có dấu) · `transcript.txt` (lời) · `hook_sheet.jpg` (12 khung 0–3s có ghi thời gian, 1 ảnh) · `scenes_sheet.jpg` (các cảnh, 1 ảnh). Chỉ mở khung lẻ trong `hook/`, `scenes/` để soi chi tiết hoặc kiểm tra dòng chữ nhỏ bị mất dấu. Thiếu OCR/transcript thì đọc từ ảnh lưới và ghi rõ.

## 2. `vN/analysis.md` (gọn)
Angle 1 câu · persona · nỗi đau bề mặt → sâu · kết quả hứa hẹn · kẻ thù/cách cũ · cơ chế · proof · objection · offer/CTA.
Hook 0–3s: bảng `t | hình | chữ | lời`, kiểu hook (callout nỗi đau, kết quả trước, hình lạ, "đừng làm X", tò mò, POV, social proof, demo, authority, us vs them, câu hỏi), vì sao giữ chân, điểm /10.
Beat theo timestamp · format · nhịp (cuts/10s, từ/giây) · ad copy có khớp angle không.

## 3. `videos.md`
Bảng: video · angle · nỗi đau · kiểu hook · format · ngày chạy · bản nhân · điểm hook. Gom angle trùng (angle nhiều video + nhiều bản nhân = đã được xác nhận). Pattern hook lặp lại. Khoảng trống (nỗi đau khách nhắc trong bình luận mà chưa ai làm). Kết luận 5 angle đề xuất test.

## 4. Thư viện hook
Mỗi video 1 dòng vào `03-videos/hooks.jsonl`: `{"text","type","angle","pain","platform","visual","ad_id","days_running","duplicates","eu_reach","views"}` (text = chữ + lời 0–3s nguyên văn có dấu) → `hooks_library.py harvest --root research --niche "<ngách>"`.

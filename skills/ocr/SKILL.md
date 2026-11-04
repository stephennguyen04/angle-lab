---
name: ocr
description: Đọc chữ trên màn hình video/ảnh ad (text overlay hook, caption, sticker giá), tiếng Việt có dấu, có timeline. Dùng khi "đọc chữ trong video", "OCR", "text overlay", "caption ghi gì".
argument-hint: "<video | ảnh…> [out_dir]"
---

# /angle-lab:ocr

Nhiều ad (nhất là Reels/TikTok) đặt hook bằng chữ chứ không bằng lời.

Cài: tesseract + gói tiếng Việt (`brew install tesseract tesseract-lang` · `sudo apt install tesseract-ocr tesseract-ocr-vie` · Windows: bộ cài UB-Mannheim, tick Vietnamese) hoặc `pip install easyocr`.
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ocr_frames.py" --video <video> --out-dir <thư mục video>     # hoặc --images a.png b.jpg
```
`video_prep.sh` tự gọi bước này nếu máy có engine. Output: `ocr.txt` (đọc file này) và `ocr.json` (`hook_text`, `first_text_at`, `timeline`). Tuỳ chọn `--fps 2 --hook-fps 4 --engine easyocr`.

**Kiểm tra:** chữ nhỏ (dưới khoảng 20px) hay mất dấu; chữ cách điệu hoặc karaoke từng từ dễ đọc thiếu. Với dòng quan trọng, mở `hook_sheet.jpg` hoặc khung lẻ để tự đọc lại.

**Dùng trong phân tích:** chữ 0–3s = phần chữ của hook (so với lời nói: trùng, bổ sung hay mâu thuẫn?) · `first_text_at` > 0,5s là chậm · offer xuất hiện ở giây nào · cụm từ đối thủ dùng → thư viện hook.

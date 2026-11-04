---
name: ocr
description: Đọc chữ trên màn hình của video và ảnh ad (text overlay ở hook, caption, sticker giá, badge "Giảm 50%", chữ trên bao bì, screenshot landing page), hỗ trợ tiếng Việt CÓ DẤU, kèm timeline giây nào hiện chữ gì. Dùng khi cần biết hook 3s đầu ghi chữ gì, video không có lời thoại, phân tích caption/overlay của đối thủ, hoặc nói "đọc chữ trong video", "OCR", "chữ trên màn hình", "text overlay", "caption ghi gì".
argument-hint: "<video | ảnh…> [out_dir]"
---

# /angle-lab:ocr: Đọc chữ trên màn hình (tiếng Việt có dấu)

Rất nhiều ad (nhất là Reels/TikTok) **đặt hook bằng chữ**, không bằng lời. Không đọc chữ thì mổ hook sai.

## Cài một lần

| Engine | Cài | Ghi chú |
|---|---|---|
| **tesseract + tiếng Việt** (mặc định) | macOS: `brew install tesseract tesseract-lang` · Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-vie` · Windows: bộ cài UB-Mannheim, tick "Vietnamese" | Nhanh, chính xác với caption chữ trắng viền đen |
| **easyocr** (dự phòng) | `pip install easyocr` | Tốt hơn với chữ cách điệu/nghiêng, nhưng nặng và chậm |

## Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ocr_frames.py" --video <video.mp4> --out-dir <thư mục video>   # timeline cả video
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ocr_frames.py" --images a.png b.jpg --out-dir <out>            # ảnh / screenshot
```
`video_prep.sh` tự gọi bước này nếu máy có engine. Tuỳ chọn: `--fps 2` (thân video), `--hook-fps 4` (3 giây đầu), `--lang vie+eng`, `--engine easyocr`.

Cách script làm: mỗi khung được xử lý 3 kiểu (tách chữ sáng thành chữ đen nền trắng, xám tăng tương phản, đảo màu), chọn bản đọc tin cậy nhất. Sau đó theo dõi **từng dòng chữ** qua các khung: dòng cố định như "Freeship toàn quốc" không làm rối dòng hook đổi liên tục. Mỗi dòng giữ bản đọc khớp nhất giữa các khung, để khử lỗi OCR lẻ tẻ.

Output: `ocr.json` (`hook_0_3s`, `hook_text`, `first_text_at`, `timeline[{start,end,text,conf,frames}]`) và `ocr.txt`.

## Kiểm tra lại (bắt buộc)

- **Chữ nhỏ** (dưới ~20px, như footer, điều khoản) hay **mất dấu** ("Doi tra" thay vì "Đổi trả"). Với dòng quan trọng, Read khung hình gốc trong `hook/` hoặc `scenes/` để tự đọc lại.
- Chữ cách điệu, viết tay, chữ chạy karaoke từng từ: OCR dễ đọc thiếu. Đối chiếu với khung hình và transcript.
- Ghi rõ trong phân tích dòng nào đã được kiểm tra bằng mắt.

## Dùng kết quả trong phân tích

- **Hook bằng chữ:** câu chữ xuất hiện trong 0–3s là phần chữ của hook. So với lời nói (`transcript.json`): trùng nhau, bổ sung cho nhau, hay mâu thuẫn?
- **Thời điểm chữ đầu tiên** (`first_text_at`): xuất hiện sau 0,5s là chậm, dễ mất người lướt.
- **Offer trên màn hình:** giảm giá, freeship, bảo hành xuất hiện ở giây nào. So với angle (offer xuất hiện quá sớm thường làm loãng angle).
- **Ngôn ngữ đối thủ dùng:** gom vào phần "đạn" cho hook/copy, và vào thư viện hook (`/angle-lab:hooks`).

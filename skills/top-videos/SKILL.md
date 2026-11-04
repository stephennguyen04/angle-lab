---
name: top-videos
description: Lấy 5 video ad top của đối thủ và mổ angle cho từng video, gồm họ đánh vào nỗi đau gì, persona nào, hook 3 giây đầu ra sao (hình, chữ, câu nói đầu, kiểu hook), cấu trúc beat theo timestamp, bằng chứng, CTA, format, nhịp cắt. Sau đó so sánh 5 video để thấy angle nào được nhân bản nhiều nhất. Dùng khi nói "phân tích 5 video top", "mổ video đối thủ", "angle gì", "hook 3s đầu", "họ đánh vào nỗi đau gì".
argument-hint: "<research/<slug> | danh sách link video>"
---

# /angle-lab:top-videos: Mổ 5 video top

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/`. Lưu vào `research/<slug>/03-videos/`.

## Định nghĩa phải giữ nhất quán (dùng cho cả quy trình test → nhân bản)

- **ANGLE** = *Ai* + *nỗi đau/mong muốn cụ thể* + *niềm tin/cơ chế vì sao sản phẩm giải quyết được* → lý do mua. Ví dụ: "Dân văn phòng đau lưng vì ngồi 8 tiếng; ghế không sai, tư thế sai; miếng X sửa tư thế thụ động nên đỡ đau mà không cần tập."
- **HOOK** = cách mở 0–3s để *đưa angle vào mắt người xem*. Một angle có thể có nhiều hook.
- **FORMAT** = cách thực thi (UGC nói thẳng camera, demo, skit, green screen, voiceover + b-roll, before/after, phỏng vấn đường phố…).

Hai video khác hook, khác format vẫn có thể **cùng 1 angle**. Phân tích phải tách 3 lớp này.

## 1. Chuẩn bị từng video

Lấy 5 video từ **Top ad / Top bài Instagram** trong `01-scale/scoreboard.md` nếu đã có, không thì từ `01-scale/scale.md` (hoặc link người dùng đưa). Reel IG: `ig_collect.py` ghi sẵn `video_url`; link reel cũng đưa thẳng cho `video_prep.sh` được (yt-dlp, có thể cần `--cookies-from-browser`). Với mỗi video `vN`:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/video_prep.sh" "<video_url hoặc file>" research/<slug>/03-videos/v1
```
→ `hook/hook_01..12.jpg` (4 fps trong 3s đầu), `scenes/*.jpg` + `scenes.txt` (timestamp đổi cảnh), `transcript.txt` (nếu có whisper), `meta.json` (thời lượng, nhịp cắt).

- **Xem thật** các khung hook (Read từng ảnh) và keyframe cảnh. Đừng phân tích chỉ từ transcript.
- Nếu có skill `video-watcher` thì dùng nó để phân tích sâu hơn; có MCP Higgsfield `video_analysis_create` cũng dùng được.
- Không có transcript thì đọc chữ trên màn hình từ khung hình + ad copy, và ghi rõ "không có audio transcript".
- Link snapshot Ad Library không tải được thì nhờ người dùng tải mp4 (nút download trên Ad Library) hoặc gửi link TikTok/IG gốc.

## 2. Phân tích mỗi video → `03-videos/vN/analysis.md`

```
## vN: <id> · <thời lượng>s · chạy <x> ngày · <y> bản nhân
**Angle (1 câu):** …
- Persona: …
- Nỗi đau bề mặt → nỗi đau sâu (cảm xúc): … → …
- Mong muốn / kết quả hứa hẹn: …
- Kẻ thù / cách cũ thất bại: …
- Cơ chế (vì sao SP này khác): …
- Bằng chứng: demo / before-after / review / chuyên gia / số liệu / UGC
- Objection được xử lý: …
- Offer & CTA: …

**HOOK 0–3s**
| t | Hình | Chữ trên màn hình | Lời nói / âm thanh |
|---|---|---|---|
| 0.0 | … | … | … |
- Kiểu hook: (callout nỗi đau · kết quả trước · hình gây sốc/lạ · "đừng làm X" · curiosity gap · POV/relatable · social proof · demo ngay · authority · us vs them · câu hỏi)
- Vì sao giữ chân được: pattern interrupt gì, ai thấy mình trong đó
- Điểm hook 1–10 + lý do

**Cấu trúc beat** (timestamp): Hook → Problem → Agitate → Mechanism → Demo/Proof → Offer → CTA …
**Format:** … · **Nhịp:** <cuts/10s> · **Caption style:** … · **Nhạc/voice:** …
**Ad copy (primary text/headline)** khớp angle không: …
```

## 3. So sánh 5 video → `03-videos/videos.md`

- Bảng tổng: video · angle · nỗi đau · kiểu hook · format · số ngày chạy · số bản nhân · điểm hook.
- **Gom nhóm angle**: video nào cùng angle? Angle được nhiều video + nhiều bản nhân nhất là **angle đã được thị trường xác nhận**.
- **Pattern hook** lặp lại (ví dụ 3/5 mở bằng "kết quả trước").
- **Khoảng trống**: nỗi đau nào khách nhắc nhiều trong bình luận nhưng đối thủ chưa khai thác (đối chiếu `04-comments` nếu có). Đây là angle tiềm năng riêng của mình.
- Kết: **5 angle đề xuất đưa vào test** (mặc định 1 angle / 1 video top; thay video trùng angle bằng angle "khoảng trống").

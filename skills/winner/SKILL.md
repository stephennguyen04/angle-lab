---
name: winner
description: Giai đoạn 2: đọc kết quả test (export Ads Manager), tìm video/angle ra sale, mổ video thắng → ANGLE KIM CHỈ NAM (bất biến vs biến được đổi) + angle.json cho nhân bản. Dùng khi "video nào ra sale", "đọc kết quả test", "mổ video thắng".
argument-hint: "<research/<slug>> <export.csv>"
---

# /angle-lab:winner

Output: `creative/02-readout.md`, `03-north-star.md`, `angle.json`.

## 1. Đọc số
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/test_readout.py" -i <export.csv> --price <giá> --cogs <giá vốn> --shipping <ship> --fees-pct 5 \
  --scoreboard research/<slug>/01-scale/scoreboard.json --out-md research/<slug>/creative/02-readout.md --out-json research/<slug>/creative/readout.json
```
(`--breakeven-cpa` thay cho giá/giá vốn; tên ad lệch quy ước thì thêm `--angle-regex`.) Output in bảng angle + kết luận; bảng "Dự đoán MXH vs thực tế" nằm trong file.
- Diễn giải: angle thắng nhờ đâu (hook rate / CTR / CVR), angle thua chết ở bước nào. Angle điểm MXH cao mà mình thua thường do **thực thi**, chưa chắc angle sai. Angle thắng ngoài dự đoán là quý nhất.
- **Chưa có WINNER:** TIỀM NĂNG thì chạy thêm 1–2 ngày; tất cả KILL thì xem lại offer/LP hoặc test lứa angle mới. Dừng ở đây.
- Nhiều WINNER: chọn angle CPA thấp nhất + nhiều đơn nhất; còn lại để dành, không trộn.

## 2. Mổ video thắng
```bash
ASR_LANG=vi bash "${CLAUDE_PLUGIN_ROOT}/scripts/video_prep.sh" <video thắng> research/<slug>/creative/winner_video
```
Đọc `ocr.txt`, `transcript.txt`, `hook_sheet.jpg`, `scenes_sheet.jpg`. So với video gốc đối thủ và với video thua: chỉ thứ **có ở video thắng mà video thua không có** mới là yếu tố quyết định. Đối chiếu bình luận dưới ad thắng nếu có.

## 3. `03-north-star.md` (theo `${CLAUDE_PLUGIN_ROOT}/templates/north-star.md`)
- **Angle 1 câu:** *[Persona] đang [nỗi đau] vì [nguyên nhân họ chưa biết]; [sản phẩm] [cơ chế] nên [kết quả], [bằng chứng].*
- **Bất biến:** persona + tình huống · nỗi đau sâu · cơ chế · lời hứa (kết quả + thời gian) · loại proof · thứ tự beat · objection bắt buộc xử lý.
- **Được đổi:** nhân vật · bối cảnh · hook (phải gọi đúng nỗi đau/lời hứa) · giọng, nhạc, nhịp, bản 15/30/45s.
- Cơ chế hook đã thắng (t / hình / chữ / lời, và vì sao hiệu quả) · 🚩 dấu hiệu lạc angle.

## 4. `angle.json` (cho `/angle-lab:clone`)
`{angle_id, angle_name, angle_statement, invariants[], drift_red_flags[], control{hook,character,setting}, hooks[{id,type,text}], characters[{id,desc}], settings[{id,desc}]}`
- H0/C0/S0 = đúng của video thắng. Thêm **10 hook** (đủ kiểu, bám nỗi đau/lời hứa, dùng ngôn ngữ khách và khung từ `hooks_library.py search --q "<nỗi đau>" --status proven`), **5 nhân vật** (C0 theo persona lớn nhất trong `audience.md` nếu có), **5 bối cảnh**.

## 5. Lưu kết quả
Hook thắng của mình: `hooks_library.py add --text "…" --source own …` (hoặc `results` sau vòng nhân bản). Ghi `creative/log.md`. Bước tiếp: `/angle-lab:clone research/<slug>`.

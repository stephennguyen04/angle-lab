---
name: clone
description: Giai đoạn 3 "NHÂN BẢN SAU": nhân bản video thắng bằng AI (đổi nhân vật, bối cảnh, hook) nhưng bám ĐÚNG 1 angle kim chỉ nam; ma trận biến thể theo vòng, script + prompt AI, kiểm tra angle lock. Dùng khi "nhân bản video", "clone winner", "đổi nhân vật bối cảnh hook".
argument-hint: "<research/<slug>> [--round 1|2|3]"
---

# /angle-lab:clone

Bắt buộc có `creative/angle.json` + `03-north-star.md` (từ `/angle-lab:winner`). Chưa có angle thắng đã được số liệu xác nhận thì **không nhân bản**.

## Luật
- **1 angle duy nhất.** Mọi biến thể phải pass toàn bộ `invariants`. Ý tưởng hay nhưng khác angle thì ghi vào `creative/ideas-backlog.md`.
- **Mỗi lần chỉ đổi 1 biến so với control.** Vòng 1 HOOK → vòng 2 NHÂN VẬT → vòng 3 BỐI CẢNH. Biến thắng thành control vòng sau (cập nhật `control` trong angle.json).

## 1. Ma trận
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/variant_matrix.py" --angle research/<slug>/creative/angle.json --mode staged --round 1 --out research/<slug>/creative/04-variants.csv
```
Chế độ khác: `one-change`, `combo` (khi scale). Tên ad `<yymmdd>_<A#>_V<nn>_H#_C#_S#`.

## 2. Brief `creative/variants/<ad_name>.md`
Giữ beat + lời hứa + proof của video thắng; chỉ thay biến được đổi.
- **Hook:** 0–3s (hình + chữ + câu đầu gọi đúng nỗi đau/lời hứa). Khung từ `hooks_library.py search --q "<nỗi đau>" --status proven`.
- **Nhân vật:** ngoại hình, tuổi, vai, giọng; ưu tiên persona trong `01-scale/audience.md`. Thoại tự nhiên nhưng giữ ý.
- **Bối cảnh:** hợp tình huống nỗi đau.
- Script theo beat + timestamp (dựa trên `transcript.srt`, `ocr.json` của video thắng) · shot list · chữ trên màn hình · caption.
- Prompt AI từng cảnh (khoá ngoại hình nhân vật giữa các cảnh); cảnh sản phẩm dùng footage thật.
- Công cụ: MCP Higgsfield + `higgsfield-prompt-director` (báo giá credit trước khi tạo hàng loạt) · `ad-creative-writer` · `ffmpeg-video-edit` (cách rẻ nhất: giữ thân video, thay 3s đầu).

## 3. Angle lock (bắt buộc)
Bảng: biến thể · persona · nỗi đau · cơ chế · lời hứa · proof · beat · 🚩 · PASS/FAIL. Một ô trượt là sửa hoặc loại. Hook viral mà không dính nỗi đau = FAIL. Ghi lý do vào `creative/log.md`.

## 4. Launch & lặp
- Chạy trong ad set test creative riêng (cùng offer, LP, audience), control chạy song song.
- 3–4 ngày sau: `test_readout.py … --angle-regex "_(V\d+)_"` → biến thể thắng control vào campaign scale. Sau đó: `hooks_library.py results --readout … --variants creative/04-variants.csv …`.
- Creative mỏi (CPA tăng, CTR giảm, frequency >3) → vòng nhân bản mới, **vẫn cùng angle**. Chỉ khi nhiều vòng đều thua mới quay lại `/angle-lab:angle-test`.

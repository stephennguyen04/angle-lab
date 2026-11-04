---
name: clone
description: Giai đoạn 3 của "TEST ANGLE TRƯỚC, NHÂN BẢN SAU". Nhân bản video thắng bằng AI, đổi nhân vật, bối cảnh, hook mới nhưng bám ĐÚNG 1 angle kim chỉ nam, không lan man. Sinh ma trận biến thể theo vòng (hook → nhân vật → bối cảnh), viết script + shot list + prompt AI cho từng biến thể, chạy kiểm tra "angle lock" loại biến thể lạc angle. Dùng khi nói "nhân bản video", "clone winner", "làm thêm biến thể", "đổi nhân vật bối cảnh hook", "scale creative", "AI nhân bản".
argument-hint: "<research/<slug>> [--round 1|2|3] [--n 10]"
---

# /angle-lab:clone: NHÂN BẢN SAU (bám đúng 1 angle)

Input bắt buộc: `research/<slug>/creative/angle.json` + `03-north-star.md` (từ `/angle-lab:winner`). Chưa có thì dừng lại và bảo người dùng chạy `/angle-lab:winner`. **Không nhân bản khi chưa có angle thắng đã được số liệu xác nhận.**

Output: `creative/04-variants.csv`, `creative/variants/<ad_name>.md`, (tuỳ chọn) video sinh bằng AI.

## 1. Luật vàng

- **1 angle duy nhất.** Mọi biến thể đều phải pass toàn bộ `invariants` trong `angle.json`. Ý tưởng hay nhưng khác angle thì ghi vào `creative/ideas-backlog.md` cho lứa test angle sau, **không** đưa vào lứa nhân bản.
- **Mỗi lần chỉ đổi 1 biến so với control** (ở chế độ staged) để đọc số biết biến nào ăn.
- Thứ tự mặc định: **Vòng 1 HOOK** (rẻ nhất, ảnh hưởng mạnh nhất tới hook rate/CPM) → **Vòng 2 NHÂN VẬT** → **Vòng 3 BỐI CẢNH**. Biến thắng của vòng trước trở thành control vòng sau (cập nhật `control` trong angle.json).

## 2. Sinh ma trận biến thể

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/variant_matrix.py" --angle research/<slug>/creative/angle.json --mode staged --round 1 \
  --out research/<slug>/creative/04-variants.csv
```
Chế độ: `staged` (mặc định, theo vòng) · `one-change` (đổi 1 biến, gộp mọi vòng) · `combo` (ghép hook × nhân vật × bối cảnh thắng, dùng khi scale). Tên ad sinh ra theo dạng `<yymmdd>_<A#>_V<nn>_H#_C#_S#` → `test_readout.py` đọc lại được (`--angle-regex "_(V\d+)_"` để gom theo biến thể).

## 3. Viết brief từng biến thể → `creative/variants/<ad_name>.md`

Giữ nguyên **cấu trúc beat + lời hứa + proof** của video thắng; chỉ thay phần thuộc biến được đổi:
- **Hook mới:** viết lại 0–3s (hình mở + chữ + câu nói đầu). Câu đầu tiên phải gọi đúng nỗi đau hoặc lời hứa của angle. Lấy khung từ thư viện: `hooks_library.py search --q "<nỗi đau>" --status proven`.
- **Nhân vật mới:** mô tả ngoại hình, tuổi, vai, giọng; thoại chỉnh cho tự nhiên với nhân vật đó nhưng *ý* giữ nguyên. Ưu tiên persona thực tế trong `01-scale/audience.md`.
- **Phụ đề / chữ trên màn hình:** dựa trên `transcript.srt` và `ocr.json` của video thắng, chỉ thay câu thuộc biến được đổi.
- **Bối cảnh mới:** nơi chốn hợp với tình huống nỗi đau của persona.
- Script đầy đủ theo beat + timestamp · shot list · chữ trên màn hình · caption ad (dòng đầu khớp hook).
- **Prompt AI** cho từng cảnh: nhân vật (khoá ngoại hình nhất quán giữa các cảnh), bối cảnh, hành động, góc máy, ánh sáng, thời lượng; cảnh sản phẩm dùng footage thật của mình (AI hay sai chi tiết sản phẩm).

Công cụ AI (dùng cái nào có sẵn trong phiên):
- MCP **Higgsfield**: generate video/image, recast nhân vật từ footage thắng, đổi bối cảnh, UGC/ads studio. Gọi skill `higgsfield-prompt-director` nếu có để viết prompt chuẩn. Báo giá credit cho người dùng trước khi generate hàng loạt.
- Skill `ad-creative-writer` (nếu có) để viết thêm hook/copy trong khuôn angle.
- Skill `ffmpeg-video-edit` để ghép hook mới vào thân video thắng (cách nhân bản rẻ nhất: **giữ nguyên thân, chỉ thay 3s đầu**).

## 4. Kiểm tra ANGLE LOCK (bắt buộc trước khi giao)

Chấm từng biến thể theo checklist `invariants` (cột `angle_lock_checklist` trong CSV):
| Biến thể | Persona | Nỗi đau | Cơ chế | Lời hứa | Proof | Beat | 🚩 drift? | PASS/FAIL |
Bất kỳ ô nào FAIL thì sửa lại hoặc loại. Đặc biệt soi hook: hook "viral" mà không dính nỗi đau = FAIL. Ghi lý do FAIL vào `creative/log.md`.

## 5. Launch & vòng lặp

- Biến thể mới chạy trong **ad set/campaign test creative riêng**, cùng offer + LP + audience như lúc test angle; control (video thắng) chạy song song làm mốc.
- Sau 3–4 ngày: export → `test_readout.py ... --angle-regex "_(V\d+)_"` → biến thể nào thắng control thì đưa vào campaign scale; biến thắng thì thành control vòng tiếp.
- **Creative mỏi** (CPA tăng, CTR giảm, frequency >3 ở campaign scale) → chạy vòng nhân bản mới, **vẫn cùng angle**. Chỉ khi cả angle hết hiệu quả (nhiều vòng biến thể đều thua) mới quay lại `/angle-lab:angle-test` với angle mới từ `ideas-backlog.md`.
- Cập nhật `creative/log.md` sau mỗi vòng: vòng · biến thể · kết quả · control mới.
- Sau mỗi vòng: `hooks_library.py results --readout … --variants creative/04-variants.csv …` để hook thắng/thua của mình vào thư viện.

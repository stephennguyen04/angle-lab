---
name: hooks
description: Thư viện hook dùng chung cho mọi sản phẩm. Lưu hook đã được chứng minh (ad đối thủ sống lâu, nhiều bản nhân, tiếp cận cao; hoặc hook mình test thắng kèm hook rate/CPA thật), tìm lại theo từ khoá không dấu, ngách, kiểu hook, angle. Dùng khi nói "thư viện hook", "swipe file", "lưu hook", "hook nào đã thắng", "tìm hook cho sản phẩm mới", "hook đã chứng minh".
argument-hint: "<add | harvest | results | search | report> …"
---

# /angle-lab:hooks: Thư viện hook đã chứng minh

Mục tiêu: sản phẩm thứ 2, thứ 3 không bắt đầu từ số 0. Hook từng thắng (của đối thủ hoặc của mình) được lưu lại cùng **bằng chứng** và tìm lại được ngay.

File thư viện: `hooks-library/hooks.jsonl` ở thư mục gốc dự án (đổi bằng `--lib` hoặc biến `ANGLE_LAB_HOOKS`, ví dụ một thư mục dùng chung cho nhiều dự án). `hooks-library/README.md` là bản xem nhanh.

## Đưa hook vào

1. **Khi mổ video đối thủ** (`/angle-lab:top-videos`): với mỗi video, ghi 1 dòng vào `research/<slug>/03-videos/hooks.jsonl`:
   ```json
   {"text": "câu hook (chữ + lời, nguyên văn, có dấu)", "type": "callout nỗi đau", "angle": "…", "pain": "…", "platform": "instagram",
    "visual": "hình mở 0–1s", "ad_id": "…", "days_running": 119, "duplicates": 12, "eu_reach": 1850000, "views": 950000}
   ```
   Câu hook lấy từ `ocr.json` (`hook_text`) + `transcript.json` (`hook_0_3s`), không đoán.
2. **Gom vào thư viện:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py" harvest --root research --niche "<ngách>"
   ```
3. **Sau mỗi lần test của mình** (`/angle-lab:winner` hoặc vòng nhân bản), gắn kết quả thật vào hook:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py" results --readout research/<slug>/creative/readout.json \
     --variants research/<slug>/creative/04-variants.csv --product <slug> --niche "<ngách>" --angle "<angle>"
   ```
4. Thêm tay: `hooks_library.py add --text "…" --type "…" --angle "…" --niche "…" --days 95 --dupes 6`.

## Tìm lại

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py" search --q "dau lung" --status proven --top 15
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py" search --type "kết quả trước" --niche "sức khoẻ"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py" report
```
Tìm không cần gõ dấu. Xếp hạng theo điểm bằng chứng: hook **mình test WINNER** > hook đối thủ Long-Runner + nhiều bản nhân + tiếp cận cao > hook đã test nhưng thua > ý tưởng.

## Dùng thư viện đúng cách

- Khi viết hook mới cho `/angle-lab:clone` hoặc `/angle-lab:angle-test`: lấy **cấu trúc / kiểu hook** đã thắng, rồi viết lại cho đúng nỗi đau và lời hứa của angle hiện tại. Không bê nguyên câu của đối thủ.
- Hook thắng ở ngách khác vẫn dùng được **khung**, nhưng phải chạy test lại, không coi là đã chứng minh cho sản phẩm mới.
- Hook bị KILL vẫn giữ trong thư viện, để lần sau tránh lặp lại.

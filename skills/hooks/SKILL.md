---
name: hooks
description: Thư viện hook dùng chung mọi sản phẩm (hook đối thủ sống lâu + hook mình test thắng, kèm bằng chứng), tìm không cần dấu. Dùng khi "thư viện hook", "swipe file", "hook nào đã thắng", "tìm hook cho sản phẩm mới".
argument-hint: "<harvest | results | add | search | report> …"
---

# /angle-lab:hooks

File: `hooks-library/hooks.jsonl` ở gốc dự án (đổi bằng `--lib` hoặc `ANGLE_LAB_HOOKS`). Bản xem nhanh: `hooks-library/README.md`.
```bash
H="${CLAUDE_PLUGIN_ROOT}/scripts/hooks_library.py"
python3 "$H" harvest --root research --niche "<ngách>"            # gom research/*/03-videos/hooks.jsonl
python3 "$H" results --readout research/<slug>/creative/readout.json --variants research/<slug>/creative/04-variants.csv --product <slug> --niche "<ngách>" --angle "<angle>"
python3 "$H" add --text "…" --type "…" --angle "…" --niche "…" --days 95 --dupes 6 [--source own]
python3 "$H" search --q "dau lung" --status proven --top 15         # không cần dấu
python3 "$H" report
```
Mỗi dòng `03-videos/hooks.jsonl`: `{"text","type","angle","pain","platform","visual","ad_id","days_running","duplicates","eu_reach","views"}` (text lấy từ `ocr.txt` + `transcript.txt`, không đoán).

Xếp hạng: mình test WINNER > đối thủ Long-Runner + nhiều bản nhân > đã test thua > ý tưởng. Dùng **khung** hook, viết lại cho đúng nỗi đau của angle hiện tại; hook ngách khác vẫn phải test lại. Hook bị KILL vẫn giữ để tránh lặp lại.

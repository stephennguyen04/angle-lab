---
name: transcribe
description: Nghe lời thoại/voiceover video ad → chữ (tiếng Việt có dấu, tiếng Anh…), timestamp từng từ, câu hook 3s, tốc độ nói, phụ đề .srt. Dùng khi "nghe video", "transcript", "bóc lời thoại", "họ nói gì".
argument-hint: "<video | audio> [--lang vi]"
---

# /angle-lab:transcribe

Cài: `pip install faster-whisper` (lần đầu tải model `medium` ~1,5 GB). Dự phòng: `pip install openai-whisper`.
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" <video> --out-dir <thư mục video> --lang vi [--model medium] [--prompt "<tên SP, brand, từ ngách>"]
```
- `--model`: `medium` (mặc định, giữ dấu tốt) · `large-v3` (chính xác nhất, chậm ~2×) · `small` (nhanh, sai nhiều với tiếng Việt).
- `--prompt` giúp viết đúng tên riêng. `video_prep.sh` tự gọi bước này (`ASR_LANG=vi ASR_MODEL=medium`).
- Output: `transcript.txt` (đọc file này), `transcript.srt` (chia theo câu, dùng lại khi dựng), `transcript.json` (`hook_0_3s`, `first_word_at`, `words_per_sec`, `pauses`, `low_confidence_words`).

**Kiểm tra:** từ độ tin cậy thấp (tên riêng, số, giá) thì đối chiếu với `ocr.txt` hoặc nghe lại. Nhạc to, nói nhanh: dùng `large-v3` + `--prompt`.

**Dùng:** hook bằng lời + giây bắt đầu nói · nhịp (khoảng 2,5–3,5 từ/giây là UGC tự nhiên) · gắn câu vào beat · cụm từ đắt giá → thư viện hook. Script của mình phải viết lại bằng lời của mình.

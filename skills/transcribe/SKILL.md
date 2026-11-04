---
name: transcribe
description: Nghe lời thoại / voiceover của video ad và chuyển thành chữ (tiếng Việt có dấu, tiếng Anh và ngôn ngữ khác), có timestamp từng từ, câu nói trong 3 giây đầu (hook), tốc độ nói, khoảng ngừng, từ model không chắc, và phụ đề .srt. Dùng khi cần phân tích lời trong video đối thủ hoặc video thắng, viết lại script, làm phụ đề, hoặc nói "nghe video", "chuyển giọng nói thành chữ", "transcript", "bóc lời thoại", "speech to text", "họ nói gì trong video".
argument-hint: "<video | audio> [--lang vi]"
---

# /angle-lab:transcribe: Nghe lời thoại → chữ

## Cài một lần

```bash
pip install faster-whisper          # khuyên dùng; chạy CPU được
```
Lần đầu chạy sẽ tải model (~1,5 GB với `medium`). Không cài được thì `pip install openai-whisper` (script tự dùng làm dự phòng).

## Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" <video|audio> --out-dir <thư mục video> --lang vi \
  [--model medium] [--prompt "<tên sản phẩm, thương hiệu, từ chuyên ngành>"]
```
- `--lang vi` khi biết là tiếng Việt (chính xác hơn tự nhận). Video tiếng Anh thì `--lang en`.
- `--model`: `medium` (mặc định, giữ dấu tiếng Việt tốt), `large-v3` (chính xác nhất, chậm hơn ~2×), `small` (nhanh nhưng sai nhiều với tiếng Việt).
- `--prompt`: tên sản phẩm, brand, từ ngách ("PosturePro, nẹp lưng, cột sống"). Model sẽ viết đúng chính tả các từ này.
- `video_prep.sh` tự gọi bước này nếu có faster-whisper (đặt `ASR_LANG=vi ASR_MODEL=medium` trước lệnh).

Output:
- `transcript.json`: `segments` + `words` (timestamp từng từ, độ tin cậy), `hook_0_3s` (lời nói trong 3 giây đầu), `first_word_at`, `words_per_sec`, `speech_ratio`, `pauses` (ngừng >0,7s), `low_confidence_words`.
- `transcript.txt`, và `transcript.srt` chia theo câu hoặc ~4 giây (dùng lại khi dựng video test/nhân bản).

## Kiểm tra lại

- Từ trong `low_confidence_words` (nhất là tên riêng, số, giá tiền): nghe lại đoạn đó, hoặc đối chiếu chữ trên màn hình (`/angle-lab:ocr`). Thường lời nói và caption trùng nhau.
- Nhạc nền to, nói nhanh, giọng địa phương: chuyển lên `large-v3`, thêm `--prompt`.
- Video không có âm thanh: script báo rõ; khi đó phân tích bằng hình + OCR.

## Dùng kết quả trong phân tích

- **Hook bằng lời:** `hook_0_3s` + `first_word_at`. Nói ngay ở giây 0 hay mở bằng hình/âm thanh trước? Câu đầu gọi nỗi đau, kết quả, hay tò mò?
- **Nhịp:** `words_per_sec` (~2,5–3,5 là nhịp UGC tự nhiên; >4 là dồn dập), `pauses` (ngừng dài giữa video dễ mất người xem).
- **Beat theo timestamp:** gắn từng câu vào beat (Hook → Problem → Mechanism → Proof → Offer → CTA) trong `analysis.md`.
- **Ngôn ngữ đối thủ / khách:** cụm từ đắt giá đưa vào thư viện hook (`/angle-lab:hooks`) và script nhân bản.
- Script viết lại cho video của mình phải **viết lại bằng lời của mình**, không chép nguyên văn lời đối thủ.

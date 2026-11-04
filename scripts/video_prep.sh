#!/usr/bin/env bash
# video_prep.sh: Chuẩn bị 1 video ad để AI "xem": khung hình hook 0–3s, keyframe theo cảnh, transcript.
#
# Dùng: bash video_prep.sh <file_video | URL> <out_dir>
#   URL (TikTok / IG / YouTube / FB / link .mp4 Ad Library) → tải bằng yt-dlp (hoặc curl nếu là .mp4 trực tiếp)
#
# Output:
#   out_dir/video.mp4
#   out_dir/hook/hook_XX.jpg        : 4 fps trong 3 giây đầu (12 khung) để soi hook
#   out_dir/scenes/scene_XXX.jpg    : keyframe khi đổi cảnh (tối đa 24), kèm scenes.txt (timestamp)
#   out_dir/audio.wav
#   out_dir/transcript.txt|.srt|.json : lời thoại (transcribe.py, nếu có faster-whisper/whisper). ASR_LANG=vi ASR_MODEL=medium
#   out_dir/ocr.json|.txt           : chữ trên màn hình có dấu (ocr_frames.py, nếu có tesseract-vie/easyocr)
#   out_dir/meta.json               : duration, độ phân giải, số cảnh, nhịp cắt (cuts/10s)
set -euo pipefail
SRC="${1:?Thiếu video hoặc URL}"
OUT="${2:?Thiếu out_dir}"
mkdir -p "$OUT/hook" "$OUT/scenes"
command -v ffmpeg >/dev/null || { echo "Thiếu ffmpeg"; exit 2; }

VID="$OUT/video.mp4"
if [[ "$SRC" =~ ^https?:// ]]; then
  if [[ "$SRC" =~ \.mp4(\?|$) ]] || [[ "$SRC" =~ fbcdn|video\.f ]]; then
    curl -sSL "$SRC" -o "$VID"
  elif command -v yt-dlp >/dev/null; then
    yt-dlp -q -f "mp4/bestvideo*+bestaudio/best" --merge-output-format mp4 -o "$VID" "$SRC"
  else
    echo "Cần yt-dlp để tải từ nền tảng: pipx install yt-dlp (hoặc pip install yt-dlp)"; exit 2
  fi
else
  cp "$SRC" "$VID"
fi

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VID" | cut -d. -f1)
RES=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$VID")

# Hook: 3 giây đầu, 4 fps
ffmpeg -loglevel error -y -t 3 -i "$VID" -vf "fps=4,scale=540:-2" "$OUT/hook/hook_%02d.jpg"

# Keyframe theo đổi cảnh
ffmpeg -hide_banner -loglevel info -y -i "$VID" -vf "select='gt(scene,0.30)',showinfo,scale=540:-2" -vsync vfr \
  -frames:v 24 "$OUT/scenes/scene_%03d.jpg" 2> "$OUT/scenes/_showinfo.log" || true
grep "Parsed_showinfo" "$OUT/scenes/_showinfo.log" | grep -o "pts_time:[0-9.]*" | cut -d: -f2 > "$OUT/scenes/scenes.txt" || true
NSCENES=$(wc -l < "$OUT/scenes/scenes.txt" | tr -d ' ')
# Ít cảnh quá (video 1 shot) → lấy mỗi 2s 1 khung
if [ "${NSCENES:-0}" -lt 4 ]; then
  ffmpeg -loglevel error -y -i "$VID" -vf "fps=1/2,scale=540:-2" -frames:v 24 "$OUT/scenes/every2s_%03d.jpg"
fi

ffmpeg -loglevel error -y -i "$VID" -vn -ac 1 -ar 16000 "$OUT/audio.wav" || true

# Nghe → chữ (transcribe.py) và đọc chữ trên màn hình (ocr_frames.py), nếu máy có công cụ
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANS="none"
if [ -f "$OUT/audio.wav" ] && { python3 -c "import faster_whisper" 2>/dev/null || command -v whisper >/dev/null; }; then
  if python3 "$HERE/transcribe.py" "$VID" --out-dir "$OUT" ${ASR_LANG:+--lang "$ASR_LANG"} ${ASR_MODEL:+--model "$ASR_MODEL"} >"$OUT/transcribe.log" 2>&1; then
    TRANS=$(python3 -c "import json;print(json.load(open('$OUT/transcript.json')).get('engine') or 'none')")
  fi
fi
OCR="none"
if command -v tesseract >/dev/null || python3 -c "import easyocr" 2>/dev/null; then
  if python3 "$HERE/ocr_frames.py" --video "$VID" --out-dir "$OUT" >"$OUT/ocr.log" 2>&1; then
    OCR=$(python3 -c "import json;print(json.load(open('$OUT/ocr.json')).get('engine'))")
  fi
fi

CUTS10=$(python3 -c "d=${DUR:-0} or 1; print(round(${NSCENES:-0}/d*10,1))")
cat > "$OUT/meta.json" <<JSON
{"duration_s": ${DUR:-0}, "resolution": "${RES}", "scene_cuts": ${NSCENES:-0}, "cuts_per_10s": ${CUTS10}, "transcript": "${TRANS}", "ocr": "${OCR}"}
JSON
echo "OK → $OUT  (dài ${DUR}s, ${RES}, ${NSCENES} lần cắt cảnh, lời thoại: ${TRANS}, chữ trên màn hình: ${OCR})"
if [ ! -s "$OUT/audio.wav" ]; then echo "Video không có âm thanh: phân tích bằng hình + chữ trên màn hình."
elif [ "$TRANS" = "none" ]; then echo "Gợi ý: pip install faster-whisper → có transcript lời thoại (ASR_LANG=vi để ép tiếng Việt)."; fi
[ "$OCR" = "none" ] && echo "Gợi ý: cài tesseract + tiếng Việt (apt install tesseract-ocr tesseract-ocr-vie | brew install tesseract tesseract-lang) → đọc chữ trên màn hình." || true

#!/usr/bin/env python3
"""transcribe.py: Nghe lời thoại / voiceover của video ad → chữ (tiếng Việt có dấu, tiếng Anh…), có timestamp từng từ.

Engine:
  1. faster-whisper (pip install faster-whisper): nhanh, chạy CPU được, có timestamp từng từ + lọc khoảng lặng (VAD)
  2. openai-whisper CLI (pip install openai-whisper): dự phòng
Lần đầu chạy sẽ tải model về máy (medium ≈ 1.5 GB). Tiếng Việt: medium trở lên mới giữ dấu tốt; small/base nhanh nhưng sai nhiều.

Dùng:
  python3 transcribe.py <video|audio> --out-dir out/ [--lang vi] [--model small] [--prompt "PosturePro, nẹp lưng"]
    --lang   : bỏ trống để tự nhận; ghi rõ "vi" khi biết là tiếng Việt sẽ chính xác hơn
    --prompt : tên sản phẩm/thương hiệu/từ chuyên ngành, giúp model viết đúng chính tả

Output trong out-dir:
  transcript.json : language, duration, segments[{start,end,text,words[{start,end,word,prob}]}],
                    hook_0_3s (lời nói trong 3 giây đầu), first_word_at, words_per_sec, pauses (>0.7s),
                    low_confidence_words (từ model không chắc, nên nghe lại)
  transcript.txt  : "[  0.00] câu…"
  transcript.srt  : phụ đề (dùng lại khi dựng video test / nhân bản)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").strip()


def to_wav(src: Path, dst: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 1000


def srt_time(t: float) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"


def run_faster_whisper(wav: Path, a) -> dict:
    from faster_whisper import WhisperModel  # type: ignore
    model = WhisperModel(a.model, device="auto", compute_type=a.compute_type)
    # Tự đọc WAV 16 kHz mono → mảng float32, tránh lỗi lệch phiên bản thư viện 'av' khi faster-whisper tự giải mã
    import wave
    import numpy as np  # type: ignore
    with wave.open(str(wav), "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, language=a.lang, initial_prompt=a.prompt, word_timestamps=True,
                                  vad_filter=True, beam_size=5)
    out = []
    for s in segs:
        out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": nfc(s.text),
                    "words": [{"start": round(w.start, 2), "end": round(w.end, 2), "word": nfc(w.word), "prob": round(w.probability, 2)}
                              for w in (s.words or [])]})
    return {"engine": f"faster-whisper/{a.model}", "language": info.language, "language_prob": round(info.language_probability, 2),
            "duration": round(info.duration, 2), "segments": out}


def run_whisper_cli(wav: Path, a, tmp: Path) -> dict:
    cmd = ["whisper", str(wav), "--model", a.model, "--output_dir", str(tmp), "--output_format", "json", "--word_timestamps", "True"]
    if a.lang:
        cmd += ["--language", a.lang]
    if a.prompt:
        cmd += ["--initial_prompt", a.prompt]
    subprocess.run(cmd, check=True, capture_output=True)
    d = json.loads((tmp / f"{wav.stem}.json").read_text(encoding="utf-8"))
    segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": nfc(s["text"]),
             "words": [{"start": round(w["start"], 2), "end": round(w["end"], 2), "word": nfc(w["word"]), "prob": round(w.get("probability", 1), 2)}
                       for w in s.get("words", [])]} for s in d.get("segments", [])]
    return {"engine": f"whisper/{a.model}", "language": d.get("language"), "language_prob": None,
            "duration": segs[-1]["end"] if segs else 0, "segments": segs}


def srt_chunks(res: dict, max_s: float = 4.0, max_words: int = 10) -> list[dict]:
    """Chia phụ đề theo dấu câu / ~4 giây / ~10 từ để dùng lại khi dựng video."""
    words = [w for s in res["segments"] for w in s["words"]]
    if not words:
        return res["segments"]
    out, cur = [], []
    for w in words:
        cur.append(w)
        if (w["word"].rstrip().endswith((".", ",", "?", "!", "…")) or w["end"] - cur[0]["start"] >= max_s
                or len(cur) >= max_words):
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": nfc(" ".join(x["word"] for x in cur)).replace("  ", " ")})
            cur = []
    if cur:
        out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": nfc(" ".join(x["word"] for x in cur)).replace("  ", " ")})
    return out


def analyze(res: dict, hook_s: float) -> dict:
    words = [w for s in res["segments"] for w in s["words"]]
    if not words:  # engine không trả timestamp từng từ → ước lượng theo câu
        hook = " ".join(s["text"] for s in res["segments"] if s["start"] < hook_s)
        res.update(hook_0_3s=hook, first_word_at=res["segments"][0]["start"] if res["segments"] else None,
                   words_per_sec=None, pauses=[], low_confidence_words=[])
        return res
    hook_words = [w["word"] for w in words if w["start"] < hook_s]
    speech = sum(w["end"] - w["start"] for w in words)
    pauses = [{"at": round(b["start"], 2), "len": round(b["start"] - a_["end"], 2)}
              for a_, b in zip(words, words[1:]) if b["start"] - a_["end"] > 0.7]
    res.update(
        hook_0_3s=nfc(" ".join(hook_words)).replace("  ", " "),
        first_word_at=words[0]["start"],
        words_per_sec=round(len(words) / max(words[-1]["end"] - words[0]["start"], 0.1), 2),
        speech_ratio=round(speech / max(res["duration"], 0.1), 2),
        pauses=pauses,
        low_confidence_words=[{"t": w["start"], "word": w["word"], "prob": w["prob"]} for w in words if w["prob"] < 0.5][:40],
    )
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--lang", default=None, help="vi, en, … (trống = tự nhận)")
    ap.add_argument("--model", default="medium", help="tiny | base | small | medium (mặc định, tốt cho tiếng Việt) | large-v3 (chính xác nhất, chậm)")
    ap.add_argument("--compute-type", default="int8")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--hook-seconds", type=float, default=3.0)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        wav = tmp / "audio.wav"
        if not to_wav(Path(a.src), wav):
            res = {"engine": None, "language": None, "duration": 0, "segments": [], "note": "video không có âm thanh"}
            (out / "transcript.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            (out / "transcript.txt").write_text("(không có âm thanh)\n", encoding="utf-8")
            print("Video không có âm thanh → chỉ phân tích hình + chữ trên màn hình (ocr_frames.py).")
            return
        try:
            import faster_whisper  # type: ignore  # noqa: F401
            res = run_faster_whisper(wav, a)
        except ImportError:
            if shutil.which("whisper"):
                res = run_whisper_cli(wav, a, tmp)
            else:
                sys.exit("Chưa có engine nghe → chữ. Cài: pip install faster-whisper  (hoặc pip install openai-whisper)")
    res = analyze(res, a.hook_seconds)
    (out / "transcript.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "transcript.txt").write_text("\n".join(f"[{s['start']:>6.2f}] {s['text']}" for s in res["segments"]) + "\n", encoding="utf-8")
    (out / "transcript.srt").write_text("\n".join(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n"
                                                  for i, s in enumerate(srt_chunks(res), 1)), encoding="utf-8")
    print(f"Ngôn ngữ: {res['language']} · dài {res['duration']}s · engine {res['engine']}")
    print(f"HOOK 0–{a.hook_seconds:g}s (lời): {res.get('hook_0_3s') or '(chưa nói gì)'} · từ đầu tiên ở {res.get('first_word_at')}s · "
          f"{res.get('words_per_sec')} từ/giây")
    for s in res["segments"][:6]:
        print(f"[{s['start']:>6.2f}] {s['text']}")
    if res.get("low_confidence_words"):
        print(f"⚠️ {len(res['low_confidence_words'])} từ độ tin cậy thấp, nên nghe lại: "
              + ", ".join(f"{w['word']}@{w['t']}s" for w in res["low_confidence_words"][:8]))


if __name__ == "__main__":
    main()

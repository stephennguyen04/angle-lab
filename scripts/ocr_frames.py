#!/usr/bin/env python3
"""ocr_frames.py: Đọc CHỮ TRÊN MÀN HÌNH (text overlay, caption, sticker giá…) của video/ảnh ad, hỗ trợ tiếng Việt có dấu.

Engine (tự chọn cái có sẵn, ưu tiên theo thứ tự):
  1. tesseract + gói ngôn ngữ vie   (apt install tesseract-ocr tesseract-ocr-vie | brew install tesseract tesseract-lang)
  2. easyocr ['vi','en']            (pip install easyocr, nặng hơn nhưng tốt với chữ cách điệu)

Mỗi khung được xử lý 2 kiểu (chữ sáng trên nền tối và ngược lại), phóng to 2× rồi chọn kết quả có độ tin cậy cao hơn.
Chữ giống nhau ở các khung liên tiếp được gộp thành 1 đoạn có thời gian bắt đầu/kết thúc.

Dùng:
  python3 ocr_frames.py --video ad.mp4 --out-dir out/ [--fps 2] [--hook-fps 4] [--lang vie+eng]
  python3 ocr_frames.py --images a.jpg b.png --out-dir out/          # ảnh tĩnh / screenshot
Output: ocr.json (timeline + hook 0–3s) · ocr.txt ("[0.0–2.5] chữ")
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def clean(s: str) -> str:
    s = nfc(s).replace("|", "I")
    s = re.sub(r"[^\w\s%$€£₫.,!?:;'\"()+\-/&@#…–—]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------- tiền xử lý ----------
def variants(img_path: Path, tmp: Path) -> list[Path]:
    """3 bản: (1) tách chữ sáng trắng/vàng (caption ad phổ biến nhất: chữ trắng viền đen) → chữ đen nền trắng,
    (2) xám tăng tương phản, (3) đảo màu. Phóng lên chiều ngang ~1400px."""
    try:
        from PIL import Image, ImageOps, ImageFilter  # type: ignore
    except ImportError:
        return [img_path]
    rgb = Image.open(img_path).convert("RGB")
    w, h = rgb.size
    scale = max(1.0, min(2.0, 1400 / max(1, min(w, h))))
    rgb = rgb.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    gray = rgb.convert("L")
    # chữ sáng: luma cao và độ bão hoà thấp (trắng) hoặc vàng (B thấp, R,G cao)
    r, g, b = rgb.split()
    bright = gray.point(lambda v: 255 if v >= 190 else 0)
    mask = ImageOps.invert(bright).filter(ImageFilter.MedianFilter(3))
    out = []
    for name, v in (("m", mask), ("g", ImageOps.autocontrast(gray, cutoff=2)), ("i", ImageOps.invert(ImageOps.autocontrast(gray, cutoff=2)))):
        p = tmp / f"{img_path.stem}_{name}.png"
        v.save(p)
        out.append(p)
    return out


# ---------- engine ----------
def tesseract_ok(lang: str) -> bool:
    if not shutil.which("tesseract"):
        return False
    langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout + \
        subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stderr
    return all(l in langs.split() for l in lang.split("+"))


def ocr_tesseract(p: Path, lang: str, min_conf: float) -> tuple[str, float]:
    best = ("", 0.0)
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
    for psm in ("11",):   # 11: chữ rải rác (text overlay, sticker, caption)
        r = subprocess.run(["tesseract", str(p), "stdout", "-l", lang, "--oem", "1", "--psm", psm, "tsv"],
                           capture_output=True, text=True, env=env)
        lines: dict[tuple, list] = {}
        confs = []
        for row in r.stdout.splitlines()[1:]:
            c = row.split("\t")
            if len(c) < 12 or not c[11].strip():
                continue
            try:
                conf = float(c[10])
            except ValueError:
                continue
            if conf < min_conf:
                continue
            key = (int(c[2]), int(c[3]), int(c[4]))   # block, paragraph, line
            lines.setdefault(key, []).append(c[11])
            confs.append(conf)
        text = " / ".join(clean(" ".join(ws)) for _, ws in sorted(lines.items()) if len(re.sub(r"\W", "", " ".join(ws))) >= 2)
        score = (sum(confs) / len(confs) if confs else 0) * min(1.0, len(text) / 8) + min(len(confs), 12)
        if score > best[1]:
            best = (text, score)
    return best


_EASY = None


def ocr_easy(p: Path, min_conf: float) -> tuple[str, float]:
    global _EASY
    import easyocr  # type: ignore
    if _EASY is None:
        _EASY = easyocr.Reader(["vi", "en"], gpu=False, verbose=False)
    res = _EASY.readtext(str(p))
    res = [r for r in res if r[2] * 100 >= min_conf]
    res.sort(key=lambda r: (round(r[0][0][1] / 40), r[0][0][0]))
    text = clean(" / ".join(r[1] for r in res))
    return text, (sum(r[2] for r in res) / len(res) * 100 if res else 0)


def ocr_image(img: Path, engine: str, lang: str, min_conf: float, tmp: Path) -> tuple[str, float]:
    best = ("", 0.0)
    for v in variants(img, tmp):
        t = ocr_tesseract(v, lang, min_conf) if engine == "tesseract" else ocr_easy(v, min_conf)
        if t[1] > best[1]:
            best = t
    return best


# ---------- timeline ----------
def similar(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.75


def build_timeline(items: list[tuple[float, str, float]], step: float, min_frames: int = 1) -> list[dict]:
    """Theo dõi TỪNG DÒNG chữ: dòng cố định (footer 'Freeship…') không làm rối dòng chính đổi liên tục."""
    open_segs: list[dict] = []
    done: list[dict] = []
    for t, text, conf in sorted(items, key=lambda x: x[0]):
        lines = [l.strip() for l in (text or "").split(" / ") if len(re.sub(r"\W", "", l)) >= 2]
        still = []
        for s in open_segs:
            match = next((l for l in lines if similar(s["text"], l)), None)
            if match is not None and t - s["end"] <= step * 1.6:
                s["end"] = round(t + step, 2)
                s["n"] += 1
                s["reads"].append(match)
                lines.remove(match)
                still.append(s)
            elif t - s["end"] > step * 1.6:
                done.append(s)
            else:
                still.append(s)
        for l in lines:
            still.append({"start": round(t, 2), "end": round(t + step, 2), "text": l, "conf": round(conf, 1), "n": 1, "reads": [l]})
        open_segs = still
    done += open_segs
    out = []
    for s in done:
        if s["n"] < min_frames:
            continue
        # bản đọc "đại diện": dòng giống các lần đọc khác nhất (khử nhiễu OCR từng khung)
        reads = s.pop("reads")
        s["text"] = max(reads, key=lambda r: (sum(difflib.SequenceMatcher(None, r, o).ratio() for o in reads), len(r)))
        s["frames"] = s.pop("n")
        out.append(s)
    return sorted(out, key=lambda s: (s["start"], -s["frames"]))


def extract(video: Path, fps: float, tmp: Path, start=0.0, dur=None, tag="f") -> list[tuple[float, Path]]:
    args = ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(start)]
    if dur:
        args += ["-t", str(dur)]
    args += ["-i", str(video), "-vf", f"fps={fps}", str(tmp / f"{tag}_%05d.png")]
    subprocess.run(args, check=True)
    frames = sorted(tmp.glob(f"{tag}_*.png"))
    return [(start + i / fps, f) for i, f in enumerate(frames)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video")
    ap.add_argument("--images", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--fps", type=float, default=2.0, help="khung/giây cho toàn video")
    ap.add_argument("--hook-fps", type=float, default=4.0, help="khung/giây cho 3 giây đầu")
    ap.add_argument("--lang", default="vie+eng")
    ap.add_argument("--engine", choices=["auto", "tesseract", "easyocr"], default="auto")
    ap.add_argument("--min-conf", type=float, default=55)
    a = ap.parse_args()
    if not a.video and not a.images:
        sys.exit("Cần --video hoặc --images")

    engine = a.engine
    if engine == "auto":
        if tesseract_ok(a.lang):
            engine = "tesseract"
        else:
            try:
                import easyocr  # type: ignore  # noqa: F401
                engine = "easyocr"
            except ImportError:
                sys.exit("Không có engine OCR. Cài 1 trong 2:\n"
                         "  tesseract + tiếng Việt: apt install tesseract-ocr tesseract-ocr-vie  |  brew install tesseract tesseract-lang\n"
                         "  easyocr: pip install easyocr\n"
                         "Hoặc để Claude tự đọc khung hình (Read file ảnh) thay cho OCR.")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res = {"engine": engine, "lang": a.lang}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if a.images:
            res["images"] = []
            for p in a.images:
                text, conf = ocr_image(Path(p), engine, a.lang, a.min_conf, tmp)
                res["images"].append({"file": p, "text": text, "conf": round(conf, 1)})
            lines = [f"{Path(x['file']).name}: {x['text']}" for x in res["images"]]
        else:
            v = Path(a.video)
            hook = extract(v, a.hook_fps, tmp, 0, 3, "h")
            body = [(t, f) for t, f in extract(v, a.fps, tmp, 0, None, "b") if t >= 3]
            from concurrent.futures import ThreadPoolExecutor
            run = lambda tf: (tf[0], *ocr_image(tf[1], engine, a.lang, a.min_conf, tmp))  # noqa: E731
            workers = 1 if engine == "easyocr" else max(1, (os.cpu_count() or 2))
            with ThreadPoolExecutor(workers) as ex:
                hook_items = list(ex.map(run, hook))
                body_items = list(ex.map(run, body))
            hook_tl = build_timeline(hook_items, 1 / a.hook_fps)
            # gộp hook (4 fps) + thân (2 fps): bước thời gian dùng bước lớn hơn để không đứt đoạn
            tl = build_timeline(hook_items + body_items, max(1 / a.fps, 1 / a.hook_fps), min_frames=2)
            hook_main = [s for s in hook_tl if s["frames"] >= 2] or hook_tl
            res.update({
                "hook_0_3s": hook_main,
                "hook_text": " / ".join(s["text"] for s in hook_main),
                "first_text_at": hook_tl[0]["start"] if hook_tl else None,
                "timeline": tl,
                "frames_read": len(hook_items) + len(body_items),
            })
            lines = [f"[{s['start']:.1f}–{s['end']:.1f}] {s['text']}" for s in tl]
            lines.insert(0, f"HOOK 0–3s: {res['hook_text'] or '(không có chữ)'}")
    (out / "ocr.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "ocr.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:40]))
    print(f"\n→ {out}/ocr.json · engine={engine}")


if __name__ == "__main__":
    main()

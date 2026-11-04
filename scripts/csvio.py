"""csvio.py: Đọc CSV "bẩn" (Excel VN dùng dấu ;, tab, BOM, dòng trống) cho mọi script của angle-lab."""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path


def read_csv_rows(path: str | Path) -> list[dict]:
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1258", "latin-1"):
        try:
            text = raw.decode(enc)
            if enc == "utf-16" and not raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                continue
            break
        except UnicodeDecodeError:
            continue
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\n")
    if not text.strip():
        return []
    head = text.split("\n", 1)[0]
    delim = max([",", ";", "\t", "|"], key=head.count)
    if head.count(delim) == 0:
        delim = ","
    # đọc nguyên khối để giữ ô có xuống dòng bên trong dấu ngoặc kép
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    out = []
    for r in reader:
        r = {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items() if k is not None}
        if any(v not in (None, "") for v in r.values()):
            out.append(r)
    return out


def norm_key(k: str) -> str:
    """'Nội dung' → 'noi_dung', 'Số tiền đã chi tiêu (VND)' → 'so_tien_da_chi_tieu_vnd'."""
    k = unicodedata.normalize("NFKD", str(k).strip().lower().replace("đ", "d"))
    k = "".join(ch for ch in k if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", k).strip("_")


def parse_count(v):
    """'1.2K' / '1,2K' / '3M' / '12,345' / '1.234.567' / 1500 → int. Âm hoặc không đọc được → None."""
    if v is None or isinstance(v, (list, dict, bool)):
        return None
    if isinstance(v, (int, float)):
        return None if v < 0 else int(v)
    s = str(v).strip().lower().replace("\u00a0", "").replace(" ", "")
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)([kmb]|n|tr|ngh[iì]n|tri[eệ]u)?", s)
    if m and m[2]:
        mult = {"k": 1e3, "n": 1e3, "nghin": 1e3, "nghìn": 1e3, "m": 1e6, "tr": 1e6, "trieu": 1e6, "triệu": 1e6, "b": 1e9}[m[2]]
        return int(float(m[1].replace(",", ".")) * mult)
    digits = re.sub(r"[.,](?=\d{3}(\D|$))", "", s)      # bỏ dấu phân cách nghìn
    m = re.match(r"-?\d+(?:[.,]\d+)?", digits)
    if not m or m[0].startswith("-"):
        return None
    return int(float(m[0].replace(",", ".")))

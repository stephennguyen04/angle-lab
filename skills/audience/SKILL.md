---
name: audience
description: Persona đối thủ THỰC SỰ tiếp cận (giới, tuổi, quốc gia theo angle/ad) từ dữ liệu minh bạch EU/UK của Ad Library, để chọn nhân vật video. Dùng khi "đối thủ đánh vào ai", "persona", "độ tuổi giới tính khách".
argument-hint: "<research/<slug>> [Page ID] [quốc gia EU/UK]"
---

# /angle-lab:audience

Target khai báo thường rộng; người xem thực tế dồn vào nhóm mà thuật toán tìm ra là **người mua**. Chỉ có dữ liệu với ad **phân phối ở EU/UK**. Không có thì dùng nhân vật trong ad sống lâu nhất, persona người hỏi mua trong bình luận, creator trong ad hợp tác.

**Lấy dữ liệu:** (A) API: xác minh danh tính tại facebook.com/ID → User Access Token (Graph API Explorer) → `export META_ADLIB_TOKEN=…`; hoặc (B) HAR với quốc gia EU/UK, có mở "See ad details".
```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"
python3 "$S/adlib_api.py" --page-ids <ID> --countries DE,FR,GB -o research/<slug>/01-scale/ads_api.json      # lỗi version: --version v23.0|v25.0
python3 "$S/adlib_parse.py" -i research/<slug>/01-scale/ads_api.json -o research/<slug>/01-scale/ads_eu.json
python3 "$S/audience.py" --ads research/<slug>/01-scale/ads_eu.json --angle-map research/<slug>/01-scale/angle_map.csv --out-md research/<slug>/01-scale/audience.md
```
**Dùng:** nhân vật video test theo persona của từng angle · nhân bản: C0 = persona lớn nhất, C1–C2 = nhóm lớn thứ 2, 3 · hai angle khác persona = hai thị trường con, không trộn · persona lệch target = thuật toán đang mở rộng.

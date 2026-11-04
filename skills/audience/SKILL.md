---
name: audience
description: Đọc persona mà đối thủ THỰC SỰ tiếp cận (giới tính, nhóm tuổi, quốc gia, theo từng angle và từng ad) từ dữ liệu minh bạch EU/UK của Meta Ad Library (lượt tiếp cận EU, cơ cấu tuổi × giới × quốc gia, target khai báo), để chọn đúng nhân vật khi dựng video test và nhân bản. Dùng khi hỏi "đối thủ đánh vào ai", "persona", "độ tuổi giới tính khách", "ai đang xem ad của họ", "chọn nhân vật cho video", "Ad Library API".
argument-hint: "<research/<slug>> [Page ID] [quốc gia EU/UK]"
---

# /angle-lab:audience: Persona đối thủ đang tiếp cận

**Vì sao đáng làm:** target khai báo thường rất rộng (18–65+, mọi giới), nhưng người xem thực tế dồn vào một nhóm. Đó là nhóm thuật toán Meta đã tìm ra là **người mua**. Chọn nhân vật video theo nhóm này, thay vì đoán.

**Giới hạn:** dữ liệu này chỉ có với ad **có phân phối ở EU/UK** (quy định DSA). Đối thủ chỉ bán ở Mỹ hoặc Việt Nam thì không có. Khi đó dùng tín hiệu thay thế: nhân vật trong các ad sống lâu nhất, persona trong bình luận (ai đang hỏi mua), và creator trong ad hợp tác.

## 1. Lấy dữ liệu (chọn 1)

**A. Ad Library API chính thức** (đầy đủ nhất, cần làm 1 lần):
1. Xác minh danh tính & vị trí tại facebook.com/ID.
2. Lấy User Access Token ở developers.facebook.com (Graph API Explorer). Không ghi token vào file hay repo.
```bash
export META_ADLIB_TOKEN=…
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_api.py" --page-ids <PAGE_ID> --countries DE,FR,GB -o research/<slug>/01-scale/ads_api.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adlib_parse.py" -i research/<slug>/01-scale/ads_api.json -o research/<slug>/01-scale/ads_eu.json
```
Lỗi về phiên bản thì thêm `--version v23.0` hoặc `v25.0`. Chọn các nước EU/UK mà đối thủ thật sự bán.

**B. File HAR** (không cần token): trên Ad Library chọn quốc gia EU/UK, bấm "See ad details" ở các ad cần xem rồi lưu HAR → `adlib_parse.py`. Mục chi tiết có cơ cấu tiếp cận nếu Meta hiển thị.

## 2. Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audience.py" --ads research/<slug>/01-scale/ads_eu.json \
  --angle-map research/<slug>/01-scale/angle_map.csv \
  --out-md research/<slug>/01-scale/audience.md --out-json research/<slug>/01-scale/audience.json
```
Kết quả gồm: theo angle (% nữ/nam, nhóm tuổi chính, quốc gia, ô persona lớn nhất, 1 câu persona), và top ad theo tiếp cận (persona thực tế vs target khai báo).

## 3. Dùng kết quả

- **Angle test:** nhân vật trong video test của mỗi angle khớp persona của angle đó.
- **Nhân bản (`/angle-lab:clone`):** nhân vật C0 = persona chính; C1–C2 = nhóm lớn thứ hai, thứ ba (vd "Nữ 35–44" → "Nữ 45–54", "Nam 35–44") để mở rộng có căn cứ.
- **Hai angle đánh vào hai persona khác nhau:** đó là hai thị trường con; không trộn chung một video.
- **Persona lệch target:** target nữ nhưng người xem nhiều nam → thuật toán mở rộng; xem ad đó có còn sống lâu không.

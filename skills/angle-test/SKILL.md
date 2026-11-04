---
name: angle-test
description: Giai đoạn 1 "TEST ANGLE TRƯỚC": dựng lại 5 video top thành 5 video test (1 video = 1 angle, mọi thứ khác cố định), cấu trúc camp, ngân sách theo CPA hoà vốn, naming, rule kill. Dùng khi "test angle", "edit lại 5 video đối thủ", "lên camp test".
argument-hint: "<research/<slug>> [giá] [giá vốn] [ship]"
---

# /angle-lab:angle-test

Giai đoạn này chỉ nhằm **biết angle nào ăn tiền**: 5 video khác nhau ở angle, mọi thứ khác giống nhau. Input: `01-scale/scoreboard.json` (A1–A5), `03-videos/`, `04-comments/insights.md`, `02-funnel/funnel.md`. Output: `creative/01-test-plan.md` + `creative/briefs/A1..A5.md`.

## 1. Chốt A1–A5
Lấy mã từ `scoreboard.json` (`test_code`). Bảng: mã · angle 1 câu · nỗi đau · persona · điểm · video tham chiếu (bài share cao nhất hoặc ad sống lâu nhất của angle đó). Angle bị chê nhiều → chèn đoạn xử lý objection.

## 2. Brief dựng lại `briefs/A<n>.md`
"Edit lại" = **dựng lại theo cấu trúc** (giữ angle, beat, nhịp, kiểu hook); **không re-up nguyên footage, giọng, logo** của đối thủ (bị report IP là mất ad/page, data test bẩn). Có 3 cách: quay lại · AI dựng lại (Higgsfield / `higgsfield-prompt-director`) + cảnh sản phẩm thật · re-edit footage của mình (`stock-footage`, `ffmpeg-video-edit`).
Brief gồm: angle + video gốc · **script viết lại bằng lời của mình** chia beat có timestamp (lấy từ `transcript.json` + `ocr.json` của video gốc), chèn ngôn ngữ khách từ `insights.md` · hook 0–3s (giữ kiểu hook gốc) · shot list · chữ trên màn hình, caption, nhạc · độ dài ±20% bản gốc · nhân vật hợp persona (`01-scale/audience.md` nếu có) · checklist (không logo đối thủ, không claim y tế vô căn cứ, 9:16).

## 3. Test plan `01-test-plan.md`
- **Cố định:** offer, giá, LP, audience broad, placement, template primary text/headline, thời điểm launch.
- **Meta:** 1 campaign Sales, **ABO**; 5 ad set = 5 angle, mỗi ad set 1 ad (hoặc 2 ad cùng angle khác hook); ngân sách/ad set/ngày ≈ 0.5–1× CPA hoà vốn; chạy 3–4 ngày; mỗi angle tiêu ≥2–3× CPA hoà vốn mới kết luận; không sửa ad khi đang test.
- CPA hoà vốn = giá − giá vốn − ship − phí%. Chưa có số thì hỏi.
- **Naming (bắt buộc):** `<yymmdd>_A<n>-<slug>_V<nn>_H<n>`.
- **Rule** (`test_readout.py`): WINNER ≥3 đơn và CPA ≤ BE · TIỀM NĂNG có đơn, CPA ≤ BE, <3 đơn · BORDERLINE CPA 1–1.5× BE · KILL chi ≥1.5× BE mà 0 đơn, hoặc hook rate <15% sau 3.000 hiển thị, hoặc chi ≥1× BE với 0 ATC và CTR <0.7%.
- Chỉ số "vì sao thua": hook rate (dừng lại không) · hold rate (giữ được không) · CTR (lời hứa đủ hấp dẫn không) · ATC rate (PDP/offer có khớp không).

## 4. Tiếp
Ghi ngày launch, ngày đọc số (D+3, D+4). Khi có số: export cấp **Ad** → `/angle-lab:winner research/<slug> <file>`. Ghi quyết định vào `creative/log.md`.

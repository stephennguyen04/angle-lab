---
name: angle-test
description: Giai đoạn 1 của quy trình creative "TEST ANGLE TRƯỚC, NHÂN BẢN SAU". Từ 5 video top của đối thủ, lên brief edit/dựng lại 5 video test, mỗi video = đúng 1 angle, giữ mọi thứ khác cố định để đọc được angle nào ăn tiền. Có cấu trúc campaign, ngân sách theo CPA hoà vốn, naming convention, rule kill/giữ. Dùng khi nói "test angle", "edit lại 5 video đối thủ", "lên camp test", "test creative", "remix video đối thủ".
argument-hint: "<research/<slug>> [giá bán] [giá vốn] [phí ship]"
---

# /angle-lab:angle-test: TEST ANGLE TRƯỚC

**Nguyên tắc:** giai đoạn này chỉ nhằm **xác định angle nào ăn tiền**, chưa cần creative đẹp và chưa tối ưu hook. Vì vậy mỗi video test phải khác nhau **ở angle**, còn lại giữ giống nhau nhiều nhất có thể.

Input: `research/<slug>/01-scale/scoreboard.json` + `scoreboard.md` (A1–A5 đã chốt từ dữ liệu mạng xã hội), `03-videos/videos.md` + `04-comments/insights.md` + `02-funnel/funnel.md`. Thiếu thì chạy `/angle-lab:spy` trước. Output: `research/<slug>/creative/01-test-plan.md` + `creative/briefs/A1..A5.md`.

## 1. Chốt 5 angle

Lấy đúng mã **A1…A5** từ `scoreboard.json` (trường `test_code`), dùng xuyên suốt (tên ad, file, báo cáo). Chưa có scoreboard thì chạy `/angle-lab:scoreboard` trước.
| Mã | Angle (1 câu) | Nỗi đau | Persona | Điểm MXH | Tín hiệu mạnh nhất | Video tham chiếu |
- Mỗi angle chọn **bài có share cao nhất** (hoặc ad sống lâu nhất) của chính angle đó làm bản gốc để dựng lại.
- Nếu đổi 1 slot sang angle "khoảng trống" từ bình luận: sửa `test_code` trong `scoreboard.json` cho khớp, để bước đọc số so sánh đúng.
- Angle bị chê nhiều trong bình luận: chèn đoạn xử lý objection đó vào script.
- Điểm MXH chỉ để chọn angle và đối chiếu sau test. Rule kill vẫn theo CPA hoà vốn ở mục 3.

## 2. Brief edit cho từng angle → `creative/briefs/A<n>.md`

"Edit lại" ở đây = **dựng lại theo cấu trúc** video gốc của đối thủ: giữ angle, beat, nhịp, kiểu hook. **Không re-up nguyên footage/giọng/logo của họ.** Họ report IP là ad bị gỡ, page/TKQC bị hạn chế, và data test cũng bẩn theo. Có 3 cấp, chọn theo nguồn lực:
1. **Quay lại** cùng beat với sản phẩm của mình (tốt nhất).
2. **AI dựng lại:** nhân vật AI/UGC AI + bối cảnh mới đọc script cùng cấu trúc (MCP Higgsfield hoặc skill `higgsfield-prompt-director` nếu có), chèn cảnh quay sản phẩm thật của mình.
3. **Re-edit từ footage của mình** (hàng mẫu, b-roll, stock: skill `stock-footage`), voiceover + chữ theo script viết lại.

Mỗi brief gồm:
- Angle 1 câu + video gốc tham chiếu (link, thời lượng)
- **Script viết lại bằng lời của mình**, chia beat có timestamp, bám đúng thứ tự beat của video gốc; chèn ngôn ngữ khách thật từ `insights.md`
- Hook 0–3s: hình + chữ + câu nói (giữ **kiểu hook** của bản gốc)
- Shot list (cảnh, góc máy, thời lượng, nguồn footage)
- Chữ trên màn hình, caption, nhạc, độ dài (giữ ±20% bản gốc)
- Checklist: không logo/watermark đối thủ · không claim y tế/kết quả vô căn cứ · ra mắt ở khung 9:16 (thêm 4:5 nếu chạy Feed)

Muốn tự cắt ghép thì dùng skill `ffmpeg-video-edit` nếu có (9:16, burn caption, loudness).

## 3. Thiết kế test để đọc được angle → `creative/01-test-plan.md`

**Biến cố định** (giống hệt cho cả 5): offer & giá · landing page · audience (broad, cùng quốc gia/độ tuổi) · placement · primary text/headline theo cùng template (chỉ đổi dòng đầu cho khớp angle) · thời điểm launch.

**Cấu trúc gợi ý (Meta):**
- 1 campaign Sales/Conversion (Purchase), **ABO** để chia đều tiền
- 5 ad set = 5 angle, mỗi ad set 1 ad (hoặc 2 ad cùng angle khác hook, đọc ở cấp angle để giảm nhiễu do hook)
- Ngân sách/ad set/ngày ≈ **0.5–1× CPA hoà vốn**; chạy **3–4 ngày**; mỗi angle cần tiêu tổng ≥ **2–3× CPA hoà vốn** mới kết luận
- Không sửa ad trong lúc test (sửa = reset learning)

CPA hoà vốn = giá bán − giá vốn − ship − phí (%). Hỏi người dùng nếu chưa có số.

**Naming convention** (bắt buộc, `test_readout.py` dựa vào đây để gom theo angle):
```
<yymmdd>_A<n>-<angle-slug>_V<nn>_H<n>     ví dụ: 261104_A3-dau-lung-van-phong_V01_H1
```

**Rule đọc kết quả** (mặc định của `test_readout.py`):
| Tình huống | Quyết định |
|---|---|
| ≥3.000 hiển thị, hook rate <15%, 0 đơn | KILL sớm: 3s đầu không giữ người xem |
| Chi ≥1.5× BE, 0 đơn | KILL |
| Chi ≥1× BE, 0 ATC, CTR <0.7% | KILL |
| ≥3 đơn, CPA ≤ BE | **WINNER** |
| Có đơn, CPA ≤ BE, <3 đơn | TIỀM NĂNG: chạy thêm |
| CPA trong BE–1.5× BE | BORDERLINE: xem lại sau 1–2 ngày |

Chỉ số phụ để hiểu *vì sao* thua: hook rate (3s view/impr): người xem có dừng lại không · hold rate (thruplay/3s): angle có giữ được không · CTR link: lời hứa có đủ hấp dẫn không · ATC rate: PDP/offer có khớp không.

## 4. Lịch & bước tiếp

Ghi vào test plan: ngày launch, ngày đọc số (D+3, D+4), người phụ trách. Khi có số: export Ads Manager ở cấp **Ad** (cột: tên ad, chi tiêu, hiển thị, link click, 3s video plays, ThruPlays, ATC, purchases, purchase value) rồi chạy `/angle-lab:winner research/<slug> <file export>`.

Ghi mọi quyết định vào `creative/log.md` (ngày · việc · lý do).

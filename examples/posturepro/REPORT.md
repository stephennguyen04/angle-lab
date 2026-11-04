# SPY REPORT: PosturePro (đai chỉnh tư thế) · thị trường EU · 2026-11-04

> ⚠️ **Ví dụ minh hoạ trên dữ liệu giả lập** (fixture của repo), không phải brand thật. Mọi con số lấy từ các file trong thư mục này.

## ⚖️ Verdict: LÀM CÓ ĐIỀU KIỆN
1. **Angle "Đau lưng văn phòng" đã được thị trường xác nhận:** ad sống 119 ngày, 12 bản nhân, 1,85 triệu lượt tiếp cận EU; 3 creator khác nhau cùng làm reel, view gấp ~15 lần follower.
2. **Rủi ro sản phẩm cao (🔴):** 62% bình luận của người đã mua là tiêu cực; có 3 lỗi nghiêm trọng (2 vụ 3 tuần chưa nhận hàng, 1 vụ kích ứng da).
3. **Điều kiện để làm:** nguồn hàng có chất liệu không gây kích ứng, kho gần thị trường (ship dưới 7 ngày), bảng size rõ ràng.

## 1. Scale (`01-scale/scale_auto.md`)
5 ad active / 6 ad · 60% ad chạy Instagram · 2 ad có EU reach (tổng 2,27 triệu) · 1 ad hợp tác creator (@coach.linh). Hạng: 2 Long-Runner (≥60 ngày) · 1 Performer · 1 Solid. Đối thủ đang **scale một angle chính** và mới bắt đầu thử angle khác (quà tặng, chuyên gia).

## 2. Funnel & offer (`02-funnel/lp1/step1_summary.md`, `step1_bundle.png`)
Ad → **thẳng PDP** (không qua advertorial). Bundle: 1 Pack $49.99 · 2 Pack $79.99 (Most popular, $40/cái) · 3 Pack $99.99 (Best value, $33/cái). Có guarantee 30 ngày và freeship. **Điểm yếu:** FAQ không trả lời "dùng cho vẹo cột sống được không", cũng không có bảng size, dù cả hai đều là câu khách hỏi nhiều.

## 3. Mạnh nhất trên Meta Ads + Instagram (`01-scale/scoreboard.md`)
| Mã | Angle | Điểm | Ad lâu nhất | Bản nhân | Tiếp cận EU | View/follower | Muốn mua | Chê |
|---|---|---|---|---|---|---|---|---|
| A1 | Đau lưng văn phòng | **83** | 119 ngày | 18 | 2.270.000 | 15,3× | 33% | 33% |
| A2 | So sánh với nẹp cứng | 36 | 41 ngày | 3 | — | 6,1× | — | — |
| A3 | Quà tặng bố mẹ | 15 | 21 ngày | 1 | — | — | — | — |
| A4 | Tư thế xấu khi chụp ảnh | 12 | đã tắt | 2 | — | 1,4× | — | — |

**Top ad:** 9001 "Ngồi 8 tiếng mỗi ngày? Lưng bạn đang kêu cứu" (119 ngày, 12 bản nhân). **Top reel:** @coach.linh (bài hợp tác, 610K view, gấp 15 lần follower).

## 4. Hook video top (`03-videos/v1/ocr.txt`, `transcript.txt`, `hook_sheet.jpg`)
0,2s chữ "Ngồi 8 tiếng mỗi ngày?" → 2,0s "Lưng bạn đang kêu cứu" → 4,0s "Không phải do ghế!" → 6,5s "Giảm 50% hôm nay". Kiểu hook: **callout nỗi đau**, rồi phá niềm tin ("không phải do ghế"). Chữ xuất hiện ngay giây đầu, lời nói bắt đầu ở giây 1,1.

## 5. Tiếng nói khách hàng (`04-comments/report.md`): 🔴
13 bình luận / 3 nền tảng (Instagram, TikTok, Amazon). Khen 23% · chê + nghi ngờ 46% · hỏi 23%.
- **Chê:** ship 3 tuần / nghi lừa đảo (sev 3, 120 like) · kích ứng da vai (sev 3) · gãy sau 2 ngày, nhựa rẻ (sev 2) · chật, phải lấy lên 1 size.
- **Hỏi:** giá, link mua · dùng cho vẹo cột sống được không.
- **Khen:** "đeo 1 tuần đỡ hẳn" → đạn cho lời hứa 7 ngày.
- **Nghi ngờ:** "trên Temu có giá $5" (200 like) → cần lý do vì sao đáng tiền hơn.

## 6. Làm tốt hơn đối thủ ở đâu
| Điểm yếu đối thủ | Mình làm | Áp dụng ở |
|---|---|---|
| Ship 3 tuần | Kho EU, ship 3–5 ngày, ghi rõ trên ad | Offer, ad, PDP |
| Kích ứng da, nhựa rẻ | Lót vải cotton, khung bền hơn, quay cận chất liệu | Sản phẩm, video proof |
| So sánh với Temu | Video "vì sao không phải hàng $5" (chất liệu + bảo hành) | Angle phụ, PDP |
| Không có bảng size | Bảng size + video đo | PDP |

## 7. A1–A5 đưa sang test → `/angle-lab:angle-test`
A1 Đau lưng văn phòng (video tham chiếu ad 9001) · A2 So sánh với nẹp cứng · A3 Quà tặng bố mẹ · A4 Tư thế xấu khi chụp ảnh · A5 **khoảng trống từ bình luận:** "Chất liệu không kích ứng, không phải hàng Temu".

**Kết quả test sau đó** (`creative/02-readout.md`): **A1 WINNER** (CPA 15,53 so với hoà vốn 33,49; ROAS 3,22) → angle kim chỉ nam (`creative/angle.json`) → vòng nhân bản 1: đổi 3 hook (`creative/04-variants.csv`).

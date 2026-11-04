# Kết quả test angle

- CPA hoà vốn (BE): **33.49** · ROAS hoà vốn: **1.49** · rule winner: ≥3 đơn & CPA ≤ BE

## Theo ANGLE

| Angle | Ads | Chi | Hook% | Hold% | CTR% | CPC | ATC | Đơn | CPA | ROAS | Quyết định | Lý do |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 1 | 62.10 | 32.1 | 26.9 | 1.17 | 0.65 | 9 | 4 | 15.53 | 3.22 | **WINNER** | 4 đơn, CPA 15.53 ≤ BE 33.49 |
| A5 | 1 | 48.00 | 23.1 | 20.0 | 0.62 | 1.2 | 3 | 2 | 24.0 | 2.08 | **TIỀM NĂNG** | 2 đơn, CPA 24.0 ≤ BE nhưng chưa đủ 3 đơn → chạy thêm |
| A4 | 1 | 55.00 | 27.1 | 26.3 | 1.0 | 0.79 | 5 | 1 | 55.0 | 0.91 | **BORDERLINE** | CPA 55.0 > 1.5×BE nhưng mới chi 55.00 (< 3×BE), chạy thêm nếu hook/CTR tốt, không thì kill |
| A2 | 1 | 70.00 | 12.2 | 18.2 | 0.67 | 1.17 | 2 | 0 | — | — | **KILL** | hook rate 12.2% < 15.0% sau 9000 hiển thị → 3s đầu không giữ được người xem |
| A3 | 1 | 20.00 | 10.0 | 15.0 | 0.62 | 0.8 | 0 | 0 | — | — | **KILL** | hook rate 10.0% < 15.0% sau 4000 hiển thị → 3s đầu không giữ được người xem |

## Theo từng AD

| Ad | Angle | Chi | Hook% | Hold% | CTR% | ATC | Đơn | CPA | Quyết định |
|---|---|---|---|---|---|---|---|---|---|
| 261101_A1-dau-lung_V01_H1 | A1 | 62.10 | 32.1 | 26.9 | 1.17 | 9 | 4 | 15.53 | **WINNER** |
| 261101_A5-qua-tang_V01_H1 | A5 | 48.00 | 23.1 | 20.0 | 0.62 | 3 | 2 | 24.0 | **TIỀM NĂNG** |
| 261101_A4-tu-the-xau_V01_H1 | A4 | 55.00 | 27.1 | 26.3 | 1.0 | 5 | 1 | 55.0 | **BORDERLINE** |
| 261101_A2-so-sanh_V01_H1 | A2 | 70.00 | 12.2 | 18.2 | 0.67 | 2 | 0 | — | **KILL** |
| 261101_A3-chuyen-gia_V01_H1 | A3 | 20.00 | 10.0 | 15.0 | 0.62 | 0 | 0 | — | **KILL** |

## Dự đoán từ mạng xã hội vs kết quả thật

| Angle | Tên | Điểm MXH (hạng) | Hạng thật | Quyết định | Hook% | CPC thật | ROAS thật | Nhận xét |
|---|---|---|---|---|---|---|---|---|
| A1 | Đau lưng văn phòng | 100 (#1) | #1 | WINNER | 32.1 | 0.65 | 3.22 | đúng dự đoán |
| A2 | So sánh với nẹp cứng | 41 (#2) | #4 | KILL | 12.2 | 1.17 | — | bất ngờ: kém hơn dự đoán, xem lại cách dựng/hook trước khi bỏ angle |
| A3 | Quà tặng bố mẹ | 17 (#3) | #5 | KILL | 10.0 | 0.8 | — | bất ngờ: kém hơn dự đoán, xem lại cách dựng/hook trước khi bỏ angle |
| A4 | Tư thế xấu khi chụp ảnh | 14 (#4) | #3 | BORDERLINE | 27.1 | 0.79 | 0.91 | đúng dự đoán |

> Angle được mạng xã hội chuộng mà ad của mình thua → thường do **thực thi** (hook, dựng, offer/LP), chưa chắc angle sai. Angle thắng ngoài dự đoán → đáng giá nhất, vì đối thủ chưa khai thác.

## Kết luận

🏆 **Angle kim chỉ nam ứng viên: A1** (CPA 15.53, 4 đơn). Chạy `/angle-lab:winner` để mổ video thắng của angle này.

> ⚠️ Mẫu nhỏ (vài đơn) dao động mạnh. Winner thật phải giữ CPA khi tăng ngân sách/nhân bản.

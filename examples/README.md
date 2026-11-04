# Ví dụ output: PosturePro (dữ liệu giả lập)

Chạy toàn bộ quy trình trên fixture của repo để thấy mỗi bước tạo ra gì. **Không phải brand hay số liệu thật.**

| Bước | File | Là gì |
|---|---|---|
| Tổng hợp | [`posturepro/REPORT.md`](posturepro/REPORT.md) | Báo cáo cuối của `/angle-lab:spy` (AI viết từ các file bên dưới) |
| Scale | [`01-scale/scale_auto.md`](posturepro/01-scale/scale_auto.md) | Ad active, nhịp ra ad, hạng Long-Runner, % IG, EU reach, winner |
| Mạnh nhất Meta + IG | [`01-scale/scoreboard.md`](posturepro/01-scale/scoreboard.md) | Bảng điểm angle, Top ad, Top reel, A1–A5 |
| Persona | [`01-scale/audience.md`](posturepro/01-scale/audience.md) | Giới / tuổi / quốc gia người xem theo angle |
| Funnel | [`02-funnel/lp1/step1_summary.md`](posturepro/02-funnel/lp1/step1_summary.md) · `step1_fold.png` · `step1_bundle.png` | Tóm tắt trang + ảnh màn hình đầu + ảnh khu bundle |
| Video | [`03-videos/v1/`](posturepro/03-videos/v1/) | `hook_sheet.jpg` (12 khung 0–3s), `ocr.txt` (chữ có dấu), `transcript.txt` (lời) |
| Bình luận | [`04-comments/batches/batch_001.tsv`](posturepro/04-comments/batches/batch_001.tsv) → [`labels.txt`](posturepro/04-comments/labels.txt) → [`report.md`](posturepro/04-comments/report.md) | Batch AI đọc → nhãn mã ngắn AI viết → báo cáo |
| Test angle | [`creative/02-readout.md`](posturepro/creative/02-readout.md) | KILL / GIỮ / WINNER + so dự đoán MXH với kết quả thật |
| Nhân bản | [`creative/angle.json`](posturepro/creative/angle.json) · [`04-variants.csv`](posturepro/creative/04-variants.csv) | Angle kim chỉ nam + ma trận biến thể vòng 1 |
| Theo dõi | [`posturepro/monitor_latest.md`](posturepro/monitor_latest.md) | Thay đổi giữa 2 lần chụp |
| Thư viện hook | [`hooks-library/README.md`](hooks-library/README.md) | Hook đã chứng minh |

Lưu ý: `transcript.txt` ở đây nghe từ giọng đọc máy (espeak) nên sai nhiều; với giọng người thật, model `medium` cho kết quả tốt hơn.

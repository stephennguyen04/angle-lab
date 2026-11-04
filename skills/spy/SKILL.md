---
name: spy
description: Spy toàn diện 1 sản phẩm / đối thủ e-commerce. Đo mức scale ads (bao nhiêu ad active, ra ad mới đều không), mổ product page + bundle + funnel (thẳng PDP hay qua advertorial), lấy 5 video top phân tích angle/nỗi đau/hook 3s đầu, check họ bán trên những nền tảng nào và đọc bình luận từng nền tảng (khen/chê/hỏi → rủi ro sản phẩm & điểm để làm tốt hơn). Dùng khi người dùng nói "spy sản phẩm này", "phân tích đối thủ", "research product", "soi shop này", "mổ đối thủ", dán link sản phẩm/shop/Ad Library và muốn biết có nên làm không.
argument-hint: "<link sản phẩm | link shop | link Ad Library | tên brand>"
---

# /angle-lab:spy: Spy toàn diện 1 sản phẩm

Mục tiêu cuối: trả lời **"Có nên làm sản phẩm này không, và nếu làm thì đánh angle nào, làm tốt hơn đối thủ ở đâu?"**, dựa trên bằng chứng chứ không phải cảm giác.

## 0. Định vị script

Script của plugin nằm ở `${CLAUDE_PLUGIN_ROOT}/scripts/` (mọi skill con đều gọi theo đường dẫn này). Nếu đường dẫn không tồn tại (chạy ngoài plugin), tìm bằng
`find ~/.claude -path '*angle-lab*/scripts/ad_cadence.py' 2>/dev/null | head -1` rồi dùng thư mục đó thay thế. Mỗi lệnh Bash là shell mới, nên luôn ghi đường dẫn đầy đủ.

## 1. Lập hồ sơ & workspace

Từ input `$ARGUMENTS`, xác định (hỏi người dùng nếu thiếu thứ không tự tìm được):
- **Link sản phẩm** (PDP) và **domain shop**
- **Brand / tên Page Facebook** và **Page ID** (lấy trong Ad Library: `view_all_page_id=`; hoặc tìm theo tên brand)
- **Thị trường** (country code ISO-2 cho Ad Library, ví dụ US, AU, VN)

Tạo workspace `research/<product-slug>/` (slug ngắn, không dấu) và ghi `00-input.md`:
```
research/<slug>/
  00-input.md      01-scale/     02-funnel/     03-videos/     04-comments/
  REPORT.md        creative/     (creative/ dùng cho giai đoạn test angle → nhân bản)
```
Nếu workspace đã tồn tại → đọc lại các phần đã làm, chỉ làm tiếp phần còn thiếu, không ghi đè dữ liệu cũ (thêm hậu tố ngày nếu chạy lại).

## 2. Chạy 4 mảng phân tích, SONG SONG

Bốn mảng độc lập nhau, nên giao cho 4 agent của plugin chạy song song (một message, 4 lần gọi Agent), mỗi agent nhận đủ hồ sơ ở bước 1 + đường dẫn workspace + đường dẫn thư mục script:

| Mảng | Agent | Skill chi tiết | Output |
|---|---|---|---|
| Scale ads | `angle-lab:ad-scale-analyst` | `/angle-lab:ad-scale` | `01-scale/scale.md` + danh sách 5 video top |
| Product page / bundle / funnel | `angle-lab:funnel-analyst` | `/angle-lab:funnel` | `02-funnel/funnel.md` |
| Đa nền tảng + bình luận | `angle-lab:comment-miner` | `/angle-lab:comments` | `04-comments/insights.md` |

Mảng **5 video top** phụ thuộc vào danh sách video từ mảng Scale → sau khi `ad-scale-analyst` xong, chạy `angle-lab:video-angle-analyst` (hoặc tự làm theo `/angle-lab:top-videos`) → `03-videos/videos.md`. Có thể chạy song song 5 agent `video-angle-analyst`, mỗi agent 1 video, rồi tự tổng hợp bảng so sánh.

Nếu môi trường không có Agent tool, hãy làm tuần tự theo từng skill con.

**Mảng bình luận là quan trọng nhất**, đừng làm qua loa: phải đọc thật nhiều bình luận trên MỌI nền tảng họ bán, không chỉ vài cái đầu.

## 3. Tổng hợp REPORT.md

Đọc 4 file output và viết `research/<slug>/REPORT.md` theo `${CLAUDE_PLUGIN_ROOT}/templates/spy-report.md`. Bắt buộc có:

1. **Verdict 1 dòng:** LÀM / LÀM CÓ ĐIỀU KIỆN / BỎ, kèm 3 lý do chính.
2. **Scale:** số ad active, ad mới 7/14/30 ngày, nhịp ra ad, ad sống lâu nhất. Kết luận: sản phẩm đang lên, đang đỉnh hay đang chết.
3. **Funnel & offer:** sơ đồ funnel (ad → advertorial? → PDP → upsell), giá, bundle bậc thang, giá/đơn vị, guarantee, điểm yếu của PDP.
4. **5 angle của đối thủ:** bảng (nỗi đau, persona, hook 3s, kiểu hook, format, bằng chứng), đánh dấu angle họ nhân bản nhiều nhất = angle đã được thị trường xác nhận.
5. **Tiếng nói khách hàng:** nền tảng nào, tỉ lệ khen/chê/hỏi, top chê (rủi ro), top hỏi (FAQ/objection), top khen (đạn cho creative). Mức rủi ro 🔴🟡🟢.
6. **Rủi ro sản phẩm** (từ bình luận + funnel + policy): hàng lỗi, ship lâu, claim y tế/sức khoẻ dễ bị Meta reject, IP/trademark.
7. **Cơ hội làm tốt hơn đối thủ:** mỗi điểm chê là một cơ hội (sản phẩm, offer, PDP, CSKH, creative). Ghi cụ thể: làm gì, ở đâu.
8. **Đề xuất 5 angle để test** → chuyển sang `/angle-lab:angle-test`.

Mọi con số phải dẫn nguồn (file trong workspace). Phần nào thiếu dữ liệu thì ghi rõ "chưa có dữ liệu + cách lấy", không bịa.

## 4. Kết thúc

Trả lời người dùng: verdict, 5 phát hiện đáng giá nhất, đường dẫn REPORT.md, và bước tiếp theo: `/angle-lab:angle-test research/<slug>`.

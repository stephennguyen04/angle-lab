---
name: funnel
description: Mổ product page, offer/bundle và funnel của đối thủ, cụ thể là ad trỏ thẳng trang sản phẩm hay qua advertorial/listicle/quiz/VSL, PDP dựng thế nào (thứ tự section, hình, review, guarantee), bundle bán ra sao (giá bậc thang, giá/đơn vị, quà, upsell), app nào đang dùng. Dùng khi hỏi "product page dựng thế nào", "bundle bán ra sao", "funnel đi đâu", "có advertorial không", "trang sản phẩm đối thủ".
argument-hint: "<link sản phẩm hoặc link đích của ad>"
---

# /angle-lab:funnel: Product page, bundle, funnel

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/`. Lưu vào `research/<slug>/02-funnel/`.

## 1. Lấy đúng điểm vào funnel

Đừng chỉ mở link sản phẩm. Lấy **landing URL thật từ ad** (từ `01-scale/scale.json` → `top_landing_urls`). Nếu ad trỏ về nhiều URL khác nhau thì capture top 2–3 URL (đối thủ hay test nhiều LP).

## 2. Capture như khách thật (mobile)

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/capture_page.cjs" "<landing_url>" research/<slug>/02-funnel/lp1 --follow-cta
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/shopify_product.py" "<link PDP>" --out research/<slug>/02-funnel/product.json
```
- `capture_page.cjs` lưu screenshot full trang, text, heading, CTA, giá, marker (advertorial, bundle, guarantee, countdown, review app…), app nhận diện được, và `funnel.json` (redirect chain + loại trang từng bước). `--follow-cta` tự đi tiếp từ advertorial → PDP.
- `shopify_product.py` đọc `/products/<handle>.js`: variants, giá, giá gạch, giảm %, giá/đơn vị nếu bundle nằm trong variant.
- **XEM screenshot** (Read file .png), vì nhiều bundle hiện bằng widget, chỉ thấy trong ảnh.
- Không có Playwright thì dùng WebFetch cho text + yêu cầu người dùng gửi screenshot.

## 3. Phân tích → `02-funnel/funnel.md`

**a. Funnel shape**: vẽ dạng `Ad → [Advertorial "..."] → PDP → Cart drawer upsell → Checkout → Post-purchase upsell`.
- Đi thẳng PDP: sản phẩm dễ hiểu, demo trong video là đủ, chiến lược impulse.
- Qua advertorial/listicle: sản phẩm cần giáo dục / có cơ chế mới / giá cao / angle sức khoẻ. Ghi tiêu đề advertorial, góc kể (báo chí, câu chuyện cá nhân, "5 lý do"), độ dài, cách chuyển sang PDP.
- Quiz / VSL: ghi rõ cấu trúc.

**b. PDP teardown**: liệt kê section theo thứ tự từ trên xuống (above the fold có gì: headline, sub, ảnh/GIF, rating, bullet lợi ích, giá, bundle, CTA, trust badge), rồi các section dưới: so sánh "us vs them", how it works, UGC/review, FAQ, guarantee, sticky ATC. Đánh giá: headline nói lợi ích hay tính năng? Có khớp angle trong ad không (message match)?

**c. Offer & bundle**: bảng các tier

| Tier | Giá | Giá gạch | Giảm | Giá/đơn vị | Quà/freeship | Badge |
|---|---|---|---|---|---|---|

Ghi: tier nào được đẩy làm mặc định ("Most popular"), cách neo giá, upsell/cross-sell, subscription, guarantee (bao nhiêu ngày), BNPL, ước AOV.

**d. Tech & app**: page builder, review app, bundle app, upsell app. Chi tiết này giúp mình dựng lại nhanh.

**e. Điểm yếu & cơ hội**: chỗ nào PDP yếu (load chậm, thiếu FAQ cho câu hỏi lặp lại trong bình luận, review giả, giá/đơn vị không hấp dẫn, guarantee mập mờ). Đối chiếu với `04-comments` nếu đã có: câu hỏi khách hay hỏi mà PDP không trả lời = cơ hội.

Không sao chép nguyên văn copy/hình của đối thủ vào trang của mình; chỉ học cấu trúc.

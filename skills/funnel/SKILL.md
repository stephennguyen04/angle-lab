---
name: funnel
description: Mổ product page, bundle/offer, funnel đối thủ (thẳng PDP hay qua advertorial/listicle/quiz/VSL), app dùng, điểm yếu PDP. Dùng khi "product page dựng thế nào", "bundle bán ra sao", "funnel đi đâu".
argument-hint: "<link sản phẩm | link đích của ad>"
---

# /angle-lab:funnel

Lưu vào `research/<slug>/02-funnel/`. Lấy **landing URL thật từ ad** (`01-scale/scale.json` → `top_landing_urls`), nếu nhiều URL thì capture 2–3 URL đầu.

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/capture_page.cjs" "<landing_url>" research/<slug>/02-funnel/lp1 --follow-cta
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/shopify_product.py" "<link PDP>" --out research/<slug>/02-funnel/product.json
```
**Đọc theo thứ tự (tiết kiệm token):** `stepN_summary.md` → `stepN_fold.png` (màn hình đầu) → `stepN_bundle.png` (khu bundle). Chỉ mở `stepN.png` (toàn trang) hoặc `stepN.txt` khi cần một chi tiết. `shopify_product.py` cho variants, giá, giá gạch, giá/đơn vị.

## Viết `funnel.md`
1. **Funnel:** `Ad → [advertorial "…"] → PDP → upsell → checkout`. Đi thẳng PDP = sản phẩm dễ hiểu, mua bốc đồng. Qua advertorial = cần giáo dục, cơ chế mới, giá cao. Ghi tiêu đề và góc kể.
2. **PDP theo thứ tự section:** above the fold (headline, ảnh, rating, bullet, giá, bundle, CTA, trust) → các section dưới. Headline nói lợi ích hay tính năng? Có khớp angle của ad không?
3. **Bảng bundle:** tier · giá · giá gạch · giảm · giá/đơn vị · quà/freeship · badge. Thêm: tier mặc định, upsell, subscription, guarantee, BNPL, ước AOV.
4. **App:** page builder, review, bundle, upsell.
5. **Điểm yếu & cơ hội:** đối chiếu với `04-comments` (câu hỏi khách hay hỏi mà PDP không trả lời).

Chỉ học cấu trúc, không chép copy hay hình của đối thủ.

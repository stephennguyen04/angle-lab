---
name: comments
description: Tìm đối thủ bán trên nền tảng nào rồi đọc và gắn nhãn TỪNG bình luận/review (khen/chê/hỏi, chủ đề, mức nghiêm trọng, đã mua chưa) → rủi ro sản phẩm, FAQ, proof, điểm làm tốt hơn. Dùng khi "đọc bình luận", "khách chê gì khen gì hỏi gì", "review đối thủ".
argument-hint: "<research/<slug> | brand + link>"
---

# /angle-lab:comments

**Phần quan trọng nhất.** Đọc rộng (mọi nền tảng), đọc hết (mọi bình luận, kể cả reply), gắn nhãn xong mới kết luận. Lưu vào `research/<slug>/04-comments/`.

## 1. Nền tảng → `platforms.md`
WebSearch song song: `"<brand>"` + tiktok / tiktok shop / site:instagram.com / site:youtube.com / site:amazon.<tld> / site:trustpilot.com / site:reddit.com / scam OR legit / shopee / lazada; tên sản phẩm generic trên AliExpress/Temu/Amazon (cho biết chất lượng hàng gốc). Chỉ tính "có bán" khi thấy shop/listing thật.

## 2. Thu thập → `raw/`
Facebook/Instagram: **`/angle-lab:apify`** (lấy cả trả lời lồng) hoặc `ig_collect.py`. TikTok/YouTube: `yt-dlp --write-comments`. Amazon/Trustpilot/Shopee: WebFetch trang review (1–3 sao và 5 sao). Reddit: URL + `.json`. Chi tiết: `reference.md`. Ưu tiên bài đông tương tác và **post của ad sống lâu** (nhiều người đã mua).

## 3. Chuẩn hoá
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/comments.py" prep --out-dir research/<slug>/04-comments -i facebook:<file> -i instagram:<file> -i tiktok:<file.info.json> -i amazon:<file.csv>
```
Script dedupe, bỏ bình luận chỉ có emoji, băm tên tác giả, **gộp bình luận gần trùng** (chỉ gắn nhãn 1 lần), và ghi batch **TSV gọn**: `batches/batch_XXX.tsv` (`id · like · ×trùng · gợi_ý · nội dung`).

## 4. Gắn nhãn từng dòng trong batch → `labels.txt`
Nhiều batch thì chia cho nhiều agent `angle-lab:comment-miner`, mỗi agent ghi `labels/batch_XXX.txt`. Mỗi id đúng **1 dòng mã ngắn** (đỡ tốn token đầu ra):
```
c00012 C shi,scam 3 b 3 tuần chưa nhận hàng
c00013 Q pri - -
c00014 P eff 0 b đeo 1 tuần đỡ đau
```
`id LOẠI chủ_đề sev mua [ghi chú ngắn]`
- LOẠI: P khen · C chê · Q hỏi · I muốn mua/đã đặt · S nghi ngờ (scam, hàng Temu, "AI ad") · T tag bạn · O khác
- Chủ đề: eff qua pri shi siz use saf scam sup des sme dur comp pack oth (nhiều chủ đề nối bằng dấu phẩy)
- sev (chỉ chê/nghi ngờ): 0 cằn nhằn · 1 không hài lòng · 2 lỗi thật · **3** không nhận hàng / lừa đảo / hại sức khoẻ / hỏng ngay
- mua: b đã mua · n chưa · - không rõ. Ghi chú chỉ khi có chi tiết đắt giá (con số, bộ phận hỏng, thời gian).

Gợi ý trong batch chỉ để tham khảo. Bắt sarcasm, seeding (khen chung chung, lặp mẫu), khiếu nại ẩn trong câu hỏi ("có ai nhận được hàng chưa?" = Q scam 2), reply của shop.

## 5. Tổng hợp
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/comments.py" report --out-dir research/<slug>/04-comments
```
Output in tóm tắt; `report.md` có top chê/hỏi/khen kèm quote. Còn dòng chưa gắn nhãn thì quay lại bước 4.

## 6. `insights.md`
Tổng quan (bao nhiêu bình luận / nền tảng) · **Chê gì** (lỗi sản phẩm = lý do có thể BỎ; lỗi vận hành = mình làm tốt hơn được; nghi ngờ uy tín = xử lý bằng proof) · **Hỏi gì** (objection → câu trả lời cho PDP, ad, CSKH) · **Khen gì** (đạn cho creative) · 10–20 cụm từ nguyên văn của khách · bảng *điểm chê/hỏi → mình làm gì → áp dụng ở đâu* · angle gợi ra từ bình luận · verdict 🔴🟡🟢. Quote giữ nguyên văn, không ghi tên người bình luận.

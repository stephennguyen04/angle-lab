---
name: comment-miner
description: Tìm nền tảng đối thủ bán và đọc/gắn nhãn TỪNG bình luận (khen/chê/hỏi, chủ đề, sev, đã mua) → rủi ro, FAQ, proof. Dùng trong /angle-lab:spy, /angle-lab:comments, hoặc gắn nhãn song song từng batch.
---

Làm đúng `${CLAUDE_PLUGIN_ROOT}/skills/comments/SKILL.md`.
- **Chế độ gắn nhãn batch** (khi được giao danh sách batch): đọc từng `batches/batch_XXX.tsv`, ghi `labels/batch_XXX.txt` đúng định dạng mã ngắn `id LOẠI chủ_đề sev mua [ghi chú]`, mỗi id 1 dòng, không bỏ dòng nào. Ghi chú chỉ khi có chi tiết đắt giá.
- Đọc từng bình luận, không lấy mẫu; bắt sarcasm, seeding, khiếu nại ẩn trong câu hỏi. Không ghi tên người bình luận.
- Trả về ≤15 dòng: số bình luận/nền tảng, tỉ lệ khen/chê/hỏi, top 5 chê (kèm sev), top 5 hỏi, top 5 khen, mức rủi ro 🔴🟡🟢.

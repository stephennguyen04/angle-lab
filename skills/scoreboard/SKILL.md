---
name: scoreboard
description: Chấm điểm từng ANGLE của đối thủ chỉ bằng dữ liệu công khai trên mạng xã hội (view, like, comment, share, save trên TikTok/Instagram/Facebook/YouTube, số creator cùng đánh angle, % bình luận muốn mua hoặc chê, cộng tín hiệu công khai từ Ad Library), rồi chọn A1–A5 để đưa sang bước test angle. Dùng khi hỏi "angle nào của đối thủ mạnh nhất", "xếp hạng angle", "chọn angle để test", "angle nào viral", hoặc là bước cuối của /angle-lab:spy.
argument-hint: "<research/<slug>>"
---

# /angle-lab:scoreboard: Xếp hạng angle bằng dữ liệu mạng xã hội → A1–A5

Chỉ dùng **số nhìn thấy công khai**. Không ước tính CPC, ROAS hay chi tiêu của đối thủ, vì những số đó không công khai và đoán ra chỉ gây hiểu sai. Số CPC/ROAS duy nhất trong quy trình là số **thật** từ ad của chính bạn, ở bước test.

## Tín hiệu được dùng

| Tín hiệu | Lấy ở đâu | Vì sao có giá trị | Trọng số |
|---|---|---|---|
| **Tỉ lệ share** (share/view) | TikTok, IG, FB, YouTube | Người xem gửi cho người khác = angle chạm đúng nỗi đau | 20% |
| **Tỉ lệ tương tác** (like+comment+share+save)/view | như trên | Mức độ angle giữ được người xem | 15% |
| **View trung vị / bài** | như trên | Độ phủ, tránh để 1 bài viral kéo cả angle | 15% |
| **% bình luận muốn mua / hỏi giá, link** | `/angle-lab:comments`, nối theo URL bài | Tín hiệu mua gần nhất có thể quan sát | 15% |
| **Số creator khác nhau cùng đánh angle** | tên tài khoản đăng bài | Affiliate/UGC tự copy angle = angle bán được | 10% |
| **Ad chạy lâu nhất** | Ad Library (công khai) | Đối thủ giữ ad lâu = ad ổn | 15% |
| **Ad active + ad mới 30 ngày** | Ad Library | Đối thủ đang đổ thêm vào angle này | 10% |
| **% bình luận chê / nghi ngờ** | `/angle-lab:comments` | **Trừ điểm**: tối đa −50% nếu toàn chê | phạt |

Thiếu nguồn nào thì script tự bỏ tín hiệu đó và chia lại trọng số. Cột "Tin cậy" thể hiện dữ liệu dày hay mỏng.

## 1. Gom bài đăng theo angle → `01-scale/posts.csv`

Với mỗi angle đã rút ra ở `03-videos/videos.md`, tìm **mọi bài** dùng angle đó, không chỉ của brand:
- Tài khoản chính của brand trên TikTok / IG / FB / YouTube
- Video affiliate, TikTok Shop, KOC/UGC đăng cùng sản phẩm (tìm theo tên sản phẩm, hashtag, nhạc/âm thanh của video gốc)
- Spark ads / bài organic trùng creative với ad trong Ad Library

Lấy số:
```bash
yt-dlp --skip-download --write-info-json -o "research/<slug>/01-scale/posts/%(extractor)s_%(id)s" <url>
```
File `.info.json` có `view_count, like_count, comment_count, repost_count, uploader, channel_follower_count`. Instagram/Facebook thường cần đăng nhập: đọc số hiển thị trên bài (hoặc nhờ người dùng chụp màn hình/export) rồi nhập tay.

Ghi CSV: `angle,angle_name,platform,url,creator,views,likes,comments,shares,saves,followers`.
- Mỗi bài gán **1 angle**, dựa trên nội dung video (xem hook + nỗi đau), không dựa vào caption.
- Ghi `url` đầy đủ để nối với bình luận đã tải ở bước comments.

## 2. (Tuỳ chọn) Gán ad Ad Library vào angle → `01-scale/angle_map.csv`

`ad_id,angle,angle_name` cho toàn bộ ad trong `01-scale/ads_raw.json` (theo ad copy, video, landing page; ad cùng creative thì cùng angle; không chắc thì gán `unclear`).

## 3. Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/angle_scoreboard.py" \
  --posts research/<slug>/01-scale/posts.csv \
  --comments-dir research/<slug>/04-comments \
  --ads research/<slug>/01-scale/ads_raw.json --angle-map research/<slug>/01-scale/angle_map.csv \
  --assign 5 --out-md research/<slug>/01-scale/scoreboard.md --out-json research/<slug>/01-scale/scoreboard.json
```
Có thể thêm `--posts <slug>:<file>.info.json` cho từng bài thay vì CSV.

## 4. Diễn giải & chốt A1–A5

Dưới bảng của script, viết thêm:
- Angle nào **lan nhất** (share cao, nhiều creator), angle nào **ra đơn nhất** (nhiều bình luận muốn mua), và hai nhóm này có trùng nhau không.
- Angle **bị chê nhiều**: vẫn có thể test, nhưng video phải xử lý objection đó ngay trong script.
- Angle **viral mà không ai hỏi mua**: cẩn thận, giải trí tốt nhưng chưa chắc bán được.
- **Khoảng trống:** angle khách nhắc nhiều trong bình luận nhưng chưa ai làm video. Không có điểm vì chưa có bài nào, nhưng có thể dành **1 trong 5 slot** cho nó (sửa `test_code` trong `scoreboard.json` cho khớp).
- Chốt bảng **A1–A5**: mã · angle · điểm · tín hiệu mạnh nhất · video tham chiếu (bài có share cao nhất của angle đó). Đây là input bắt buộc của `/angle-lab:angle-test`.

Ngân sách test vẫn **chia đều** 5 angle. Điểm chỉ dùng để *chọn* angle, không dùng để chia tiền.

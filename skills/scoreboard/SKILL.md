---
name: scoreboard
description: Tìm angle, ad và reel MẠNH NHẤT của đối thủ trên Meta Ads + Instagram chỉ bằng số công khai (ad sống lâu, bản nhân, EU reach, % IG, hợp tác creator, view/follower, % muốn mua/chê) → Top ad, Top bài IG, chọn A1–A5. Dùng khi "angle/ad/reel nào mạnh nhất", "chọn angle để test".
argument-hint: "<research/<slug>>"
---

# /angle-lab:scoreboard

Chỉ dùng số công khai, **không ước tính CPC/ROAS của đối thủ**. Mặc định `--focus meta-ig` (bỏ bài/ad ngoài Facebook/Instagram; `--focus all` để tính cả). Trọng số và ý nghĩa từng tín hiệu: `reference.md`.

## 1. Ad Meta
`01-scale/ads_raw.json` (từ `/angle-lab:ad-scale`) + gán **toàn bộ** ad vào angle → `01-scale/angle_map.csv` (`ad_id,angle,angle_name`; ad cùng creative thì cùng angle; không chắc thì `unclear`). Gán dựa trên ad copy, có thể chạy theo lô.

## 2. Bài Instagram → `01-scale/ig/posts.csv`
```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"; O=research/<slug>/01-scale/ig
python3 "$S/ig_collect.py" profile <brand_ig> --reels-only --limit 80 --comments 200 --login <user> --out-dir $O
python3 "$S/ig_collect.py" tagged <brand_ig> --limit 80 --login <user> --out-dir $O        # UGC / affiliate
python3 "$S/ig_collect.py" urls <reel của creator trong ad hợp tác> … --out-dir $O
```
Không có instaloader/đăng nhập: `apify_fetch.py ig-posts <URL profile>` → `ig_collect.py import <items.json>`. Các lần chạy gộp vào cùng posts.csv và giữ angle đã gán. Gán cột `angle` theo nội dung video (hook + nỗi đau), không theo caption. Bình luận IG đưa qua `/angle-lab:comments`.

## 3. Chạy
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/angle_scoreboard.py" --posts research/<slug>/01-scale/ig/posts.csv \
  --comments-dir research/<slug>/04-comments --ads research/<slug>/01-scale/ads_raw.json --angle-map research/<slug>/01-scale/angle_map.csv \
  --assign 5 --top 10 --out-md research/<slug>/01-scale/scoreboard.md --out-json research/<slug>/01-scale/scoreboard.json
```
Output in bảng angle + top 3 ad/bài; bản đầy đủ trong `scoreboard.md`.

## 4. Diễn giải & chốt A1–A5
- Angle **đối thủ đổ tiền nhiều nhất** (Meta) so với angle **lan tự nhiên mạnh nhất** (IG). Trùng nhau = chắc nhất. IG mạnh mà ít ad = cơ hội đối thủ chưa khai thác.
- Creator trong ad hợp tác → gợi ý nhân vật cho bước nhân bản.
- Angle bị chê nhiều vẫn test được, nhưng video phải xử lý objection. Angle viral mà không ai hỏi mua thì cẩn thận.
- Có thể dành 1 slot cho angle khoảng trống từ bình luận (sửa `test_code` trong `scoreboard.json`).
- Chốt bảng A1–A5: mã · angle · điểm · tín hiệu mạnh nhất · video tham chiếu (ad mạnh nhất của angle, không có thì bài IG mạnh nhất). Ngân sách test chia đều.

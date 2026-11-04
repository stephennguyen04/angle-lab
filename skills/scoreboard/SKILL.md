---
name: scoreboard
description: Tìm angle, ad và bài MẠNH NHẤT của đối thủ trên Meta Ads + Instagram chỉ bằng dữ liệu công khai. Phía Meta Ads gồm ad sống lâu, bản nhân, lượt tiếp cận EU, % ad chạy Instagram, ad hợp tác creator. Phía Instagram gồm view/follower của Reels, tương tác, bài UGC/affiliate, % bình luận muốn mua hoặc chê. Kết quả là bảng điểm angle, Top 10 ad, Top 10 bài IG, rồi chọn A1–A5 để test. Dùng khi hỏi "angle nào mạnh nhất", "ad nào mạnh nhất trên Meta", "reel nào mạnh nhất", "tìm mạnh nhất trên insta và meta ads", "chọn angle để test", hoặc là bước cuối của /angle-lab:spy.
argument-hint: "<research/<slug>>"
---

# /angle-lab:scoreboard: Angle / ad / bài mạnh nhất trên Meta Ads + Instagram → A1–A5

Chỉ dùng **số công khai**. Không ước tính CPC, ROAS hay chi tiêu của đối thủ. Mặc định `--focus meta-ig`: chỉ chấm bài Instagram/Facebook và ad có placement Facebook/Instagram (`--focus all` để tính cả TikTok/YouTube).

## Tín hiệu & trọng số (focus meta-ig)

| Nhóm | Tín hiệu | Vì sao có giá trị | Trọng số |
|---|---|---|---|
| Meta Ads | Ad active chạy lâu nhất | Không ai giữ ad lỗ nhiều tuần | 15% |
| Meta Ads | Ad active + ad mới 30 ngày | Đối thủ đang đổ thêm vào angle này | 10% |
| Meta Ads | Tổng bản nhân ("N ads use this creative") | Nhân bản = đang scale creative đó | 8% |
| Meta Ads | **Lượt tiếp cận EU** | Tín hiệu công khai gần chi tiêu nhất (chỉ ad phân phối ở EU/UK/Brazil) | 12% |
| Meta Ads + IG | **Hợp tác creator** (Paid partnership ad / bài) | Đối thủ trả tiền creator = đã tin angle | 5% |
| Instagram | **View / follower** của Reels | Reel vượt tập follower = angle lan tự nhiên | 12% |
| Instagram | Tỉ lệ tương tác (like+comment+share+save)/view | Angle giữ được người xem | 10% |
| Instagram | % bình luận muốn mua / hỏi giá, link | Tín hiệu mua gần nhất quan sát được | 12% |
| Instagram | Số creator khác nhau cùng đánh angle | UGC/affiliate tự copy = angle bán được | 8% |
| Instagram | View trung vị (min–max trên thang log) | Độ phủ, không để 1 reel viral kéo cả angle | 5% |
| Instagram | Share (nếu hiển thị) | Gửi cho người khác = chạm đúng nỗi đau | 3% |
| Phạt | % bình luận chê / nghi ngờ | Trừ tối đa −50% | — |

Thiếu nguồn nào thì script tự bỏ tín hiệu đó và chia lại trọng số; cột "Tin cậy" thể hiện dữ liệu dày hay mỏng.

## 1. Ad Meta → `01-scale/ads_raw.json` + `angle_map.csv`

- Lấy ad theo `/angle-lab:ad-scale` (HAR / MCP / scraper → `adlib_parse.py`). Đối thủ có bán ở EU/UK thì lấy thêm EU reach.
- Gán **toàn bộ** ad vào angle: `ad_id,angle,angle_name` (căn cứ ad copy, video, landing; ad cùng creative thì cùng angle; không chắc thì `unclear`).

## 2. Bài Instagram → `01-scale/ig/posts.csv`

Thu thập đủ 4 nguồn:
```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"
python3 "$S/ig_collect.py" profile <brand_ig> --reels-only --limit 80 --comments 200 --login <user> --out-dir research/<slug>/01-scale/ig
python3 "$S/ig_collect.py" tagged  <brand_ig> --limit 80 --login <user> --out-dir research/<slug>/01-scale/ig       # UGC / affiliate tag brand
python3 "$S/ig_collect.py" urls <link reel của creator trong ad hợp tác> … --out-dir research/<slug>/01-scale/ig
python3 "$S/ig_collect.py" hashtag <hashtag sản phẩm> --limit 60 --login <user> --out-dir research/<slug>/01-scale/ig
```
- Không có instaloader/đăng nhập: nhờ người dùng chạy actor Instagram trên Apify (profile/reels/hashtag) rồi `ig_collect.py import <file>.json`. CSV tự làm cũng được, miễn đủ cột.
- Các lần chạy **gộp vào cùng posts.csv** và giữ cột angle đã gán.
- AI gán cột `angle` cho từng bài dựa trên **nội dung video** (hook + nỗi đau), không dựa vào caption.
- Bình luận IG: `comments.py prep -i instagram:research/<slug>/01-scale/ig/comments/<code>.json …`, gắn nhãn như `/angle-lab:comments` để có % muốn mua / chê theo angle.

## 3. Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/angle_scoreboard.py" \
  --posts research/<slug>/01-scale/ig/posts.csv --comments-dir research/<slug>/04-comments \
  --ads research/<slug>/01-scale/ads_raw.json --angle-map research/<slug>/01-scale/angle_map.csv \
  --assign 5 --top 10 --out-md research/<slug>/01-scale/scoreboard.md --out-json research/<slug>/01-scale/scoreboard.json
```
Xuất ra: bảng điểm angle, **Top 10 ad mạnh nhất trên Meta**, **Top 10 bài Instagram mạnh nhất**, và A1–A5.

## 4. Diễn giải & chốt A1–A5

Dưới bảng của script, viết thêm:
- Angle **đối thủ đổ tiền nhiều nhất** (ad sống lâu, bản nhân, EU reach) so với angle **lan tự nhiên mạnh nhất trên IG** (view/follower, số creator). Trùng nhau thì đó là angle chắc nhất. Lệch nhau: angle IG mạnh mà ad ít có thể là **cơ hội** đối thủ chưa khai thác bằng ads.
- **Hợp tác creator:** creator nào, angle nào. Đây là gợi ý persona/nhân vật cho bước nhân bản.
- Angle bị chê nhiều: vẫn test được, nhưng video phải xử lý objection đó.
- Angle viral mà không ai hỏi mua: giải trí tốt, chưa chắc bán được.
- **Khoảng trống:** angle khách nhắc nhiều trong bình luận nhưng chưa ai làm video. Có thể dành 1 slot (sửa `test_code` trong `scoreboard.json`).
- Chốt **A1–A5**: mã · angle · điểm · tín hiệu mạnh nhất · **video tham chiếu** (ưu tiên ad mạnh nhất của angle trong Top ad, không có thì bài IG mạnh nhất). Đây là input bắt buộc của `/angle-lab:angle-test`.

Ngân sách test vẫn **chia đều**. Điểm chỉ dùng để *chọn* angle, không dùng để chia tiền.

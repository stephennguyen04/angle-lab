---
name: scoreboard
description: Chấm điểm từng ANGLE của đối thủ với CPC ước tính, ROAS sàn suy ra và proof score (độ bền ad, số ad + bản nhân, ad mới 30 ngày, tương tác), rồi chọn A1–A5 kèm KPI kỳ vọng để đưa sang bước test angle. Dùng khi hỏi "CPC ROAS của mỗi angle", "angle nào của đối thủ ra tiền nhất", "xếp hạng angle", "chọn angle để test", hoặc là bước cuối của /angle-lab:spy.
argument-hint: "<research/<slug>> [AOV] [giá vốn] [ship] [CPC chuẩn]"
---

# /angle-lab:scoreboard: CPC / ROAS theo từng angle → chọn A1–A5

## Nói thẳng về dữ liệu

**CPC, ROAS, chi tiêu thật của đối thủ không công khai.** Ad Library chỉ có ngày chạy, trạng thái, số bản nhân và nội dung. Vì vậy bảng điểm này **không bao giờ** được trình bày con số ước tính như số thật. Mỗi con số đều kèm nguồn và độ tin cậy:

| Chỉ số | Cách có | Ý nghĩa |
|---|---|---|
| **ROAS sàn suy ra** | Angle có ad active ≥30 ngày ⇒ ROAS ≥ ROAS hoà vốn (AOV ÷ (AOV − giá vốn − ship − phí)) | Không ai đốt tiền 1 tháng cho ad lỗ. Đây là **cận dưới**, không phải ROAS thật |
| **CPC ước tính** | CPC chuẩn ÷ chỉ số tương tác của angle (kẹp 0.6–1.6), khoảng ±25% | Angle được tương tác nhiều thường có CTR cao hơn nên CPC thấp hơn |
| **Số từ tool spy** | Export của PiPiAds / Minea / BigSpy… (`est_spend, est_cpc, est_roas`) | Vẫn là ước tính của tool, ghi rõ nguồn |
| **Proof score 0–100** | Độ bền ad 35% · ad active + bản nhân 25% · ad mới 30 ngày 15% · tương tác 15% · chi tiêu ước tính 10% | Thị trường đã xác nhận angle này tới mức nào |

**CPC chuẩn** lấy theo thứ tự ưu tiên: (1) CPC thật trong tài khoản của bạn cho sản phẩm/ngách tương tự (MCP Meta Ads: `ads_get_ad_entities` với metric cpc), (2) benchmark ngành (MCP Meta Ads: `ads_insights_industry_benchmark`), (3) người dùng cung cấp. Không có thì để trống cột CPC, **không đoán**.

## 1. Gắn mỗi ad đối thủ vào 1 angle → `01-scale/angle_map.csv`

Khác bước top-videos (chỉ mổ 5 video), ở đây phải gán **toàn bộ** ad trong `01-scale/ads_raw.json`:
- Dùng danh sách angle đã rút ra ở `03-videos/videos.md` làm bộ nhãn; ad không khớp angle nào thì tạo angle mới (slug ngắn, không dấu).
- Căn cứ: ad copy (body), headline, thumbnail/video nếu có, landing page. Ad cùng creative (bản nhân) thì cùng angle.
- Định dạng: `ad_id,angle,angle_name` (ví dụ `1234,dau-lung-van-phong,Đau lưng văn phòng`).
- Không chắc thì gán `unclear`, đừng ép.

## 2. Gom tương tác (tuỳ chọn nhưng nên có) → `01-scale/posts.csv`

Cùng creative thường được đăng organic hoặc Spark trên TikTok/IG/YouTube. Lấy `view_count, like_count, comment_count, repost_count` từ file `.info.json` mà bước comments đã tải bằng yt-dlp, rồi ghi CSV `angle,platform,url,views,likes,comments,shares`. Có thể truyền thẳng `--posts <slug>:<file>.info.json`.

## 3. Chạy

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/angle_scoreboard.py" \
  --ads research/<slug>/01-scale/ads_raw.json --angle-map research/<slug>/01-scale/angle_map.csv \
  --posts research/<slug>/01-scale/posts.csv [--spy-tool <export tool spy>.csv] \
  --aov <AOV đối thủ từ 02-funnel> --cogs <giá vốn của bạn> --shipping <ship> --fees-pct 5 --bench-cpc <CPC chuẩn> \
  --assign 5 --out-md research/<slug>/01-scale/scoreboard.md --out-json research/<slug>/01-scale/scoreboard.json
```
AOV lấy từ tier bundle mặc định trong `02-funnel/funnel.md` (không phải giá 1 cái).

## 4. Diễn giải & chọn A1–A5

Dưới bảng của script, viết thêm:
- Angle nào **đã được xác nhận** (proof cao, tin cậy Cao), angle nào **đang được đổ tiền mới** (nhiều ad mới 30 ngày, nghĩa là đối thủ đang scale nó ngay lúc này).
- Angle **đang chết** (đã tắt hết, không có ad mới): không đưa vào test.
- **Khoảng trống:** angle mà khách nhắc nhiều trong `04-comments/insights.md` nhưng đối thủ chưa chạy. Proof score bằng 0 vì chưa ai chạy, nhưng vẫn có thể dành **1 trong 5 slot** cho nó (ghi rõ "angle khoảng trống, không có dữ liệu đối thủ").
- Chốt bảng **A1–A5**: mã · angle · proof · CPC kỳ vọng · ROAS mục tiêu · lý do chọn. Đây là input bắt buộc của `/angle-lab:angle-test`.

Ngân sách test vẫn **chia đều** 5 angle. Proof score dùng để *chọn* angle và *đặt kỳ vọng*, không dùng để chia tiền, vì chia lệch thì test không còn sạch.

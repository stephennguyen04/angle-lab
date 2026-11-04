---
name: winner
description: Giai đoạn 2 của "TEST ANGLE TRƯỚC, NHÂN BẢN SAU". Đọc kết quả test (file export Ads Manager), xác định video/angle nào ra sale, rồi mổ sâu video thắng để rút ra ANGLE KIM CHỈ NAM, gồm các yếu tố bất biến (không được đổi) và các biến được phép đổi (nhân vật, bối cảnh, hook). Xuất north-star.md + angle.json làm luật cho mọi lần nhân bản. Dùng khi nói "video nào ra sale", "đọc kết quả test", "mổ video thắng", "rút angle kim chỉ nam", "winner".
argument-hint: "<research/<slug>> <file export Ads Manager .csv>"
---

# /angle-lab:winner: Mổ video thắng → ANGLE KIM CHỈ NAM

Script: `${CLAUDE_PLUGIN_ROOT}/scripts/`. Output: `research/<slug>/creative/02-readout.md`, `03-north-star.md`, `angle.json`.

## 1. Đọc số

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/test_readout.py" -i <export.csv> --price <giá> --cogs <giá vốn> --shipping <ship> --fees-pct 5 \
  --scoreboard research/<slug>/01-scale/scoreboard.json \
  --out-md research/<slug>/creative/02-readout.md --out-json research/<slug>/creative/readout.json
```
Bảng **"Dự đoán từ spy vs thực tế"** đặt CPC/ROAS **thật** của từng angle cạnh CPC ước tính / ROAS sàn suy ra lúc spy:
- Angle proof cao mà mình chạy thua: thường do **thực thi** (hook, dựng, offer/LP), chưa chắc angle sai. Cân nhắc test lại 1 bản dựng tốt hơn trước khi bỏ.
- Angle thắng **ngoài dự đoán** (nhất là angle khoảng trống): đáng giá nhất vì đối thủ chưa khai thác.
- CPC thật cao hơn khoảng ước tính: hook 3s yếu hơn bản gốc, xem lại hook rate.
(hoặc `--breakeven-cpa <số>`; tên ad không theo naming convention thì truyền `--angle-regex`.)

Diễn giải thêm dưới bảng: angle nào thắng, thắng vì đâu (hook rate cao? CTR cao? CVR cao?), angle thua chết ở bước nào trong phễu.
- **Chưa có WINNER** thì đừng ép. Nếu có TIỀM NĂNG: chạy thêm 1–2 ngày. Nếu tất cả KILL: xem lại offer/LP trước, hoặc quay về `/angle-lab:angle-test` với lứa angle mới. Dừng ở đây.
- Nhiều WINNER thì chọn angle CPA thấp nhất + nhiều đơn nhất làm kim chỉ nam. Angle còn lại để dành, không trộn.

## 2. Mổ video thắng (sâu hơn lúc spy)

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/video_prep.sh" <file video thắng> research/<slug>/creative/winner_video
```
Xem từng khung hook + keyframe cảnh + transcript. So sánh với **video gốc của đối thủ** (`03-videos/vN`) và với **các video thua**: điểm khác biệt nào giải thích được kết quả? Chỉ những gì *có ở video thắng mà video thua không có* mới được coi là yếu tố quyết định.

Dùng thêm số liệu: hook rate cao → hook đang làm việc; hold rate cao → beat/story giữ được; CVR cao → lời hứa khớp với PDP/offer.

Đối chiếu `04-comments/insights.md` (và bình luận dưới chính ad thắng nếu có): khách phản hồi gì với ad của mình?

## 3. Viết ANGLE KIM CHỈ NAM → `creative/03-north-star.md`

Theo template `${CLAUDE_PLUGIN_ROOT}/templates/north-star.md`. Cốt lõi:

1. **Angle 1 câu** (dán lên tường): *[Persona] đang [nỗi đau cụ thể] vì [nguyên nhân họ chưa biết]; [sản phẩm] [cơ chế] nên [kết quả hứa hẹn], [bằng chứng].*
2. **BẤT BIẾN, nhân bản phải giữ nguyên:**
   - Persona & tình huống nỗi đau
   - Nỗi đau sâu / cảm xúc chủ đạo
   - Niềm tin cốt lõi / cơ chế
   - Lời hứa (kết quả + khung thời gian)
   - Loại bằng chứng (demo / before-after / review…)
   - Thứ tự beat chính (vd: Hook nỗi đau → Cách cũ thất bại → Cơ chế → Demo → Offer)
   - Objection bắt buộc xử lý
3. **BIẾN ĐƯỢC ĐỔI (để nhân bản):** nhân vật (tuổi, giới, ngoại hình, vai: khách/chuyên gia/người thân) · bối cảnh (nhà, văn phòng, xe, ngoài trời…) · hook (câu chữ, hình mở, kiểu hook nhưng *phải gọi đúng nỗi đau/lời hứa của angle*) · giọng/voice, nhạc, nhịp cắt, độ dài cutdown 15/30/45s, tỉ lệ khung.
4. **Cơ chế hook đã thắng:** khung hook cụ thể của video thắng (hình + chữ + lời) và *vì sao* nó hiệu quả.
5. **🚩 Dấu hiệu lạc angle** (ví dụ cụ thể theo sản phẩm): đổi sang nỗi đau khác · thêm lợi ích phụ làm loãng · đổi persona sang nhóm khác · đổi lời hứa · hook "viral" nhưng không liên quan nỗi đau.

## 4. Xuất `creative/angle.json` (luật máy đọc được cho `/angle-lab:clone`)

```json
{
  "angle_id": "A3",
  "angle_name": "dau-lung-van-phong",
  "angle_statement": "…",
  "invariants": ["Persona: dân văn phòng 25-40 ngồi >8h", "Nỗi đau: đau lưng dưới cuối ngày", "Cơ chế: sửa tư thế thụ động", "Lời hứa: đỡ đau sau 7 ngày", "Proof: demo đeo vào + cận cảnh tư thế", "Beat: Hook nỗi đau → cách cũ thất bại → cơ chế → demo → offer"],
  "drift_red_flags": ["…"],
  "control": {"hook": "H0", "character": "C0", "setting": "S0"},
  "hooks": [{"id": "H0", "type": "callout nỗi đau", "text": "(hook của video thắng)"}, {"id": "H1", "type": "kết quả trước", "text": "…"}],
  "characters": [{"id": "C0", "desc": "(nhân vật video thắng)"}, {"id": "C1", "desc": "…"}],
  "settings": [{"id": "S0", "desc": "(bối cảnh video thắng)"}, {"id": "S1", "desc": "…"}]
}
```
Soạn sẵn **10 hook mới** (đủ kiểu hook, đều bám nỗi đau/lời hứa của angle, ưu tiên ngôn ngữ khách thật từ bình luận), **5 nhân vật**, **5 bối cảnh** đều hợp persona. H0/C0/S0 = đúng của video thắng (control).

Ghi vào `creative/log.md`. Bước tiếp: `/angle-lab:clone research/<slug>`.

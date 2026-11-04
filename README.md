# 🎯 angle-lab: Spy đối thủ → Test angle → Nhân bản

Plugin cho **Claude Code**: với mỗi sản phẩm, AI phân tích đối thủ từ A–Z rồi chạy quy trình creative **TEST ANGLE TRƯỚC, NHÂN BẢN SAU**.

```
 SPY (1 sản phẩm)                                   CREATIVE
 ┌────────────────────────────┐   5 angle   ┌──────────────┐  vài ngày  ┌──────────────┐  angle.json  ┌──────────────┐
 │ 1. Scale ads (Ad Library)  │ ──────────▶ │  angle-test  │ ─────────▶ │    winner    │ ───────────▶ │    clone     │
 │ 2. PDP · bundle · funnel   │             │ 5 video test │  ra sale   │ mổ video thắng│  kim chỉ nam │ đổi nhân vật,│
 │ 3. 5 video top → angle/hook│             │ 1 video=1    │            │ → ANGLE KIM  │              │ bối cảnh,hook│
 │ 4. Đa nền tảng + bình luận │             │ angle        │            │   CHỈ NAM    │              │ BÁM 1 ANGLE  │
 └────────────────────────────┘             └──────────────┘            └──────────────┘              └──────────────┘
```

## Lệnh

| Lệnh | Làm gì |
|---|---|
| `/angle-lab:spy <link SP / shop / Ad Library>` | Spy toàn diện, chạy song song 4 mảng bên dưới → `REPORT.md` + verdict LÀM / BỎ |
| `/angle-lab:ad-scale` | Đang scale tới đâu: bao nhiêu ad active, ra ad mới đều không (histogram theo tuần), ad sống lâu nhất, landing về đâu, **chọn 5 video top** |
| `/angle-lab:funnel` | Product page dựng thế nào, bundle bán ra sao (giá bậc thang, giá/đơn vị), funnel thẳng PDP hay qua advertorial/listicle/quiz |
| `/angle-lab:top-videos` | Mổ 5 video top: angle, nỗi đau bề mặt → sâu, persona, **hook 0–3s theo từng khung hình**, beat, proof, format |
| `/angle-lab:comments` | Họ bán trên nền tảng nào, **đọc và gắn nhãn từng bình luận**: chê gì, khen gì, hỏi gì → rủi ro 🔴🟡🟢, FAQ, đạn creative, điểm làm tốt hơn |
| `/angle-lab:angle-test` | Brief dựng lại 5 video top thành 5 video test (1 video = 1 angle), cấu trúc camp, ngân sách theo CPA hoà vốn, naming, rule kill |
| `/angle-lab:winner <export.csv>` | Đọc số → video nào ra sale → mổ video đó → **ANGLE KIM CHỈ NAM** (bất biến vs biến được đổi) + `angle.json` |
| `/angle-lab:clone` | Nhân bản bằng AI theo vòng (hook → nhân vật → bối cảnh), có **kiểm tra angle lock**: lạc angle là loại |

Agent chạy song song: `ad-scale-analyst`, `funnel-analyst`, `video-angle-analyst`, `comment-miner`.

## Cài đặt

**Từ GitHub** (repo này đồng thời là 1 marketplace):
```
/plugin marketplace add <github-user>/angle-lab
/plugin install angle-lab@angle-lab
```

**Thử local không cần cài:**
```bash
claude --plugin-dir /đường/dẫn/angle-lab
```

### Phụ thuộc
| Công cụ | Bắt buộc? | Dùng cho |
|---|---|---|
| Python 3.9+ | ✅ | toàn bộ script phân tích (chỉ dùng thư viện chuẩn) |
| `ffmpeg` | ✅ cho mổ video | cắt khung hook 0–3s, keyframe cảnh |
| Node + `playwright` | nên có | capture funnel mobile, scraper Ad Library dự phòng (`npm i -g playwright && npx playwright install chromium`) |
| `yt-dlp` | nên có | tải video & **bình luận** TikTok/YouTube (`pipx install yt-dlp`) |
| `faster-whisper` | tuỳ chọn | transcript lời thoại video (`pip install faster-whisper`) |
| MCP **Meta Ads** | tuỳ chọn (khuyên dùng) | `ads_library_search`: lấy ad đối thủ không cần scrape |
| MCP **Higgsfield** | tuỳ chọn | sinh video AI khi nhân bản (đổi nhân vật/bối cảnh) |

## Dữ liệu được lưu ở đâu

Mọi thứ nằm trong project của bạn, mỗi sản phẩm 1 thư mục, nên vài ngày sau quay lại vẫn làm tiếp được:
```
research/<san-pham>/
  00-input.md
  01-scale/      ads_raw.json · scale.json · scale.md
  02-funnel/     lp1/step1.png … · product.json · funnel.md
  03-videos/     v1..v5/{hook/, scenes/, transcript.txt, analysis.md} · videos.md
  04-comments/   raw/ · comments.jsonl · labels.jsonl · report.md · insights.md
  REPORT.md
  creative/
    01-test-plan.md · briefs/A1..A5.md
    02-readout.md · 03-north-star.md · angle.json
    04-variants.csv · variants/*.md
    log.md · ideas-backlog.md
```

## Script (dùng độc lập được)

```bash
python3 scripts/ad_cadence.py -i ads.json --brand-domain brand.com          # scale & nhịp ra ad
node    scripts/adlib_scrape.cjs "<Ad Library URL>" ads.json --max 300       # fallback lấy ad
node    scripts/capture_page.cjs "<landing>" out/ --follow-cta               # funnel mobile
python3 scripts/shopify_product.py "<PDP url>"                               # variants / bundle
bash    scripts/video_prep.sh "<video|url>" out/                             # khung hook + cảnh + transcript
python3 scripts/comments.py prep -i tiktok:a.info.json -i amazon:r.csv --out-dir c/
python3 scripts/comments.py report --out-dir c/                              # sau khi AI gắn nhãn
python3 scripts/test_readout.py -i export.csv --price 49.99 --cogs 12 --shipping 5
python3 scripts/variant_matrix.py --angle angle.json --mode staged --round 1
bash    tests/run_tests.sh                                                   # smoke test
```

## Quy ước quan trọng

- **Angle ≠ Hook ≠ Format.** Angle = ai + nỗi đau + cơ chế (lý do mua). Hook = cách mở 3s đầu. Format = cách quay. Nhân bản = giữ angle, đổi hook/nhân vật/bối cảnh.
- **Naming ad:** `<yymmdd>_A<n>-<slug>_V<nn>_H<n>` (test angle) · `<yymmdd>_A<n>_V<nn>_H#_C#_S#` (nhân bản). Script đọc kết quả dựa vào tên này.
- **Rule mặc định:** WINNER = ≥3 đơn & CPA ≤ CPA hoà vốn; KILL = chi ≥1.5× CPA hoà vốn mà 0 đơn, hoặc hook rate <15% sau 3.000 hiển thị. Chỉnh bằng flag.
- **"Edit lại video đối thủ" = dựng lại theo cấu trúc**, không re-up nguyên footage/giọng/logo của họ (dễ dính report IP → mất ad/page, data test cũng hỏng).
- Ngưỡng scale (10/50/200 ad active) và rule kill là heuristic, phải chỉnh theo ngách & biên lợi nhuận.

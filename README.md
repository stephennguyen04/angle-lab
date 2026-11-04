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
| `/angle-lab:scoreboard` | Tìm angle / ad / reel **mạnh nhất trên Meta Ads + Instagram** chỉ bằng dữ liệu công khai: ad sống lâu, bản nhân, tiếp cận EU, % ad IG, hợp tác creator, view/follower, % bình luận muốn mua/chê → Top 10 ad, Top 10 bài IG, chốt A1–A5 |
| `/angle-lab:audience` | Persona đối thủ **thực sự tiếp cận** (giới, tuổi, quốc gia theo angle) từ dữ liệu minh bạch EU/UK của Ad Library API, dùng để chọn nhân vật |
| `/angle-lab:ocr` | Đọc **chữ trên màn hình** video/ảnh (text overlay hook, caption, sticker giá), **tiếng Việt có dấu**, có timeline |
| `/angle-lab:transcribe` | **Nghe lời thoại → chữ** (tiếng Việt có dấu), timestamp từng từ, câu hook 3s đầu, tốc độ nói, phụ đề .srt |
| `/angle-lab:apify` | Lấy **bình luận Facebook/Instagram** (kèm trả lời), bài IG, ad Meta qua Apify, chuyển thẳng sang định dạng phân tích |
| `/angle-lab:hooks` | **Thư viện hook dùng chung** mọi sản phẩm: hook đối thủ sống lâu + hook mình test thắng, tìm không cần dấu |
| `/angle-lab:monitor` | **Theo dõi đối thủ hằng ngày**: ad mới, ad vượt 30/60 ngày, tăng bản nhân, đổi giá/bundle |
| `/angle-lab:discover` | **Tự tìm đối thủ** từ từ khoá ngách, xếp hạng page đáng spy, loại sàn TMĐT |
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
| `yt-dlp` | nên có | tải video & **bình luận** TikTok/YouTube, tải reel IG (`pipx install yt-dlp`) |
| `instaloader` | nên có | lấy Reels/bài IG, bài được tag, hashtag, bình luận (`pip install instaloader`, rồi `instaloader -l <user>` để có session). Không có thì import export Apify |
| `faster-whisper` | nên có | nghe lời thoại → chữ, tiếng Việt có dấu (`pip install faster-whisper`; model `medium` ~1,5 GB tải lần đầu) |
| `tesseract` + `vie` | nên có | đọc chữ trên màn hình có dấu (`brew install tesseract tesseract-lang` · `apt install tesseract-ocr tesseract-ocr-vie`); hoặc `pip install easyocr` |
| Apify (`APIFY_TOKEN`) | tuỳ chọn | bình luận FB/IG, bài IG, ad Meta qua actor Apify |
| Meta Ad Library API (`META_ADLIB_TOKEN`) | tuỳ chọn | lượt tiếp cận EU + cơ cấu tuổi/giới/quốc gia (cần xác minh danh tính tại facebook.com/ID) |
| MCP **Meta Ads** | tuỳ chọn (khuyên dùng) | `ads_library_search`: lấy ad đối thủ không cần scrape |
| MCP **Higgsfield** | tuỳ chọn | sinh video AI khi nhân bản (đổi nhân vật/bối cảnh) |

## Dữ liệu được lưu ở đâu

Mọi thứ nằm trong project của bạn, mỗi sản phẩm 1 thư mục, nên vài ngày sau quay lại vẫn làm tiếp được:
```
research/<san-pham>/
  00-input.md
  01-scale/      ads_raw.json · scale.json · scale.md · ig/posts.csv · ig/comments/ · angle_map.csv · scoreboard.md/json
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
python3 scripts/adlib_parse.py -i ads.har -o ads.json                       # HAR / GraphQL / JSON → ad chuẩn (placement, bản nhân, EU reach, hợp tác)
node    scripts/adlib_scrape.cjs "<Ad Library URL>" scrape.json --platform instagram --details 30   # bắt GraphQL
python3 scripts/ad_cadence.py -i ads.json --brand-domain brand.com          # scale, nhịp ra ad, hạng Long-Runner, % IG, EU reach
python3 scripts/ig_collect.py profile <brand> --reels-only --comments 200 --login <user>        # Reels + bình luận IG
python3 scripts/ig_collect.py import apify_instagram.json                    # hoặc từ export Apify
APIFY_TOKEN=… python3 scripts/apify_fetch.py fb-comments <URL bài/ad> --limit 500 --out-dir c/raw   # bình luận FB qua Apify
META_ADLIB_TOKEN=… python3 scripts/adlib_api.py --page-ids 123 --countries DE,FR -o api.json   # API chính thức (DSA)
python3 scripts/audience.py --ads ads_raw.json --angle-map angle_map.csv     # persona theo angle
python3 scripts/ocr_frames.py --video ad.mp4 --out-dir v1/                   # chữ trên màn hình (tiếng Việt có dấu)
python3 scripts/transcribe.py ad.mp4 --out-dir v1/ --lang vi                 # lời thoại → chữ
python3 scripts/hooks_library.py harvest --root research                     # thư viện hook
python3 scripts/monitor.py diff --dir research/x/monitor                     # theo dõi thay đổi
python3 scripts/discover.py -i kw1.json -i kw2.json                          # tìm đối thủ
node    scripts/capture_page.cjs "<landing>" out/ --follow-cta               # funnel mobile
python3 scripts/shopify_product.py "<PDP url>"                               # variants / bundle
bash    scripts/video_prep.sh "<video|url>" out/                             # khung hook + cảnh + transcript
python3 scripts/comments.py prep -i tiktok:a.info.json -i amazon:r.csv --out-dir c/
python3 scripts/comments.py report --out-dir c/                              # sau khi AI gắn nhãn
python3 scripts/angle_scoreboard.py --posts ig/posts.csv --comments-dir c/ --ads ads.json --angle-map angle_map.csv   # Top ad, top reel, A1–A5
python3 scripts/test_readout.py -i export.csv --price 49.99 --cogs 12 --shipping 5 --scoreboard scoreboard.json
python3 scripts/variant_matrix.py --angle angle.json --mode staged --round 1
bash    tests/run_tests.sh                                                   # smoke test
```

## Quy ước quan trọng

- **Angle ≠ Hook ≠ Format.** Angle = ai + nỗi đau + cơ chế (lý do mua). Hook = cách mở 3s đầu. Format = cách quay. Nhân bản = giữ angle, đổi hook/nhân vật/bối cảnh.
- **Naming ad:** `<yymmdd>_A<n>-<slug>_V<nn>_H<n>` (test angle) · `<yymmdd>_A<n>_V<nn>_H#_C#_S#` (nhân bản). Script đọc kết quả dựa vào tên này.
- **Không ước tính CPC/ROAS của đối thủ** (không công khai). Bảng điểm angle chỉ dùng số nhìn thấy được trên mạng xã hội. CPC/ROAS duy nhất là số thật từ ad của bạn, và `test_readout.py --scoreboard` so nó với hạng dự đoán.
- **Rule mặc định:** WINNER = ≥3 đơn & CPA ≤ CPA hoà vốn; KILL = chi ≥1.5× CPA hoà vốn mà 0 đơn, hoặc hook rate <15% sau 3.000 hiển thị. Chỉnh bằng flag.
- **"Edit lại video đối thủ" = dựng lại theo cấu trúc**, không re-up nguyên footage/giọng/logo của họ (dễ dính report IP → mất ad/page, data test cũng hỏng).
- Ngưỡng scale (10/50/200 ad active) và rule kill là heuristic, phải chỉnh theo ngách & biên lợi nhuận.

## Tham khảo

Ý tưởng được học từ các dự án mã nguồn mở (không sao chép code):
- [seancrowe01/ads-machine](https://github.com/seancrowe01/ads-machine): xếp hạng ad theo số ngày chạy (Long-Runner / Performer / Solid / Testing), vòng lặp winner → thư viện hook.
- [NiksHacks/meta-ads-library-scraper](https://github.com/NiksHacks/meta-ads-library-scraper): bắt response GraphQL thay vì đọc giao diện, và cách đọc file HAR do người dùng tự lưu.
- [instaloader](https://github.com/instaloader/instaloader): thư viện lấy dữ liệu Instagram công khai.

Lưu ý: chỉ thu thập dữ liệu công khai, giữ tốc độ vừa phải và tôn trọng điều khoản của Meta / Instagram.

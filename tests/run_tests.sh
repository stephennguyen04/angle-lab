#!/usr/bin/env bash
# Smoke test cho toàn bộ script của angle-lab. Chạy: bash tests/run_tests.sh
set -euo pipefail
cd "$(dirname "$0")"
S=$(cd ../scripts && pwd); T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass() { echo "✅ $1"; }

python3 $S/ad_cadence.py -i fixtures/ads.json --as-of 2026-11-04 --brand-domain brand.com --out-json $T/s.json --out-md $T/s.md
python3 - $T/s.json <<'PY'
import json,sys; d=json.load(open(sys.argv[1]))
assert d["total_ads"]==61 and d["active_ads"]==45, d["active_ads"]
assert len(d["top_videos"])==5 and d["new_ads"]["30d"]==17
assert "PDP (thẳng trang sản phẩm)" in d["landing_mix"]
PY
pass "ad_cadence.py"

python3 $S/comments.py prep --out-dir $T/c -i tiktok:fixtures/tiktok.info.json -i amazon:fixtures/amazon.csv >/dev/null
test "$(wc -l < $T/c/comments.jsonl)" -eq 10
python3 - $T/c <<'PY'
import json,sys; d=sys.argv[1]
with open(d+"/labels.jsonl","w") as f:
    for l in open(d+"/comments.jsonl"):
        c=json.loads(l); bad=any(k in c["text"] for k in ("Ordered","rash"))
        f.write(json.dumps({"id":c["id"],"type":"complaint" if bad else "praise","topics":["shipping" if "Ordered" in c["text"] else "safety"] if bad else ["efficacy"],"severity":3 if bad else 0,"buyer":True})+"\n")
PY
python3 $S/comments.py report --out-dir $T/c >/dev/null
python3 -c "import json;d=json.load(open('$T/c/report.json'));assert d['severity3_count']==2 and d['risk_level'].startswith('🔴'),d"
pass "comments.py prep/report"

python3 $S/test_readout.py -i fixtures/meta_export.csv --price 49.99 --cogs 10 --shipping 4 --fees-pct 5 --out-json $T/r.json >/dev/null
python3 -c "
import json;d=json.load(open('$T/r.json'));a={x['angle']:x['decision'] for x in d['angles']}
assert a=={'A1':'WINNER','A5':'TIỀM NĂNG','A4':'BORDERLINE','A2':'KILL','A3':'KILL'},a"
pass "test_readout.py"

python3 $S/variant_matrix.py --angle fixtures/angle.json --out $T/v.csv --prefix 261110 >/dev/null
test "$(tail -n +2 $T/v.csv | wc -l)" -eq 8
python3 $S/variant_matrix.py --angle fixtures/angle.json --mode staged --round 1 --out $T/v1.csv >/dev/null
test "$(tail -n +2 $T/v1.csv | wc -l)" -eq 4
pass "variant_matrix.py"

python3 $S/angle_scoreboard.py --focus all --posts fixtures/posts.csv --comments-dir $T/c --ads fixtures/ads.json \
  --angle-map fixtures/angle_map.csv --as-of 2026-11-04 --out-json $T/sb.json >/dev/null
python3 - $T/sb.json <<'PY'
import json,sys; a=json.load(open(sys.argv[1]))["angles"]
top=a[0]; assert top["angle"]=="dau-lung-van-phong" and top["test_code"]=="A1" and top["creators"]==3
assert top["comments_labeled"]==7 and top["negative_pct"]==14.3, top  # 7 bình luận TikTok nối theo URL; review Amazon không có URL bài
assert sum(1 for x in a if x["test_code"])==5 and all("cpc_est" not in x for x in a)
PY
python3 $S/test_readout.py -i fixtures/meta_export.csv --price 49.99 --cogs 10 --shipping 4 --fees-pct 5 --scoreboard $T/sb.json --out-json $T/r2.json >/dev/null
python3 -c "
import json;d=json.load(open('$T/r2.json'));assert d['breakeven_roas']==1.49 and len(d['spy_vs_actual'])==5
assert any('tốt hơn dự đoán' in n for r in d['spy_vs_actual'] for n in r['notes'])"
pass "angle_scoreboard.py + test_readout --scoreboard"

# ---- Meta Ads + Instagram ----
python3 $S/adlib_parse.py -i fixtures/adlib.har -o $T/ads.json 2>/dev/null >/dev/null
python3 - $T/ads.json <<'PY'
import json,sys; d={x["id"]:x for x in json.load(open(sys.argv[1]))}
assert len(d)==6 and d["9001"]["eu_reach"]==1850000 and d["9002"]["partnership"] and d["9001"]["duplicates"]==12
assert d["9001"]["platforms"]=="facebook,instagram" and d["9006"]["is_active"] is False and d["9001"]["start_date"]=="2026-07-09"
PY
python3 $S/adlib_parse.py -i fixtures/adlib.har -o $T/ads_ig.json --platform instagram 2>/dev/null >/dev/null
python3 -c "import json;assert len(json.load(open('$T/ads_ig.json')))==4"
pass "adlib_parse.py (HAR, for(;;);, base64, gộp EU reach)"

python3 $S/ig_collect.py import fixtures/apify_instagram.json --out-dir $T/ig >/dev/null
python3 - $T/ig <<'PY'
import csv,sys,json,os; d=sys.argv[1]; rows=list(csv.DictReader(open(d+"/posts.csv")))
assert len(rows)==7 and rows[1]["is_partnership"]=="True" and rows[0]["followers"]=="85000" and rows[0]["date"]=="2026-09-02"
c=json.load(open(d+"/comments/AAA1.json")); assert len(c["comments"])==3 and c["webpage_url"].endswith("AAA1/")
# gán angle như AI sẽ làm, rồi import lại: angle phải được giữ
for r in rows: r["angle"]={"AAA":"dau-lung-van-phong","BBB":"so-sanh","CCC":"qua-tang","DDD":"tu-the-xau"}[r["url"].rstrip("/").split("/")[-1][:3]]
w=csv.DictWriter(open(d+"/posts.csv","w",newline=""),fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
PY
python3 $S/ig_collect.py import fixtures/apify_instagram.json --out-dir $T/ig >/dev/null
python3 -c "import csv;r=list(csv.DictReader(open('$T/ig/posts.csv')));assert len(r)==7 and all(x['angle'] for x in r)"
python3 - <<'PY'
import sys, types; sys.path.insert(0, "../scripts"); from ig_collect import row_from_post
from datetime import datetime
p = types.SimpleNamespace(shortcode="XYZ", owner_username="brand", video_play_count=None, video_view_count=5000, likes=-1, comments=12,
      date_utc=datetime(2026,10,1), is_video=True, caption="hi #ad", caption_hashtags=["ad"], is_sponsored=True, sponsor_users=[], video_url="v.mp4")
r = row_from_post(p, 1000); assert r["views"]==5000 and r["likes"] is None and r["is_partnership"] and r["url"].endswith("/p/XYZ/")
PY
pass "ig_collect.py (Apify import, giữ angle khi chạy lại, instaloader row)"

printf 'ad_id,angle,angle_name\n9001,dau-lung-van-phong,Đau lưng\n9002,dau-lung-van-phong,Đau lưng\n9003,so-sanh,So sánh\n9004,qua-tang,Quà tặng\n9005,chuyen-gia,Chuyên gia\n9006,tu-the-xau,Tư thế\n' > $T/amap.csv
python3 $S/angle_scoreboard.py --posts $T/ig/posts.csv --ads $T/ads.json --angle-map $T/amap.csv --as-of 2026-11-04 --out-json $T/sb2.json >/dev/null
python3 - $T/sb2.json <<'PY'
import json,sys; d=json.load(open(sys.argv[1])); a={x["angle"]:x for x in d["angles"]}
assert d["focus"]=="meta-ig" and d["angles"][0]["angle"]=="dau-lung-van-phong"
assert "chuyen-gia" not in a, "ad chỉ chạy Audience Network phải bị loại ở focus meta-ig"
assert a["dau-lung-van-phong"]["eu_reach_total"]==2270000 and a["dau-lung-van-phong"]["partnership_ads"]==1
assert d["top_ads"][0]["id"]=="9001" and d["top_posts"][0]["url"].endswith("AAA2/")
PY
pass "angle_scoreboard.py --focus meta-ig (top ad, top bài IG)"

# ---- Apify (server giả lập) ----
freeport() { python3 -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1]);s.close()"; }
PA=$(freeport); python3 mock_apify.py $PA & PID_A=$!
PG=$(freeport); python3 mock_graph.py $PG & PID_G=$!
trap 'kill $PID_A $PID_G 2>/dev/null; rm -rf "$T"' EXIT
sleep 1
export NO_PROXY=127.0.0.1,localhost
APIFY_API_BASE=http://127.0.0.1:$PA/v2 APIFY_POLL_SECONDS=0.05 APIFY_TOKEN=test-token \
  python3 $S/apify_fetch.py fb-comments "https://www.facebook.com/brand/posts/111" "https://www.facebook.com/brand/posts/222" --out-dir $T/apfb >/dev/null 2>&1
python3 $S/comments.py prep --out-dir $T/apc $(for f in $T/apfb/comments/*.json; do echo "-i facebook:$f"; done) >/dev/null
python3 - $T/apc <<'PY'
import json,sys; r=[json.loads(l) for l in open(sys.argv[1]+"/comments.jsonl")]
assert len(r)==3 and sum(x["is_reply"] for x in r)==1 and max(x["likes"] for x in r)==1200, r
assert all("?" not in (x["source_url"] or "") for x in r)
PY
bad=$(APIFY_API_BASE=http://127.0.0.1:$PA/v2 APIFY_TOKEN=wrong python3 $S/apify_fetch.py fb-comments x --out-dir $T/bad 2>&1 || true)
echo "$bad" | grep -q "401"
pass "apify_fetch.py (run → chờ → dataset, trả lời lồng, 1,2K, lỗi token)"

# ---- Ad Library API + persona ----
META_GRAPH_BASE=http://127.0.0.1:$PG META_ADLIB_TOKEN=tk python3 $S/adlib_api.py --page-ids 777 --countries DE,FR -o $T/api.json >/dev/null 2>&1
python3 $S/adlib_parse.py -i $T/api.json -o $T/ads_eu.json >/dev/null 2>&1
printf 'ad_id,angle,angle_name\n7001,dau-lung,Đau lưng\n7002,so-sanh,So sánh\n' > $T/amap_eu.csv
python3 $S/audience.py --ads $T/ads_eu.json --angle-map $T/amap_eu.csv --out-json $T/aud.json >/dev/null
python3 - $T/aud.json <<'PY'
import json,sys; d=json.load(open(sys.argv[1])); a=d["angles"]
assert d["ads_without_breakdown"]==1 and a["dau-lung"]["gender_pct"]["female"]>70 and a["dau-lung"]["top_cell"]=="Nữ 35-44"
assert "25–44" in a["dau-lung"]["persona"] and a["so-sanh"]["gender_pct"]["male"]>50
PY
pass "adlib_api.py (phân trang) + audience.py (persona theo angle)"

# ---- Thư viện hook ----
mkdir -p $T/hk/research/p1/03-videos $T/hk/research/p1/creative
echo '{"text":"Ngồi 8 tiếng mỗi ngày? Lưng bạn đang kêu cứu","type":"callout nỗi đau","angle":"đau lưng","days_running":119,"duplicates":12}' > $T/hk/research/p1/03-videos/hooks.jsonl
printf 'variant_id,round,ad_name,hook_id,hook_type,hook_text\nV01,1,AD1,H1,kết quả trước,"7 ngày đeo, hết đau lưng"\n' > $T/hk/research/p1/creative/04-variants.csv
echo '{"ads":[{"ad":"AD1","decision":"WINNER","hook_rate":38.5,"cpa":14}]}' > $T/hk/research/p1/creative/readout.json
(cd $T/hk && python3 $S/hooks_library.py harvest --root research >/dev/null 2>&1 && python3 $S/hooks_library.py harvest --root research >/dev/null 2>&1 \
  && python3 $S/hooks_library.py results --readout research/p1/creative/readout.json --variants research/p1/creative/04-variants.csv --product p1 >/dev/null)
python3 - $T/hk/hooks-library/hooks.jsonl <<'PY'
import json,sys; h=[json.loads(l) for l in open(sys.argv[1])]
assert len(h)==2 and h[0]["source"]=="own" and h[0]["status"]=="proven" and h[1]["source"]=="competitor"
PY
(cd $T/hk && python3 $S/hooks_library.py search --q "dau lung" | grep -q "kêu cứu")
pass "hooks_library.py (harvest không nhân đôi, kết quả test, tìm không dấu)"

# ---- Theo dõi + tìm đối thủ ----
python3 - $T <<'PY'
import json,sys,copy; T=sys.argv[1]; a=json.load(open(T+"/ads.json")); b=[x for x in copy.deepcopy(a) if x["id"]!="9004"]
for x in b:
    if x["id"]=="9001": x["duplicates"]=30
b.append({**b[0],"id":"9999","start_date":"2026-11-07"}); json.dump(b,open(T+"/ads_b.json","w"))
p={"variants":[{"title":"2 Pack","price":79.99,"compare_at":179.98,"available":True}],"markers":{"quantity_break_app":False}}
q=copy.deepcopy(p); q["variants"][0]["price"]=74.99; q["markers"]["quantity_break_app"]=True
json.dump(p,open(T+"/p1.json","w")); json.dump(q,open(T+"/p2.json","w"))
PY
python3 $S/monitor.py snapshot --dir $T/mon --ads $T/ads.json --product $T/p1.json --date 2026-11-04 >/dev/null
python3 $S/monitor.py snapshot --dir $T/mon --ads $T/ads_b.json --product $T/p2.json --date 2026-11-08 >/dev/null
python3 $S/monitor.py diff --dir $T/mon --out $T/alert.md >/dev/null
for k in "Ad mới: 1" "Tăng bản nhân" "Ad đã tắt: 1" "74.99" "Bật \*\*quantity_break_app"; do grep -q "$k" $T/alert.md || { echo "thiếu: $k"; exit 1; }; done
python3 $S/discover.py -i $T/ads.json -i fixtures/ads.json --as-of 2026-11-04 --out-json $T/disc.json >/dev/null
python3 -c "import json;d=json.load(open('$T/disc.json'));assert d[0]['page']=='PosturePro' and d[0]['ad_library'].endswith('777')"
pass "monitor.py (ad mới/tắt/tăng bản nhân, đổi giá, bật app) + discover.py"

# ---- OCR tiếng Việt (nếu có tesseract-vie) ----
if command -v tesseract >/dev/null && tesseract --list-langs 2>&1 | grep -qx vie; then
  python3 $S/ocr_frames.py --video fixtures/ocr_vi.mp4 --out-dir $T/ocr >/dev/null
  for k in "Ngồi 8 tiếng mỗi ngày" "Lưng bạn đang kêu cứu" "Không phải do ghế" "Giảm 50% hôm nay"; do grep -q "$k" $T/ocr/ocr.txt || { echo "OCR thiếu: $k"; cat $T/ocr/ocr.txt; exit 1; }; done
  pass "ocr_frames.py (đọc đúng 4/4 câu tiếng Việt có dấu)"
else echo "⏭  bỏ qua OCR (chưa cài tesseract + vie)"; fi

# ---- Nghe → chữ (chậm, cần model): RUN_SLOW=1 ----
if [ "${RUN_SLOW:-0}" = 1 ] && python3 -c "import faster_whisper" 2>/dev/null && command -v espeak-ng >/dev/null; then
  # Giọng espeak rất máy móc nên không đo độ chính xác từng chữ; kiểm tra pipeline: nhận tiếng Việt, có dấu, timestamp, hook, srt
  espeak-ng -v vi -s 140 -w $T/sp.wav "Ngồi tám tiếng mỗi ngày, lưng bạn đang kêu cứu. Không phải do ghế, mà do tư thế."
  ffmpeg -loglevel error -y -f lavfi -i "anullsrc=r=16000:cl=mono:d=1.5" -i $T/sp.wav -filter_complex "[0][1]concat=n=2:v=0:a=1[a]" -map "[a]" $T/sp2.wav
  python3 $S/transcribe.py $T/sp2.wav --out-dir $T/asr --lang vi --model medium >/dev/null 2>&1
  python3 - $T/asr <<'PY'
import json,sys,re; d=json.load(open(sys.argv[1]+"/transcript.json")); txt=" ".join(s["text"] for s in d["segments"])
assert d["language"]=="vi" and re.search(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", txt.lower()), txt
assert 0.8 <= d["first_word_at"] <= 2.0 and d["hook_0_3s"] and d["words_per_sec"] and "tư thế" in txt.lower(), d
assert open(sys.argv[1]+"/transcript.srt").read().count("-->") >= 2
PY
  pass "transcribe.py (tiếng Việt có dấu, mốc thời gian, hook 3s, srt)"
else echo "⏭  bỏ qua nghe → chữ (RUN_SLOW=1 + faster-whisper + espeak-ng để chạy)"; fi

bash -n $S/video_prep.sh && node --check $S/capture_page.cjs && node --check $S/adlib_scrape.cjs && python3 -m py_compile $S/shopify_product.py $S/csvio.py $S/transcribe.py $S/apify_fetch.py $S/adlib_api.py
pass "syntax video_prep.sh / capture_page.cjs / adlib_scrape.cjs / shopify_product.py"
echo "Tất cả test đều pass."

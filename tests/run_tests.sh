#!/usr/bin/env bash
# Smoke test cho toàn bộ script của angle-lab. Chạy: bash tests/run_tests.sh
set -euo pipefail
cd "$(dirname "$0")"
S=../scripts; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
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

bash -n $S/video_prep.sh && node --check $S/capture_page.cjs && node --check $S/adlib_scrape.cjs && python3 -m py_compile $S/shopify_product.py $S/csvio.py
pass "syntax video_prep.sh / capture_page.cjs / adlib_scrape.cjs / shopify_product.py"
echo "Tất cả test đều pass."

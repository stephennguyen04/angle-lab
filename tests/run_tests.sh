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

python3 $S/angle_scoreboard.py --ads fixtures/ads.json --angle-map fixtures/angle_map.csv --posts fixtures/posts.csv \
  --spy-tool fixtures/spy_tool.csv --aov 49.99 --cogs 10 --shipping 4 --fees-pct 5 --bench-cpc 0.9 --as-of 2026-11-04 --out-json $T/sb.json >/dev/null
python3 - $T/sb.json <<'PY'
import json,sys; d=json.load(open(sys.argv[1])); a=d["angles"]
assert d["be_roas"]==1.49 and a[0]["angle"]=="dau-lung-van-phong" and a[0]["test_code"]=="A1"
assert sum(1 for x in a if x["test_code"])==5 and a[0]["cpc_source"]=="tool spy"
assert next(x for x in a if x["angle"]=="tre-em")["confidence"]=="TB"
PY
python3 $S/test_readout.py -i fixtures/meta_export.csv --price 49.99 --cogs 10 --shipping 4 --fees-pct 5 --scoreboard $T/sb.json --out-json $T/r2.json >/dev/null
python3 -c "
import json;d=json.load(open('$T/r2.json'));assert d['breakeven_roas']==1.49 and len(d['spy_vs_actual'])==5
assert any('tốt hơn dự đoán' in n for r in d['spy_vs_actual'] for n in r['notes'])"
pass "angle_scoreboard.py + test_readout --scoreboard"

bash -n $S/video_prep.sh && node --check $S/capture_page.cjs && node --check $S/adlib_scrape.cjs && python3 -m py_compile $S/shopify_product.py
pass "syntax video_prep.sh / capture_page.cjs / adlib_scrape.cjs / shopify_product.py"
echo "Tất cả test đều pass."

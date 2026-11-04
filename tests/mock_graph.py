"""Graph API ads_archive giả lập (2 trang)."""
import http.server, json, sys
def bd(f_share):
    return [{"country": "DE", "age_gender_breakdowns": [
        {"age_range": "25-34", "male": int(4000*(1-f_share)), "female": int(4000*f_share), "unknown": 20},
        {"age_range": "35-44", "male": int(6000*(1-f_share)), "female": int(6000*f_share), "unknown": 10},
        {"age_range": "45-54", "male": int(2000*(1-f_share)), "female": int(2000*f_share)},
        {"age_range": "18-24", "male": 300, "female": 200}]},
        {"country": "FR", "age_gender_breakdowns": [{"age_range": "35-44", "male": 500, "female": 1500}]}]
P1 = {"data": [{"id": "7001", "page_id": "777", "page_name": "PosturePro", "ad_delivery_start_time": "2026-07-01", "ad_snapshot_url": "https://x/7001",
               "ad_creative_bodies": ["Ngồi 8 tiếng mỗi ngày?"], "publisher_platforms": ["facebook", "instagram"], "eu_total_reach": 15020,
               "age_country_gender_reach_breakdown": bd(.75), "target_ages": ["18", "65+"], "target_gender": "All",
               "target_locations": [{"name": "Germany", "type": "countries"}], "beneficiary_payers": [{"payer": "PP GmbH", "beneficiary": "PP"}]}],
      "paging": {"next": f"http://127.0.0.1:{sys.argv[1]}/v24.0/ads_archive?page=2"}}
P2 = {"data": [{"id": "7002", "page_id": "777", "ad_delivery_start_time": "2026-09-01", "ad_delivery_stop_time": "2026-10-01", "ad_snapshot_url": "https://x/7002",
               "ad_creative_bodies": ["So với nẹp cứng"], "publisher_platforms": ["instagram"], "eu_total_reach": 9000, "age_country_gender_reach_breakdown": bd(.4)},
              {"id": "7003", "page_id": "777", "ad_delivery_start_time": "2026-10-01", "ad_snapshot_url": "https://x/7003", "ad_creative_bodies": ["Không có DSA"]}]}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer tk":
            b = json.dumps({"error": {"code": 190, "message": "Invalid OAuth access token"}}).encode(); self.send_response(400)
        else:
            b = json.dumps(P2 if "page=2" in self.path else P1).encode(); self.send_response(200)
        self.end_headers(); self.wfile.write(b)
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()

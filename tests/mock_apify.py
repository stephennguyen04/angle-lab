"""Server Apify giả lập cho test (không gọi mạng thật)."""
import http.server, json, sys
STATE = {"polls": 0, "auth": []}
FB = [{"text": "Ship 3 tuần chưa tới, lừa à?", "likesCount": 15, "profileName": "A", "date": "2026-10-01T00:00:00Z",
       "facebookUrl": "https://www.facebook.com/brand/posts/111?__cft__=x", "threadingDepth": 0},
      {"text": "Shop đã inbox bạn rồi ạ", "likesCount": 1, "profileName": "Brand", "facebookUrl": "https://www.facebook.com/brand/posts/111", "threadingDepth": 1},
      {"text": "Link mua ở đâu?", "likesCount": "1,2K", "profileName": "B", "facebookUrl": "https://www.facebook.com/brand/posts/222"}]
IG = [{"text": "Đeo 1 tuần đỡ hẳn 😍", "ownerUsername": "c", "timestamp": "2026-10-02T00:00:00Z", "likesCount": 9, "postUrl": "https://www.instagram.com/reel/AAA1/",
       "replies": [{"text": "Mua ở đâu vậy bạn?", "ownerUsername": "d", "likesCount": 2}]}]
class H(http.server.BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
    def do_POST(self):
        STATE["auth"].append(self.headers.get("Authorization"))
        n = int(self.headers.get("Content-Length", 0)); STATE["input"] = json.loads(self.rfile.read(n) or b"{}")
        if self.headers.get("Authorization") != "Bearer test-token": return self._send({"error": "bad"}, 401)
        actor = self.path.split("/acts/")[1].split("/")[0]; STATE["actor"] = actor
        self._send({"data": {"id": "RUN1", "status": "RUNNING"}})
    def do_GET(self):
        if self.path.startswith("/v2/actor-runs/RUN1"):
            STATE["polls"] += 1
            return self._send({"data": {"id": "RUN1", "status": "SUCCEEDED" if STATE["polls"] > 1 else "RUNNING", "defaultDatasetId": "DS1"}})
        if self.path.startswith("/v2/actor-runs/"): return self._send({"error": "not found"}, 404)
        if self.path.startswith("/v2/datasets/"):
            off = int(self.path.split("offset=")[1].split("&")[0])
            items = IG if STATE.get("actor", "").startswith("apify~instagram") else FB
            return self._send(items if off == 0 else [])
        self._send({"error": "?"}, 404)
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()

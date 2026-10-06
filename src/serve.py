"""Tiny web service using only the Python standard library (no paid API, nothing to sign up for).
  python src/serve.py [--port 8000]        then open http://localhost:8000
  POST /route   {"request_text": "...", "channel": "chat", "product_family": "Water Purifier", "warranty_status": "in_warranty"}
  GET  /health"""
import argparse, json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "index.html")
BUNDLE = None
MAX_BODY = 20_000

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json"):
        if isinstance(obj, bytes): body = obj
        elif isinstance(obj, str): body = obj.encode()
        else: body = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok" if BUNDLE else "model_missing", "model_loaded": BUNDLE is not None})
        if self.path in ("/", "/index.html"):
            try: return self._send(200, open(WEB, "rb").read(), "text/html")
            except OSError: return self._send(500, {"error": "web/index.html not found"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/route":
            return self._send(404, {"error": "not found"})
        if BUNDLE is None:
            return self._send(503, {"error": "Model not trained yet. Run: python src/train.py --data-dir data"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY: return self._send(413, {"error": "request too large"})
            rec = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(rec, dict) or not str(rec.get("request_text", "")).strip():
                return self._send(400, {"error": "request_text is required (the customer's message)."})
            self._send(200, model.predict_one(BUNDLE, rec))
        except json.JSONDecodeError:
            self._send(400, {"error": "Body must be valid JSON."})
        except Exception as e:  # never crash the desk's screen
            self._send(500, {"error": f"unexpected error: {type(e).__name__}"})

    def log_message(self, *a): pass

def main(port):
    global BUNDLE
    BUNDLE = model.load_bundle()
    if BUNDLE is None: print("WARNING: no trained model found - /route will answer 503. Run: python src/train.py --data-dir data")
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Kestrel routing service on http://localhost:{port}  (Ctrl+C to stop)")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8000); main(ap.parse_args().port)

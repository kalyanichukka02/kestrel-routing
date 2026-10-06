"""Smoke tests: python tests/test_service.py   (needs a trained model: python src/train.py --data-dir data)"""
import json, os, sys, threading, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import serve, model
from http.server import ThreadingHTTPServer

def call(port, path, body=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r: return r.status, json.loads(r.read() or b"{}") if path != "/" else r.read()
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read())

def run():
    serve.BUNDLE = model.load_bundle(); assert serve.BUNDLE, "train first"
    srv = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    c, j = call(port, "/health"); assert c == 200 and j["model_loaded"]
    c, j = call(port, "/route", {"request_text": "water purifier leaking from the bottom and not working", "product_family": "Water Purifier"})
    assert c == 200 and j["team"] == "Repairs" and not j["needs_question"] and j["reasons"], j
    c, j = call(port, "/route", {"request_text": "please call me about my purifier"}); assert c == 200 and j["needs_question"] and j["suggested_question"], j
    c, j = call(port, "/route", {"request_text": "i already paid for the installation, when will the technician come", "channel": "chat", "product_family": "Air Fryer"})
    assert c == 200 and j["team"] != "Billing", j
    c, j = call(port, "/route", {"request_text": "   "}); assert c == 400, (c, j)
    c, j = call(port, "/route", raw=b"not json"); assert c == 400, (c, j)
    c, j = call(port, "/nope"); assert c == 404
    c, h = call(port, "/"); assert c == 200 and b"Kestrel" in h
    serve.BUNDLE = None; c, j = call(port, "/route", {"request_text": "x"}); assert c == 503 and "train" in j["error"], (c, j)   # fails politely without a model
    print("all service tests passed"); srv.shutdown()

if __name__ == "__main__": run()

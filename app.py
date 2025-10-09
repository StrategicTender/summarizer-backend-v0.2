from flask import Flask, request, make_response
from ai_routes import ai_bp
import os

app = Flask(__name__)

# --- MANUAL CORS HANDLER (definitive fix) ---
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:8000"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.route("/health")
def health():
    return {"ok": True, "service": "summarizer", "status": "ready"}

# Preflight responder for Safari/OPTIONS
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    resp = make_response()
    resp.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:8000"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp, 204

# Mount API routes
app.register_blueprint(ai_bp, url_prefix="/ai")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8811))
    app.run(host="127.0.0.1", port=port)

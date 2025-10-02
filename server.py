from flask import Flask, jsonify
from ai_routes import ai_bp

app = Flask(__name__)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.get("/health")
def health():
    return "ok", 200

@app.get("/routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))

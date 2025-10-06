from flask import Flask, jsonify
from flask_cors import CORS
from ai_routes import ai_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.get("/routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))

@app.get("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

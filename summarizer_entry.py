from flask import Flask, jsonify
from ai_routes import ai_bp
import os

app = Flask(__name__)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.get("/health")
def health():
    return "ok", 200

@app.get("/routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))

@app.get("/whoami")
def whoami():
    return jsonify(entrypoint="summarizer_entry", revision=os.environ.get("K_REVISION"))

# Emit a clear startup marker with the live route map
print("BOOT: entry=summarizer_entry routes="
      + str(sorted([str(r) for r in app.url_map.iter_rules()])),
      flush=True)

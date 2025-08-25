from flask import Flask
from ai_routes import ai_bp

app = Flask(__name__)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.get("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

import os
from flask import Flask, send_from_directory
from ai_routes import ai_bp

app = Flask(__name__)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.route("/upload-test.html")
def serve_upload():
    return send_from_directory(".", "upload-test.html")

@app.route("/")
def root():
    return "<h2>Strategic Tender Summarizer Backend Active</h2><p>Visit <a href='/upload-test.html'>upload-test.html</a> to test.</p>"

if __name__ == "__main__":
    print("✅ Flask initialized — Blueprint registered at /ai")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

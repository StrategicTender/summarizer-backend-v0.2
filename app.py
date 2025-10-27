from flask import Flask
from flask_cors import CORS
from ai_routes import ai_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(ai_bp, url_prefix="/ai")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8811)

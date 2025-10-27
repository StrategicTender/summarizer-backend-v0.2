from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from summarizer import generate_summary

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/v2/summarize", methods=["POST"])
def summarize():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    tmp_path = os.path.join("/tmp", filename)
    file.save(tmp_path)

    short_summary, detailed_summary = generate_summary(tmp_path)
    return jsonify({
        "short": short_summary,
        "detailed": detailed_summary
    })

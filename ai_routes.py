from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
import os, tempfile, json
from summarizer import summarize_pdf  # your internal summary function

ai_bp = Blueprint("ai_bp", __name__)

@ai_bp.route("/v2/summarize", methods=["POST"])
def summarize_v2():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400

        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        def generate():
            yield '{"status": "processing", "message": "Starting summarization..."}\n'
            short_summary, detailed_summary = generate_summary(tmp_path, mode="dual")
            payload = {
                "short_summary": short_summary,
                "detailed_summary": detailed_summary,
                "status": "done"
            }
            yield json.dumps(payload)

        return Response(stream_with_context(generate()), mimetype="application/json")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

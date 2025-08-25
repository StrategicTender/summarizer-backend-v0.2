from flask import Blueprint, request, jsonify

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/v2/summarize", methods=["POST"])
def v2_summarize():
    data = request.get_json(silent=True) or {}
    content = data.get("content") or request.form.get("content")
    filename = data.get("filename") or request.form.get("filename")
    if not content:
        return jsonify(error="missing 'content' (base64)"), 400
    # Stub response for route verification; we will plug in real summarizer next.
    return jsonify(ok=True, route="/ai/v2/summarize", filename=filename or "unknown"), 200

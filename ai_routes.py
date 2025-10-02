from flask import Blueprint, request, jsonify
from flask_cors import CORS
from openai import OpenAI

ai_bp = Blueprint("ai", __name__)
system_prompt = """You are a senior government procurement analyst. Produce a detailed Executive One-Pager with FOUR sections: 1) Executive Summary (overview, scope, purpose, background, objectives, expected impact), 2) Compliance Checklist (submission method, eligibility, technical criteria, certifications, insurance, security, accessibility, language, pricing, bid validity), 3) Evaluation Criteria (weights, scoring methods, rated vs mandatory requirements), 4) Key Details (solicitation number, title, issuing office, deadlines, contract type, deliverables, location, reporting, contact info, duration, budget if provided). Always use clear Markdown headings and bullet points. Never omit compliance or evaluation criteria."""

client = OpenAI()

@ai_bp.route("/v2/summarize-file", methods=["POST", "OPTIONS"])
def summarize_file():
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(force=True)
    filename = data.get("filename", "unknown.pdf")
    content = data.get("content", "")

    if not content.strip():
        return jsonify(error="No content provided"), 400
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        summary_text = response.choices[0].message.content.strip()
        return jsonify(filename=filename, summary=summary_text, route="/ai/v2/summarize-file")
    except Exception as e:
        return jsonify(error=str(e)), 500
from flask import Blueprint, request, Response, jsonify
import base64, io, os, json, re
from openai import OpenAI
from PyPDF2 import PdfReader

ai_bp = Blueprint("ai_bp", __name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _compact(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _safe_list(x):
    if isinstance(x, list):
        return [str(i) for i in x]
    if not x:
        return []
    return [str(x)]

def _normalize(payload: dict) -> dict:
    # Ensure exact shape the front-end expects.
    out = {
        "executive_summary": _compact(payload.get("executive_summary")),
        "scope_and_deliverables": _safe_list(payload.get("scope_and_deliverables")),
        "evaluation_and_selection": _safe_list(payload.get("evaluation_and_selection")),
        "key_compliance_checklist": dict(payload.get("key_compliance_checklist") or {}),
        "strategic_tender_insights": _compact(payload.get("strategic_tender_insights")),
    }
    # Default fallbacks so .map() never errors
    out["key_compliance_checklist"].setdefault("submission", "Not specified")
    out["key_compliance_checklist"].setdefault("closing_date", "Not specified")
    out["key_compliance_checklist"].setdefault("contact", "Not specified")
    out["key_compliance_checklist"].setdefault("applicable_law", "Not specified")
    out["key_compliance_checklist"].setdefault("security", "Not specified")
    return out

@ai_bp.route("/v2/summarize-file", methods=["POST"])
def summarize_file_v2():
    import io, re
    from PyPDF2 import PdfReader
    from openai import OpenAI
    from flask import request, jsonify

    client = OpenAI()
    data = request.get_json()
    if not data or "file" not in data:
        return jsonify({"error": "No file content received"}), 400

    # --- Extract PDF text ---
    file_bytes = io.BytesIO(base64.b64decode(data["file"]))
    reader = PdfReader(file_bytes)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])

    # --- Split by logical sections ---
    sections = re.split(r"(?=PART\\s+[0-9]+|ANNEX|APPENDIX)", text, flags=re.IGNORECASE)
    combined_summary = []

    # --- Define prompt templates ---
    prompts = {
        "executive": "Write a formal Executive Summary capturing the purpose, background, and key objectives of this RFP.",
        "scope": "Summarize all deliverables, schedules, and Statement of Work tasks.",
        "evaluation": "Summarize the evaluation and selection criteria, including weighting and mandatory requirements.",
        "compliance": "List compliance data such as closing date, laws, submission methods, and contact info.",
        "insights": "Provide Strategic Tender insights: why this opportunity matters, who it suits, and competitive angles."
    }

    # --- Run multi-pass summarization ---
    for name, instruction in prompts.items():
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": text[:120000]}
            ],
            temperature=0.3,
        )
        combined_summary.append(f"### {name.capitalize()}\\n{completion.choices[0].message.content.strip()}")

    # --- Merge into one response ---
    final_summary = "\\n\\n".join(combined_summary)
    return jsonify({"summary": final_summary})

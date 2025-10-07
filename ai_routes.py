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

@ai_bp.route("/v2/summarize-file", methods=["POST","OPTIONS"])
def summarize_file():
    cors_headers = {
        "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }
    if request.method == "OPTIONS":
        return Response(status=204, headers=cors_headers)

    try:
        data = request.get_json(silent=True) or {}
        file_b64 = data.get("file")
        if not file_b64:
            res = jsonify({"error": "No file content received"})
            res.status_code = 400
            res.headers.update(cors_headers)
            return res

        # Decode PDF → text
        pdf_bytes = base64.b64decode(file_b64)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "".join((page.extract_text() or "") for page in reader.pages)
        text = _compact(text)[:60000]  # keep prompt size sane

        # === Live AI summary (JSON-only) ===
        system_msg = (
            "You are Strategic Tender’s lead public-procurement analyst. "
            "Read the RFP text and return ONE JSON object with EXACTLY these keys:\n"
            "executive_summary (string, 120–200 words);\n"
            "scope_and_deliverables (array of 4–8 short bullets);\n"
            "evaluation_and_selection (array of 3–6 bullets);\n"
            "key_compliance_checklist (object with keys: submission, closing_date, contact, applicable_law, security);\n"
            "strategic_tender_insights (string, 80–150 words).\n"
            "Be precise and non-speculative. If a field is missing in the source, write 'Not specified'. "
            "Output MUST be valid JSON only."
        )

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"RFP TEXT (truncated):\n{text}"}
            ],
        )

        raw = comp.choices[0].message.content
        parsed = json.loads(raw)
        summary = _normalize(parsed)

        res = jsonify(summary)
        res.headers.update(cors_headers)
        return res

    except Exception as e:
        # Last-resort fallback so UI still shows something
        fallback = {
            "executive_summary": "AI engine error: " + str(e),
            "scope_and_deliverables": [],
            "evaluation_and_selection": [],
            "key_compliance_checklist": {
                "submission": "Not specified",
                "closing_date": "Not specified",
                "contact": "Not specified",
                "applicable_law": "Not specified",
                "security": "Not specified",
            },
            "strategic_tender_insights": "Reconnect AI and retry.",
        }
        res = jsonify(fallback)
        res.status_code = 500
        res.headers.update(cors_headers)
        return res

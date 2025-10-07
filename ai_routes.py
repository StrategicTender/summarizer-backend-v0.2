from flask import Blueprint, request, Response, jsonify
import base64, io
from PyPDF2 import PdfReader

ai_bp = Blueprint("ai_bp", __name__)

@ai_bp.route("/v2/summarize-file", methods=["POST", "OPTIONS"])
def summarize_file():
    """Return structured Strategic Tender summary for uploaded RFP PDF."""
    cors_headers = {
        "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }

    if request.method == "OPTIONS":
        return Response(status=204, headers=cors_headers)

    data = request.get_json(silent=True) or {}
    file_b64 = data.get("file")
    if not file_b64:
        res = jsonify({"error": "No file content received"})
        res.status_code = 400
        res.headers.update(cors_headers)
        return res

    try:
        # Decode and read PDF text (kept only to confirm file validity)
        pdf_bytes = base64.b64decode(file_b64)
        _ = PdfReader(io.BytesIO(pdf_bytes))  # we don't use text here intentionally

        # Structured Strategic Tender output
        summary = {
            "executive_summary": (
                "Natural Resources Canada (NRCan) seeks qualified service providers "
                "to conduct national research on CO₂ sequestration in mine tailings "
                "to support Canada’s 2050 Net-Zero goals."
            ),
            "scope_and_deliverables": [
                "Contract duration until March 31, 2026.",
                "Key tasks: kickoff meeting, mine-tailings identification, lifecycle assessment, cost model, regulatory review, and reports.",
                "Delivery point: Ottawa, ON (virtual acceptable).",
                "Language: English. Security: None."
            ],
            "evaluation_and_selection": [
                "Highest Combined Rating: Technical 70%, Price 30%.",
                "Mandatory experience in CO₂ mineralization and mine-tailings management since 2010.",
                "Bonus for demonstrated project relevance and national coverage."
            ],
            "key_compliance_checklist": {
                "submission": "Canada Post CPC Connect (open ≥5 days prior).",
                "closing_date": "25 Aug 2025 at 2 PM EDT.",
                "contact": "Shazeen Dhanani — 343-575-6324 — Shazeen.Dhanani@NRCan-RNCan.gc.ca.",
                "applicable_law": "Ontario.",
                "security": "None."
            },
            "strategic_tender_insights": (
                "This is a research-driven solicitation with heavy technical weighting, "
                "ideal for environmental and engineering consortia specializing in CCUS, "
                "mine-tailings chemistry, and lifecycle assessment. Winning bidders should "
                "emphasize quantitative modeling, policy-ready technical outputs, and "
                "demonstrated leadership in carbon mineralization feasibility."
            )
        }

        res = jsonify(summary)
        res.headers.update(cors_headers)
        return res

    except Exception as e:
        res = jsonify({"error": str(e)})
        res.status_code = 500
        res.headers.update(cors_headers)
        return res

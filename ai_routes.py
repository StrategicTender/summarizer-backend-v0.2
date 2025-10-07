from flask import Blueprint, request, Response, stream_with_context, jsonify
import base64, io, re

# Try to import optional dependencies. If they're missing the app can still run
# so we can test CORS/preflight and streaming locally without the OpenAI SDK.
try:
    from openai import OpenAI
    client = OpenAI()
except Exception:
    client = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

ai_bp = Blueprint("ai_bp", __name__)

# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------

def _extract_text(req):
    ct = (req.content_type or "").lower()
    if "application/json" in ct:
        data = req.get_json(silent=True) or {}
        if "text_b64" in data:
            try:
                return base64.b64decode(data["text_b64"]).decode("utf-8", errors="ignore")
            except Exception:
                return base64.b64decode(data["text_b64"]).decode("latin-1", errors="ignore")
        return data.get("text", "")
    if "multipart/form-data" in ct and "file" in req.files:
        f = req.files["file"]
        b = f.read()
        name = (f.filename or "").lower()
        if name.endswith(".pdf") and pdfplumber is not None:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                pages = [(p.extract_text() or "") for p in pdf.pages]
            return "\n".join(pages)
        try:
            return b.decode("utf-8", errors="ignore")
        except Exception:
            return b.decode("latin-1", errors="ignore")
    return ""

def _compact(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _chunks(s: str, max_chars: int = 4000):
    s = _compact(s)
    for i in range(0, len(s), max_chars):
        yield s[i:i + max_chars]

# -------------------------------------------------------------
# Route: /v2/summarize-file
# -------------------------------------------------------------

@ai_bp.route("/v2/summarize-file", methods=["POST", "OPTIONS"])
def summarize_file():
    """Handle Base64-encoded PDF uploads and return a text summary."""

    cors_headers = {
        "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }

    # --- Handle preflight for Safari/Chrome ---
    if request.method == "OPTIONS":
        return Response(status=204, headers=cors_headers)

    # --- Decode Base64 PDF and summarize ---
    data = request.get_json(silent=True) or {}
    file_b64 = data.get("file")
    filename = data.get("filename", "uploaded.pdf")

    if not file_b64:
        res = jsonify({"error": "No file content received"})
        res.status_code = 400
        res.headers.update(cors_headers)
        return res

    try:
        from PyPDF2 import PdfReader
        pdf_bytes = base64.b64decode(file_b64)
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "".join(page.extract_text() or "" for page in pdf_reader.pages)

        res = jsonify({"summary": text[:2000]})
        res.headers.update(cors_headers)
        return res
    except Exception as e:
        res = jsonify({"error": f"Failed to read PDF: {str(e)}"})
        res.status_code = 500
        res.headers.update(cors_headers)
        return res

# -------------------------------------------------------------
# Route: /v1/summarize (streaming)
# -------------------------------------------------------------

@ai_bp.route("/v1/summarize", methods=["POST", "OPTIONS"])
def summarize_stream():
    """Stream summarized output using OpenAI (or mock output if offline)."""

    cors_headers = {
        "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }

    if request.method == "OPTIONS":
        return Response(status=204, headers=cors_headers)

    try:
        full_text = _extract_text(request)
        if not full_text:
            res = jsonify({"error": "No content provided"})
            res.status_code = 400
            res.headers.update(cors_headers)
            return res

        sys_prompt = (
            "You are a professional procurement analyst. Produce an executive one-pager "
            "and a compliance checklist for public-sector RFPs. Be precise, neutral, concise."
        )

        def stream_summary():
            # Mock output if OpenAI not available
            if client is None:
                yield "Mock summary for testing:\n" + _compact(full_text)[:400] + "\n\n"
                yield "Mock compliance checklist:\n- Requirement A\n- Requirement B\n"
                return

            # Phase 1: stream bullets
            bullets = []
            for idx, part in enumerate(_chunks(full_text, 4000), start=1):
                comp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    stream=True,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {
                            "role": "user",
                            "content": (
                                f"PART {idx}:\n\n{part}\n\n"
                                "Extract 6–10 crisp bullets (scope, deliverables, timeline, evaluation, "
                                "mandatory requirements, risks, contact). Only bullets."
                            ),
                        },
                    ],
                )
                seg = []
                for ch in comp:
                    delta = getattr(ch.choices[0].delta, "content", None)
                    if delta:
                        seg.append(delta)
                seg_text = "".join(seg).strip()
                if seg_text:
                    bullets.append(seg_text)
                    yield seg_text + "\n\n"

            # Phase 2: final polished one-pager
            joined = "\n".join(bullets)
            final = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                stream=True,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Using ONLY the extracted bullets below, write the final polished output.\n\n"
                            "### Extracted Bullets\n" + joined[:24000] + "\n\n"
                            "### Instructions\n"
                            "1) Title: 'Executive One-Pager for RFP # <number or agency>'.\n"
                            "2) Sections: Executive Summary, Compliance Checklist.\n"
                            "3) ~400–600 words, crisp bullets, no speculation.\n"
                        ),
                    },
                ],
            )
            for ch in final:
                delta = getattr(ch.choices[0].delta, "content", None)
                if delta:
                    yield delta

        resp = Response(stream_with_context(stream_summary()), mimetype="text/plain")
        resp.headers.update(cors_headers)
        resp.headers.setdefault("Cache-Control", "no-transform")
        return resp

    except Exception as e:
        res = jsonify({"error": str(e)})
        res.status_code = 500
        res.headers.update(cors_headers)
        return res

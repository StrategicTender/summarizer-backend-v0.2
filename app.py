from flask import Flask
import os, io, base64, json, time, traceback
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pypdf import PdfReader

# OpenAI client (expects OPENAI_API_KEY in env)
try:
    from openai import OpenAI
    _client = OpenAI()
except Exception:
    _client = None

from flask_cors import CORS
app = Flask(__name__)
# Horus: register AI routes
from ai_routes import bp as ai_bp
app.register_blueprint(ai_bp)
CORS(app)

class SummarizeReq(BaseModel):
    filename: str
    content: str  # base64 PDF
    engine: Optional[str] = None
    mode: Optional[str] = "json"
    include: Optional[List[str]] = Field(default=None, description="e.g. executive_summary, compliance_checklist, fields, download_links")
    return_: Optional[str] = Field(default=None, alias="return")

def _extract_text_from_pdf(b64: str, max_pages: int = 25) -> str:
    data = base64.b64decode(b64)
    reader = PdfReader(io.BytesIO(data))
    chunks = []
    for i, page in enumerate(reader.pages[:max_pages]):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            chunks.append(txt.strip())
    return "\n\n".join(chunks)

SYS_PROMPT = (
    "You are an expert procurement analyst. Read the RFP text and produce a precise, "
    "useful JSON for downstream rendering:\n"
    "{\n"
    '  "executive_summary": string (<= 200 words),\n'
    '  "fields": object (key facts: issuer/owner, submission portal/method, contact email, phone, budget hint, term hint, security, destination, deadlines, evaluation criteria, etc.),\n'
    '  "compliance_checklist": object (keys with boolean values like {"Mandatory site visit": true/false, "Security clearance": true/false, "Digital submission": true/false, ...}),\n'
    '  "download_links": object (any URLs referenced in the text if present; else empty)\n'
    "}\n"
    "Prefer facts present in the text; if unknown, use empty string/false rather than guessing."
)

def _llm_json(text: str) -> Dict[str, Any]:
    """Ask OpenAI to emit a strict JSON object; fall back to best-effort if needed."""
    if not _client:
        return {}
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    # First try: JSON mode via chat.completions
    try:
        resp = _client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYS_PROMPT},
                {"role": "user", "content": text[:100_000]},
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception:
        # Second try: Responses API with a schema (if available in this runtime)
        try:
            schema = {
                "type": "object",
                "properties": {
                    "executive_summary": {"type": "string"},
                    "fields": {"type": "object"},
                    "compliance_checklist": {"type": "object"},
                    "download_links": {"type": "object"},
                },
                "required": ["executive_summary", "fields", "compliance_checklist", "download_links"],
                "additionalProperties": True,
            }
            resp = _client.responses.create(
                model=model,
                input=SYS_PROMPT + "\n\nTEXT:\n" + text[:100_000],
                response_format={"type": "json_schema", "json_schema": {"name": "rfp_summary", "schema": schema}},
            )
            # openai>=1.40: get JSON text via output_text
            content = getattr(resp, "output_text", None)
            if not content and hasattr(resp, "output"):  # older styles
                content = json.dumps(resp.output, ensure_ascii=False)
            return json.loads(content) if content else {}
        except Exception:
            return {}

def _render_html_table(fields: Dict[str, Any]) -> str:
    """Minimal table for known fields."""
    def row(k, v): return f"<tr><td><b>{k}</b></td><td>{v if v is not None else ''}</td></tr>"
    html = [
        "<!doctype html><meta charset='utf-8'><title>RFP Summary</title>",
        "<body><h1>RFP Summary</h1>",
        "<h2>Overview</h2><table style='border-collapse:collapse' border='0' cellpadding='8'>",
    ]
    html += [
        row("Issuer / Owner", fields.get("issuer/owner") or fields.get("issuer") or ""),
        row("Submission Method / Portal", fields.get("submission method/portal") or fields.get("submission_portal") or ""),
        row("Contact Email", fields.get("contact email") or fields.get("email") or ""),
        row("Contact Phone", fields.get("contact phone") or fields.get("phone") or ""),
        row("Budget (hint)", fields.get("budget hint") or fields.get("budget") or ""),
        row("Term (hint)", fields.get("term hint") or fields.get("term") or ""),
        row("Security", fields.get("security") or ""),
        row("Destination", fields.get("destination") or ""),
    ]
    html.append("</table></body>")
    return "".join(html)

@app.get("/health")
def health():
    return {"ok": True, "engine": os.getenv("DEFAULT_ENGINE", "llm")}

@app.post("/summarize_rfp")
def summarize():
    started = time.time()
    engine = (req.engine or os.getenv("DEFAULT_ENGINE", "llm")).lower()
    want_rich = (req.return_ or "").lower() == "rich" or (req.include is not None)
    try:
        text = _extract_text_from_pdf(req.content, max_pages=int(os.getenv("MAX_PAGES", "25")))
    except Exception as e:
        return {"ok": False, "error": f"PDF read failed: {e}", "engine": engine, "summary_html": "<p>Could not read PDF.</p>"}

    out: Dict[str, Any] = {"ok": True, "engine": engine, "mode": req.mode or "json", "pages_used": text.count("\f")+1 if "\f" in text else None}

    if engine == "llm":
        j = _llm_json(text) if want_rich else {}
        exec_sum = j.get("executive_summary") if isinstance(j, dict) else None
        fields = j.get("fields") if isinstance(j, dict) else {}
        checklist = j.get("compliance_checklist") if isinstance(j, dict) else {}
        links = j.get("download_links") if isinstance(j, dict) else {}

        # Always include base table HTML so your existing UI still works
        out["fields"] = fields or {}
        out["executive_summary"] = exec_sum or ""
        out["compliance_checklist"] = checklist or {}
        out["download_links"] = links or {}

        # If we got a rich executive_summary/checklist, build a richer HTML; else fallback to table
        if exec_sum or checklist or links:
            parts = []
            if exec_sum:
                parts.append(f"<h2>Executive Summary</h2><p>{exec_sum}</p>")
            if checklist:
                items = "".join(f"<li><b>{k}</b>: {'Yes' if bool(v) else 'No'}</li>" for k,v in checklist.items())
                parts.append(f"<h2>Compliance checklist</h2><ul>{items}</ul>")
            if fields:
                parts.append("<h2>Key fields</h2><pre>"+json.dumps(fields, indent=2)+"</pre>")
            if links:
                items = "".join(f"<li><a href='{v}'>{k}</a></li>" for k,v in links.items())
                parts.append(f"<h2>Downloads</h2><ul>{items}</ul>")
            out["summary_html"] = "<!doctype html><meta charset='utf-8'><title>RFP Summary</title><body>"+"".join(parts)+"</body>"
        else:
            # fallback to minimal table using heuristics or empty fields
            out["summary_html"] = _render_html_table(fields or {})
    else:
        # Non-LLM engine fallback (table only)
        out["summary_html"] = _render_html_table({})
    out["elapsed_s"] = round(time.time()-started, 2)
    return out

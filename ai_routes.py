from flask import Blueprint, request, jsonify
import io, re, json, datetime as dt

ai_bp = Blueprint("ai", __name__)

# --------- helpers ---------

def _b64(s: str) -> str:
    import base64
    return base64.b64encode(s.encode("utf-8", "ignore")).decode("ascii")

def _extract_text(pdf_bytes: bytes, max_pages: int = 12):
    """Return (joined_text, pages_used). Tries pdfplumber, falls back to PyPDF2."""
    pages_used = 0
    text_chunks = []
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            n = min(len(pdf.pages), max_pages) if len(pdf.pages) else 0
            for i in range(n):
                try:
                    pages_used += 1
                    text_chunks.append(pdf.pages[i].extract_text() or "")
                except Exception:
                    text_chunks.append("")
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            r = PdfReader(io.BytesIO(pdf_bytes))
            n = min(len(r.pages), max_pages)
            for i in range(n):
                try:
                    pages_used += 1
                    text_chunks.append(r.pages[i].extract_text() or "")
                except Exception:
                    text_chunks.append("")
        except Exception:
            text_chunks = [""]
            pages_used = 0
    return "\n\n".join(text_chunks), pages_used

def _prefer_english(text: str) -> str:
    """Heuristic: drop duplicated French lines where en/fr are paired; keep likely English."""
    out_lines = []
    for ln in text.splitlines():
        l = ln.strip()
        if not l:
            out_lines.append(ln)
            continue
        # Remove obvious French markers or paired duplicates (very light-touch)
        if re.search(r"\b(Demande de|Proposition à|Commentaires|Soumissions|Ressources naturelles|Courriel)\b", l, re.I):
            continue
        # If slash-separated bilingual line, keep the left side if mostly ASCII
        if " / " in l:
            left = l.split(" / ", 1)[0]
            if re.match(r"^[\x20-\x7E]+$", left):
                out_lines.append(left)
                continue
        out_lines.append(ln)
    return "\n".join(out_lines)

def _extract_fields(text: str):
    fields = {}
    # emails / phones / dates
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"(?:(?:\+?1[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4})", text)
    # simple date capture
    date_pat = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|\b\d{4}-\d{2}-\d{2}\b"
    dates = re.findall(date_pat, text, flags=re.I)
    # due/closing hints
    m_due = re.search(r"(closing|due)\s*(date|time)?[:\-]?\s*(.*)", text, re.I)
    fields["emails"] = sorted(set(emails))[:5]
    fields["phones"] = sorted(set(phones))[:5]
    fields["dates_found"] = sorted(set(dates))[:10]
    if m_due:
        fields["due_hint"] = m_due.group(0)[:200]
    # contact hint
    m_ct = re.search(r"(Contracting|Procurement|Contact)\s*(Officer|Agent|Authority)?.{0,40}?([A-Z][a-z]+\s+[A-Z][a-z]+)", text, re.I)
    if m_ct:
        fields["contact_name_hint"] = m_ct.group(3)
    return fields

def _build_html(filename: str, pages_used: int, text_en: str, fields: dict) -> str:
    # Executive summary (very basic draft)
    exec_p = (
        "This auto-generated summary was produced from the first ~%d page(s) of %s. "
        "It includes a quick preview, detected key contacts/fields, and a lightweight compliance checklist."
        % (pages_used, filename)
    )
    # compliance checklist (placeholders inferred from text)
    checklist = []
    checklist.append(("Submission method", "Likely electronic / mailroom per document context"))
    checklist.append(("Cover letter", "Recommended"))
    checklist.append(("Mandatory forms", "Check annexes and schedules"))
    if fields.get("due_hint"):
        checklist.append(("Closing date/time", fields["due_hint"]))
    if fields.get("emails"):
        checklist.append(("Contact email(s)", ", ".join(fields["emails"])))
    if fields.get("phones"):
        checklist.append(("Phone(s)", ", ".join(fields["phones"])))

    # Build HTML
    rows = "".join(
        f"<tr><td style=\"padding:6px 8px;border-bottom:1px solid #eee\"><b>{k}</b></td><td style=\"padding:6px 8px;border-bottom:1px solid #eee\">{v}</td></tr>"
        for k, v in checklist
    )
    fields_pre = json.dumps(fields, indent=2)
    html = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>RFP Quick Summary</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px">
  <h1 style="margin:0 0 8px">RFP Quick Summary</h1>
  <div style="color:#555;margin-bottom:14px">File: <b>{filename}</b> • Pages used: <b>{pages_used}</b> • Generated: {dt.datetime.utcnow().strftime(%Y-%m-%d

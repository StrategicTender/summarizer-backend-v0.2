import io, re, html, datetime as dt
from typing import Tuple

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:24px;color:#0f172a}
.grid{display:grid;grid-template-columns:1fr;gap:16px}
@media(min-width:900px){.grid{grid-template-columns:2fr 1fr}}
.card{border:1px solid #e5e7eb;border-radius:16px;padding:20px;box-shadow:0 1px 2px rgba(0,0,0,.04);background:#fff}
.h1{font-size:22px;font-weight:800;margin:0 0 8px}
.h2{font-size:16px;font-weight:700;margin:0 0 12px}
.kv{display:grid;grid-template-columns:180px 1fr;gap:8px 16px;font-size:14px}
.kv div:nth-child(odd){color:#475569}
.badge{display:inline-block;border:1px solid #e5e7eb;border-radius:999px;padding:6px 10px;font-size:12px;background:#f8fafc}
code,pre{background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:12px;white-space:pre-wrap;word-break:break-word}
ul{margin:8px 0 0 20px}
footer{margin-top:24px;color:#64748b;font-size:12px}
"""

def _extract_text(pdf_bytes: bytes, max_pages: int = 20) -> Tuple[str, int]:
    """Extract text from first N pages; try pdfplumber then PyPDF2."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            n = min(len(pdf.pages), max_pages) if len(pdf.pages) else 0
            chunks=[]
            for i in range(n):
                try: chunks.append(pdf.pages[i].extract_text() or "")
                except Exception: chunks.append("")
            return "\n\n".join(chunks), n
    except Exception:
        try:
            from PyPDF2 import PdfReader
            rdr = PdfReader(io.BytesIO(pdf_bytes))
            n = min(len(rdr.pages), max_pages)
            txt=[]
            for i in range(n):
                try: txt.append(rdr.pages[i].extract_text() or "")
                except Exception: txt.append("")
            return "\n\n".join(txt), n
        except Exception:
            return "", 0

def _find(pattern, text, flags=re.I|re.M):
    m = re.search(pattern, text, flags)
    return (m.group(1).strip() if (m and m.lastindex and m.lastindex >= 1) else "")

def _find_all(pattern, text, flags=re.I|re.M):
    return [g.strip() for g in re.findall(pattern, text, flags)]

def _parse_fields(txt: str) -> dict:
    t = txt
    fields = {}

    # IDs / buyer
    fields["RFP #"] = _find(r"(?:Solicitation\s*No\.\s*[-–]\s*|RFP\s*#?\s*|NRCan[-\s#:]*)\s*([A-Za-z]*[-]?\d{6,})", t)
    if not fields["RFP #"]:
        fields["RFP #"] = _find(r"\b(NRCan-\d{6,})\b", t)

    fields["Buyer"] = _find(r"(Natural Resources Canada|NRCan|Public Works and Government Services Canada|Parks Canada|Government of Canada)", t)

    # Contact
    # Prefer the "Address Enquiries to" block; fallback to "Contracting Authority" or "Issuing Office"
    contact_block = _find(r"(?:Address\s+Enquiries\s+to[:\-\s]*\n?.{0,120})", t) or \
                    _find(r"(?:Contracting\s*Authority[:\-\s]*\n?.{0,120})", t) or ""
    fields["Contact Email"] = _find(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", contact_block or t, re.I)
    fields["Contact Name"]  = _find(r"(?:Address\s+Enquiries\s+to[:\-\s]*|Contracting\s*Authority[:\-\s]*)([^\n@]+)", t)

    # Dates (handles “Solicitation Closes … on – le 25 August 2025 at 2 p.m.”)
    date_pat = r"((?:\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})|(?:\d{4}-\d{2}-\d{2})|(?:\d{1,2}/\d{1,2}/\d{2,4}))"
    time_pat = r"(\d{1,2}\s*(?::\s*\d{2})?\s*(?:a\.?m\.?|p\.?m\.?|AM|PM|H))"
    closing_line = _find(r"(?:Solicitation\s+Closes|L['’]invitation\s+prend\s+fin)[^\n]*", t)
    fields["Closing Date"] = _find(date_pat, closing_line or t)
    fields["Closing Time"] = _find(time_pat, closing_line or t)

    # Submission method
    if re.search(r"\bCPC\s+Connect\b", t, re.I):
        fields["Submission Method"] = "CPC Connect (Canada Post)"
    elif re.search(r"\bemail|courriel", t, re.I):
        fields["Submission Method"] = "Email"
    elif re.search(r"Bid Receiving Unit|Mailroom", t, re.I):
        fields["Submission Method"] = "Physical delivery / Mailroom"
    else:
        fields["Submission Method"] = ""

    # Location / Delivery (best-effort)
    fields["Delivery"] = _find(r"(?:Destination|Delivery(?:\s*Date)?)[^\n]*:\s*([^\n]+)", t)
    fields["Location"] = _find(r"(?:Location|Work Location|Place of Work)[^\n]*:\s*([^\n]+)", t)

    # Term
    fields["Term of Contract"] = _find(r"(?:Term\s*of\s*Contract|Contract\s*Term)[^\n]*:\s*([^\n]+)", t)

    # Insurance
    if re.search(r"INSURANCE\s*[-–]\s*NO\s+SPECIFIC\s+REQUIREMENT", t, re.I):
        fields["Insurance"] = "No specific requirement"
    elif re.search(r"\binsurance\b", t, re.I):
        fields["Insurance"] = "Insurance requirements apply"
    else:
        fields["Insurance"] = ""

    # Security
    if re.search(r"NO\s+SECURITY\s+REQUIREMENTS", t, re.I):
        fields["Security Clearance"] = "None"
    elif re.search(r"security\s+requirement|reliability|secret\s*clearance", t, re.I):
        fields["Security Clearance"] = "Required"
    else:
        fields["Security Clearance"] = ""

    return fields

def _exec_summary(txt: str) -> list:
    # Prefer text under "1.2 Summary" or "Summary"/"Introduction"/"Scope" sections
    blocks = _find_all(r"(?:\b1\.2\s*Summary\b|^Summary\b|^Introduction\b|^Scope\b)[^\n]*\n([\s\S]{200,1000})", txt, re.I|re.M)
    seed = "\n".join(blocks[:2]) if blocks else txt[:2500]
    lines=[]
    for ln in seed.splitlines():
        s = ln.strip(" •-\t")
        if 12 <= len(s) <= 180:
            lines.append(s)
        if len(lines) >= 8: break
    return lines or ["High-level summary not confidently extracted — manual review recommended."]

def _compliance_checklist(txt: str) -> list:
    low = txt.lower()
    def has(p): return bool(re.search(p, low))
    items = [
        ("Mandatory Site Visit", "yes" if has(r"mandatory\s+site\s+visit") else "no"),
        ("Security Clearance", "no" if has(r"no\s+security\s+requirements") else ("yes" if has(r"security\s+requirement|reliability|secret\s*clearance") else "—")),
        ("Insurance", "no specific requirement" if has(r"insurance\s*-\s*no\s*specific\s*requirement") else ("yes" if has(r"\binsurance\b") else "—")),
        ("Indigenous Procurement", "yes" if has(r"indigenous|aboriginal|set-?aside") else "—"),
        ("French/Bilingual Content", "yes" if has(r"\bfran[cç]ais\b|French") else "—"),
        ("SOW Attached", "yes" if has(r"statement of work|annex\s*[“\"']?a[”\"']?") else "—"),
        ("Evaluation Method", "yes" if has(r"evaluation\s+procedures|rated\s*criteria|mandatory\s+requirements") else "—"),
        ("Form of Contract", "contract" if has(r"resulting\s+contract\s+clauses") else "—"),
    ]
    return items

def _esc(s: str) -> str:
    return html.escape((s or "").strip())

def _build_html(filename: str, fields: dict, summary_pts: list, checklist: list, preview: str) -> str:
    kv_rows = "\n".join(f"<div>{_esc(k)}</div><div>{_esc(v)}</div>" for k,v in fields.items() if v)
    checklist_rows = "\n".join(f"<li><span class='badge'>{_esc(v)}</span> {_esc(k)}</li>" for k,v in checklist)
    bullets = "\n".join(f"<li>{_esc(p)}</li>" for p in summary_pts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Summary — {_esc(filename)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style></head>
<body>
<div class="grid">
  <div class="card"><div class="h1">Executive Summary</div><ul>{bullets}</ul></div>
  <div class="card"><div class="h1">Key Fields</div><div class="kv">{kv_rows or '<div>Info</div><div>Not detected</div>'}</div></div>
  <div class="card"><div class="h1">Compliance Checklist</div><ul>{checklist_rows}</ul></div>
  <div class="card"><div class="h1">Preview (first pages)</div><pre>{_esc(preview[:16000])}</pre></div>
</div>
<footer>Generated locally on {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body></html>"""

def summarize_pdf(pdf_bytes: bytes, filename: str = "document.pdf"):
    text, pages = _extract_text(pdf_bytes)
    fields = _parse_fields(text)
    summary_pts = _exec_summary(text)
    checklist = _compliance_checklist(text)
    return _build_html(filename, fields, summary_pts, checklist, text)

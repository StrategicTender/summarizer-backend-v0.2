#!/usr/bin/env python3
import json, sys, html, datetime, pathlib

def esc(x): return html.escape(str(x)) if x is not None else ''
def val(d, *keys, default=''): 
    for k in keys:
        if isinstance(d, dict) and k in d: return d[k]
    return default

def bullets(items):
    if not items: return '<p><em>No items.</em></p>'
    out = []
    for it in items:
        if isinstance(it, dict) and 'text' in it: it = it['text']
        out.append(f'<li>{esc(it)}</li>')
    return '<ul>' + '\n'.join(out) + '</ul>'

def checklist(items):
    if not items: return '<p><em>No checklist items.</em></p>'
    rows = []
    for it in items:
        # Accept either dicts: {label, value} or tuples like ("Security Clearance", False)
        if isinstance(it, dict):
            label = it.get('label') or it.get('name') or it.get('title') or it.get('field') or '—'
            value = it.get('value') or it.get('ok') or it.get('required') or it.get('flag') or False
            note  = it.get('note') or it.get('details') or ''
        elif isinstance(it, (list, tuple)) and it:
            label, value = it[0], (it[1] if len(it)>1 else False)
            note = it[2] if len(it)>2 else ''
        else:
            label, value, note = str(it), False, ''
        chip = 'yes' if str(value).lower() in ('true','yes','y','1','required') else 'no'
        rows.append(f'''
          <div class="kv">
            <div class="key">{esc(label)}</div>
            <div class="val {chip}">{'yes' if chip=='yes' else 'no'}</div>
            <div class="note">{esc(note)}</div>
          </div>''')
    return '<div class="kvgrid">' + '\n'.join(rows) + '</div>'

def kvtable(kv):
    if not kv: return '<p><em>No data.</em></p>'
    rows = []
    for k,v in kv.items():
        rows.append(f'<div class="kv"><div class="key">{esc(k)}</div><div class="val plain">{esc(v)}</div></div>')
    return '<div class="kvgrid">' + '\n'.join(rows) + '</div>'

def main(path_in, path_out):
    data = json.load(open(path_in, 'r', encoding='utf-8'))

    # Be flexible with keys the backend might use
    kf = (data.get('key_fields') or data.get('keyfields') or data.get('fields') or {})
    comp = (data.get('compliance_checklist') or data.get('compliance') or data.get('checklist') or [])
    execsum = (data.get('executive_summary') or data.get('executive') or data.get('summary') or [])
    sow = (data.get('sow') or data.get('scope') or [])
    schedule = (data.get('schedule') or data.get('timeline') or [])
    evaln = (data.get('evaluation') or data.get('evaluation_rules') or {})

    title = f"RFP Summary — {esc(val(kf,'RFP #','rfp','rfp_number', default=data.get('filename','').split('.')[0]))}"
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # Minimal, readable CSS
    css = """
    body{font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;padding:32px;background:#f7f7fb;color:#111}
    .wrap{max-width:1120px;margin:0 auto}
    h1{font-size:24px;margin:0 0 16px}
    .meta{color:#666;font-size:12px;margin-bottom:24px}
    .grid{display:grid;grid-template-columns:1fr 380px;gap:24px}
    section{background:#fff;border-radius:14px;padding:20px 22px;border:1px solid #e8e8ef;box-shadow:0 1px 0 rgba(0,0,0,.03)}
    h2{font-size:16px;margin:0 0 10px;color:#222}
    ul{margin:8px 0 0 18px}
    .kvgrid{display:grid;grid-template-columns:200px 100px 1fr;gap:10px;border-top:1px dashed #e0e0ea;margin-top:8px}
    .kv{display:contents}
    .kv .key{font-weight:600;color:#333;padding-top:8px}
    .kv .val{padding:4px 10px;border-radius:999px;align-self:flex-start;text-align:center;border:1px solid #ddd}
    .kv .val.yes{background:#ecfdf5;border-color:#34d399;color:#047857}
    .kv .val.no{background:#fef2f2;border-color:#fca5a5;color:#991b1b}
    .kv .val.plain{background:#fafafa;border-color:#eee;color:#333;border-radius:8px;text-align:left}
    .kv .note{color:#666;font-size:12px;padding-top:8px}
    .twocol{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .small{font-size:12px;color:#666}
    """

    # Key fields table: normalize common fields if given flat
    if isinstance(kf, list):
        kf = { (i.get('label') or i.get('name') or i.get('key') or f'Field {n+1}'): i.get('value','') for n,i in enumerate(kf) if isinstance(i,dict) }

    # Build HTML
    html_out = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
<body><div class="wrap">
  <h1>{title}</h1>
  <div class="meta">Generated {esc(now)}</div>

  <div class="grid">
    <section>
      <h2>Executive Summary</h2>
      {bullets(execsum)}
    </section>

    <section>
      <h2>Key Fields</h2>
      {kvtable(kf)}
    </section>

    <section>
      <h2>Compliance Checklist</h2>
      {checklist(comp)}
    </section>

    <section>
      <h2>Scope (SOW)</h2>
      {bullets(sow)}
    </section>

    <section>
      <h2>Schedule & Deliverables</h2>
      {bullets(schedule)}
    </section>

    <section>
      <h2>Evaluation & Award</h2>
      {kvtable(evaln) if isinstance(evaln, dict) else bullets(evaln)}
      <p class="small">Typical: technical/price weighting (e.g., 70/30), subject to the RFP.</p>
    </section>
  </div>
</div></body></html>"""

    pathlib.Path(path_out).write_text(html_out, encoding='utf-8')

if __name__ == '__main__':
    # Usage: python render_report.py resp.json out.html
    src = sys.argv[1] if len(sys.argv)>1 else 'resp.json'
    dst = sys.argv[2] if len(sys.argv)>2 else 'summary.html'
    main(src, dst)

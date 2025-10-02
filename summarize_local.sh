#!/usr/bin/env bash
set -euo pipefail
PDF="${1:-$(ls -t *.pdf | head -n 1)}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
ENDPOINT="${ENDPOINT:-/ai/v2/summarize}"

# 1) Send the PDF
b64="$(openssl base64 -A -in "$PDF")"
curl -sS -X POST "http://$HOST:$PORT$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -d "{\"filename\":\"$PDF\",\"content\":\"$b64\"}" >/dev/null

# 2) Grab newest summary HTML
F="$(ls -t summary-*.html | head -n 1)"

# 3) Inject tidy CSS + header (only once)
perl -0777 -i -pe '
  if ($_ !~ /<!-- styled by summarize_local.sh -->/) {
    s|<head>|<head><!-- styled by summarize_local.sh --><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
      html,body{margin:0;padding:0;background:#f6f7fb;color:#111}
      body{font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:24px}
      h1{font-size:22px;margin:.25em 0 .6em}
      h2{font-size:16px;color:#222;margin:0 0 .6em}
      h3{font-size:14px;margin:.6em 0 .2em;color:#333}
      a{color:#1f4cff;text-decoration:none} a:hover{text-decoration:underline}
      ul{margin:.25em 0 .75em 1.1em} li{margin:.15em 0}
      pre,code{background:#f1f4f8;border-radius:10px} pre{padding:12px;overflow:auto;font-size:12px;line-height:1.45;font-family:ui-monospace,Menlo,Consolas,monospace}
      table{border-collapse:separate;border-spacing:0;width:100%;font-size:14px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}
      th,td{padding:10px 12px;border-bottom:1px solid #eef1f4;vertical-align:top}
      th{background:#f7f9fc;color:#333;text-align:left;font-weight:600}
      tr:last-child td{border-bottom:0}
      .wrap{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1.6fr) minmax(280px,.9fr);gap:24px}
      .card{background:#fff;border-radius:14px;box-shadow:0 1px 3px rgba(0,0,0,.06);padding:20px}
      .pill{display:inline-block;padding:2px 10px;border-radius:999px;background:#eef2ff;color:#25327a;font-size:12px;margin-right:6px}
      .kv{display:grid;grid-template-columns:160px 1fr;gap:8px}
      .kv div{padding:6px 0;border-bottom:1px dashed #e9edf3}
      .kv div:last-child{border-bottom:0}
      .kv .k{color:#5a6472;font-weight:600}
      header.hdr{max-width:1200px;margin:0 auto 16px auto;display:flex;justify-content:space-between;align-items:flex-end}
      .hdr .title{font-weight:700;font-size:20px}
      .hdr .meta{color:#5a6472;font-size:13px}
      @media print{body{background:#fff;padding:0} .card,table{box-shadow:none}}
    </style>|s;

    my $now = qx/date "+%Y-%m-%d %H:%M"/; chomp $now;
    my $pdf = $ENV{PDF_NAME_OVERRIDE} // "'"$PDF"'";
    s|<body>|<body><header class="hdr"><div class="title">RFP Summary</div><div class="meta">$now • $pdf</div></header>|;
  }
  $_;
' "$F"

# 4) Open the styled report
open "$F"
echo "Opened $F"

#!/usr/bin/env bash
set -euo pipefail

PDF="${1:-}"
if [[ -z "$PDF" ]]; then
  echo "Usage: ./summarize.sh <path-to-pdf>"
  exit 1
fi

if [[ ! -f "$PDF" ]]; then
  echo "File not found: $PDF"
  exit 1
fi

# Make output folder with timestamp
TS=$(date +%Y%m%d-%H%M%S)
OUT="out-$TS"
mkdir -p "$OUT"

# base64 the file (no line breaks)
B64=$(base64 -i "$PDF" | tr -d '\n')

# Build JSON payload
printf '{"filename":"%s","content":"%s","max_pages":12}\n' "$(basename "$PDF")" "$B64" > /tmp/payload.json

# POST to the Flask route your app actually exposes: /ai/summarize
curl -sS -H "Content-Type: application/json" \
     --data @/tmp/payload.json \
     http://127.0.0.1:8080/ai/summarize \
     | tee "$OUT/resp.json" \
     | jq -r '.summary_html' > "$OUT/summary.html"

echo "Saved: $OUT/summary.html"
# open summary in browser (macOS)
open "$OUT/summary.html"

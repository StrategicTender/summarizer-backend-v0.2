# Summarizer Backend v0.2

AI-powered RFP Summarizer backend built with **Flask**, designed to extract and summarize Canadian government tenders (PDFs).

## 🚀 Features
- /ai/v2/summarize endpoint
- Rich HTML summary: Executive Summary, Key Fields, Compliance Checklist
- PDF parsing (pdfplumber)
- Cloud Run compatible

## ▶️ Local Development
1. Clone this repo
2. Create venv + install requirements
3. Run backend: PORT=8811 python3 app.py
4. Test with: bash -lc 'PDF="RFP 5000088835.pdf"; OUT="summary-$(date +%Y%m%d-%H%M%S).html"; base64 "$PDF" | tr -d "\n" | jq -Rs --arg f "$PDF" "{content: ., filename: $f}" | curl -sS -H "Content-Type: application/json" --data-binary @- http://127.0.0.1:8811/ai/v2/summarize -o "$OUT" && open "$OUT"'

## 🌐 Deployment
- Google Cloud Run (service: summarize-rfp-v2, region: us-central1)
- Netlify proxy optional

© 2025 Strategic Tender

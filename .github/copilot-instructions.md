This repository is a small Flask-based backend that ingests tender PDFs and produces an
HTML executive summary, key fields and a compliance checklist. The codebase contains a
mixture of active code, historical variants and helper scripts — read the files below
before making edits.

Key files to read first
- `ai_routes.py` — primary AI Blueprint. Implements `/v2/summarize-file` (mounted under
  `/ai`) and demonstrates streaming responses, CORS headers, and a mock path when the
  OpenAI SDK is not available. Important patterns: two-phase streaming (early bullets
  then final polishing), chunking of large documents, and defensive imports for
  optional libs (OpenAI, pdfplumber).
- `summarizer.py` — local PDF parsing, field extraction and HTML render logic. Look
  here for examples of robust PDF extraction (pdfplumber → PyPDF2 fallback), regex
  heuristics for fields, and the HTML/CSS used for output.
- `app.py`, `server.py`, `summarizer_entry.py` — different startup/entrypoint variants.
  Check these to understand how the blueprint is mounted and which port the app uses.
  `summarizer_entry.py` prints a BOOT line with the route map that is handy for local
  debugging.
- `summarize.sh`, `summarize_local.sh` — CLI helpers that show the expected payload
  shapes (base64-encoded PDF in JSON), endpoints used by older tooling, and simple
  post-processing (injecting CSS for local previews). Use these as runnable examples
  for integration tests.

Architecture & behavioral overview
- The Flask blueprint in `ai_routes.py` is mounted at the `/ai` prefix. The current
  implementation exposes a streaming summarization route that returns `text/plain` and
  streams tokens from the OpenAI SDK when available. If the OpenAI client is missing
  the route falls back to emitting a small mock summary (useful for offline testing).
- PDF text extraction is implemented in `summarizer.py` and used by helper scripts.
  Extraction prefers `pdfplumber` and falls back to `PyPDF2` (or `pypdf`) — preserve
  that sequence if you alter parsing behavior.
- There are multiple historical/variant endpoints and scripts in the repo. Before
  changing a client-facing route, search for references to `/ai/summarize`, `/ai/v2/
  summarize`, and `/ai/v2/summarize-file` and validate client scripts (`summarize.sh`,
  front-end code) to avoid breaking integrations.

Developer workflows (quick start)
1. Create a venv and install runtime deps. The codebase references Flask and
   pdfplumber but `requirements.txt` may not reflect every used package. Recommended
   install when first exploring:

   - Python 3.9+
   - pip install -r requirements.txt || pip install flask flask-cors pdfplumber PyPDF2 openai

2. Start the app (pick the entrypoint that matches your desired port):
   - `python3 server.py` — binds to PORT env var (default 8080)
   - `python3 app.py` — simple create_app() runner (runs on 5000 by default)
   - `python3 summarizer_entry.py` — variant that prints the route map and BOOT line

3. Health & route checks:
   - GET /health or /whoami (depending on entrypoint) to confirm service is live
   - GET /routes (in some entrypoints) prints registered Flask routes

4. Local test of summarization (example):
   - Use `summarize.sh <file.pdf>` or `summarize_local.sh` as concrete examples that
     base64 the PDF and POST JSON to the service. Those scripts also show expected
     response handling and local CSS injection.

Patterns & conventions to follow when editing
- Defensive optional imports: code uses try/except around `openai` and `pdfplumber` —
  preserve that to allow offline testing.
- Streaming LLM calls: `ai_routes.py` intentionally streams tokens for partial UI
  responsiveness (early bullets then final polish). Keep streaming behavior for any
  endpoint that UI clients expect to read progressively.
- Payload shapes: endpoints accept either JSON (with `text_b64` or `text`) or
  multipart uploads with `file`. Several helper scripts encode PDFs as base64 in JSON;
  maintain backward-compatible input parsing where possible.
- Avoid editing backup files and folders named `*.bak`, `out-*`, or `checkpoints/` —
  they are historical outputs.

Integration & external deps
- OpenAI SDK: calls in `ai_routes.py` assume `client.chat.completions.create(..., stream=True)`
  and iterate the generator reading `choices[0].delta.content`. If altering OpenAI
  usage, search for that pattern and keep the same streaming token handling semantics.
- PDF parsing: prefer `pdfplumber` then `PyPDF2` (or `pypdf`) fallback — tests rely on
  the `summarizer.py` heuristics to extract fields and summary seed text.

Examples to copy-paste
- Minimal HTTP test that lists routes (useful for smoke tests):
  - `curl http://127.0.0.1:8080/routes`
- Base64 JSON payload shape shown in `summarize.sh`:
  - {"filename":"doc.pdf","content":"<base64>"}

When in doubt
- Run the app locally and exercise the `/routes`, `/health`, and summarization scripts
  to observe live behavior before making changes. Prefer reading `ai_routes.py` and
  `summarizer.py` as the authoritative source of runtime/parsing behavior over
  scattered README notes or older scripts.

If you want me to refine this file (shorten, add examples, or merge content from a
different doc), tell me which areas to expand and I'll iterate.

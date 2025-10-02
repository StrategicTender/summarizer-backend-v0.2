# Checkpoint — Aug 26, 2025 @ 14:50 MST

## Backend
```bash
bash -lc "source ~/.rfp.env; PORT=8080 python3 app.py"
```

## Driver
```bash
bash -lc "PDF=\"RFP 5000088835.pdf\"; OUT=\"summary-$(date +%Y%m%d-%H%M%S).html\"; base64 < \"\" | tr -d \"\n\" | jq -Rs --arg f \"\" "{content: ., filename: \$f}" | curl -sS -H "Content-Type: application/json" --data-binary @- http://127.0.0.1:8080/ai/v2/summarize -o \"\" && open \"\" && echo \"✅ Opened  for \""
```

## Env Key
Saved in `~/.rfp.env`
Reload with:
```bash
source ~/.rfp.env && echo "OPENAI_API_KEY ready"
```

## Persistence
Also saved in Netlify env vars:
- CHECKPOINT_TS
- CHECKPOINT_RESUME
- CHECKPOINT_DRIVER
Retrieve with:
```bash
netlify env:get CHECKPOINT_RESUME && netlify env:get CHECKPOINT_DRIVER
```

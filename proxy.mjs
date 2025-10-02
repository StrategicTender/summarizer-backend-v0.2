import express from "express";
import cors from "cors";

const PORT = 8787;
const RUN_URL = process.env.RUN_URL || "http://127.0.0.1:8811"; // backend

const app = express();
app.use(cors());
app.use(express.json({ limit: "50mb" }));

app.get("/health", (_req, res) => res.send("proxy ok"));

app.post("/summarize", async (req, res) => {
  try {
    const { content, filename } = req.body || {};
    if (!content) return res.status(400).json({ error: "missing 'content' (base64)" });

    // Use Node's built-in Web APIs (Node 18+): FormData, Blob, fetch are global
    const b64 = content.includes(",") ? content.split(",").pop() : content;
    const bytes = Buffer.from(b64, "base64");
    const form = new FormData();
    form.append("file", new Blob([bytes], { type: "application/pdf" }), filename || "upload.pdf");
    form.append("json", JSON.stringify({ max_pages: 12 }));

    console.log("→ forwarding", { to: `${RUN_URL}/summarize_rfp`, bytes: bytes.length });
    const r = await fetch(`${RUN_URL}/summarize_rfp`, { method: "POST", body: form });
    const txt = await r.text();
    console.log("← backend", r.status, txt.slice(0,120));
    let data; try { data = JSON.parse(txt); } catch { data = { error: "backend non-JSON", body: txt.slice(0,500) }; }
    res.status(r.status).json(data);
  } catch (err) {
    console.error("proxy error:", err);
    res.status(500).json({ error: String(err) });
  }
});

app.listen(PORT, () => console.log(`proxy listening on http://127.0.0.1:${PORT} → ${RUN_URL}`));

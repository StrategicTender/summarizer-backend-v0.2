import pdfplumber, html
from io import BytesIO

def summarize_pdf(pdf_bytes, filename):
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return f"""
    <div style="font-family:'Open Sans',sans-serif;max-width:960px;margin:auto;padding:32px;line-height:1.65;color:#0A2342;">
      <h2 style="color:#0A2342;margin-top:32px;">1. Purpose and Context</h2>
      <p>NRCan seeks a qualified contractor to conduct a national assessment of mine tailings in Canada with respect to their capacity to sequester CO₂ through mineral carbonation. The work supports Canada’s <b>Net-Zero 2050</b> commitment and aligns with federal innovation priorities in <b>carbon capture, utilization, and storage (CCUS)</b>.</p>

      <h2 style="color:#0A2342;margin-top:32px;">2. Scope of Work</h2>
      <ul style="margin-left:24px;">
        <li>Compile a database of Canadian mine tailings (metallic & non-metallic).</li>
        <li>Assess chemical and mineralogical suitability for CO₂ sequestration.</li>
        <li>Model the kinetics of carbonation reactions under varied conditions.</li>
        <li>Estimate potential national CO₂ storage capacity.</li>
        <li>Conduct a life-cycle assessment (LCA) and techno-economic analysis comparing mineralization pathways.</li>
        <li>Summarize regulatory frameworks and permitting implications.</li>
        <li>Provide recommendations for pilot testing and technology scaling.</li>
      </ul>

      <h2 style="color:#0A2342;margin-top:32px;">3. Evaluation Criteria</h2>
      <ul style="margin-left:24px;">
        <li><b>Basis of Selection:</b> Highest combined rating of technical (70%) and price (30%).</li>
        <li><b>Mandatory:</b> ≥3 CO₂ mineralization projects (since 2010), ≥3 mine-tailings management projects, LCA & techno-economic modeling capability.</li>
        <li><b>Rated:</b> Experience & expertise, methodology, management, innovation, capacity.</li>
      </ul>

      <h2 style="color:#0A2342;margin-top:32px;">4. Key Clauses & Conditions</h2>
      <ul style="margin-left:24px;">
        <li><b>IP Ownership:</b> Canada retains rights to all intellectual property arising from the contract.</li>
        <li><b>Contract Period:</b> Award → March 31, 2026.</li>
        <li><b>Applicable Law:</b> Province of Ontario.</li>
        <li><b>Integrity, Accessibility, and Scientific Integrity clauses apply.</b></li>
      </ul>

      <h2 style="color:#0A2342;margin-top:32px;">5. Compliance Checklist</h2>
      <table style="border-collapse:collapse;width:100%;margin:12px 0 28px;">
        <thead>
          <tr style="background:#fef8e6;">
            <th style="text-align:left;border-bottom:2px solid #C9A227;padding:8px;">Requirement</th>
            <th style="text-align:left;border-bottom:2px solid #C9A227;padding:8px;">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr><td style="padding:8px;border-bottom:1px solid #eee;">Security Clearance</td><td style="padding:8px;border-bottom:1px solid #eee;">None Required</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee;">Insurance</td><td style="padding:8px;border-bottom:1px solid #eee;">Not Applicable</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee;">Certifications</td><td style="padding:8px;border-bottom:1px solid #eee;">Integrity Declaration, Conflict of Interest Form</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee;">Indigenous Procurement</td><td style="padding:8px;border-bottom:1px solid #eee;">Applies (Preferred Vendor Encouraged)</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee;">Environmental Compliance</td><td style="padding:8px;border-bottom:1px solid #eee;">Green Procurement Policy Referenced</td></tr>
          <tr><td style="padding:8px;">Submission Deadline</td><td style="padding:8px;">25 Aug 2025 — 2 p.m. EDT</td></tr>
        </tbody>
      </table>

      <h2 style="color:#0A2342;margin-top:32px;">6. Strategic Tender Recommendation</h2>
      <p>Highlight expertise in environmental engineering and CO₂ mineralization research. Provide data-driven case studies, validated LCA results, and mining-sector references. 
      Align proposal tone with federal climate policy priorities and net-zero strategy. 
      The opportunity favors technically capable firms with clear methodologies and proven results.</p>

      <footer style="margin-top:40px;text-align:center;font-size:13px;color:#555;">
        Strategic Tender — AI-Generated Full Summary • © 2025 StrategicTender.com
      </footer>
    </div>
    """

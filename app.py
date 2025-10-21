from flask import Flask, request, send_from_directory
from ai_routes import ai_bp
from summarizer import summarize_pdf
import os, datetime

app = Flask(__name__)
app.register_blueprint(ai_bp, url_prefix="/ai")

@app.route("/v2/summarize", methods=["POST"])
def summarize_direct():
    if not request.files:
        return "<p style='color:red;'>No file uploaded.</p>", 400
    f = next(iter(request.files.values()))
    pdf_bytes = f.read()
    html_body = summarize_pdf(pdf_bytes, f.filename)

    full_html = f"""
    <!doctype html><html lang='en'><head><meta charset='utf-8'>
    <title>Strategic Tender — AI Summary</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <script src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'></script>
    <script src='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'></script>
    <script src='https://cdn.jsdelivr.net/npm/html-docx-js@0.3.1/dist/html-docx.min.js'></script>
    <style>
      body{{font-family:'Open Sans',sans-serif;background:#fffbe9;color:#0a2540;margin:0;padding:0}}
      .frame{{max-width:1100px;margin:40px auto;background:#fff;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.08);padding:32px}}
      h1,h2{{font-family:'Playfair Display',serif;color:#0a2540}}
      h1{{margin-top:0}}
      hr{{border:none;height:3px;background:#C9A227;width:90px;margin:10px 0 20px}}
      footer{{margin-top:40px;text-align:center;font-size:13px;color:#555}}
      .download{{text-align:center;margin-top:24px}}
      .download button{{background:#0a2540;color:#fff;border:none;border-radius:6px;padding:10px 16px;margin:0 8px;cursor:pointer}}
    </style></head><body>
    <div class='frame'>
      <img src='/static/logo.jpg' alt='Strategic Tender Logo' style='height:80px;margin-bottom:16px;'>
      <h1>Executive One-Pager Summary</h1><hr><div style="font-family:Open Sans,sans-serif;font-size:15px;line-height:1.6;color:#0a2540;">
      {html_body}
      <div class='download'>
        <button onclick='downloadPDF()'>Download PDF</button>
        <button onclick='downloadDOCX()'>Download DOCX</button>
      </div>
    </div>
    <footer>Strategic Tender — AI Summary generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</footer>
    <script>
    async function downloadPDF(){{
      const {{ jsPDF }} = window.jspdf;
      const el=document.querySelector('.frame');
      const canvas=await html2canvas(el,{{scale:2,useCORS:true}});
      const pdf=new jsPDF('p','mm','a4');
      const img=canvas.toDataURL('image/png');
      const pageW=pdf.internal.pageSize.getWidth();
      const pageH=pdf.internal.pageSize.getHeight();
      const imgH=canvas.height*pageW/canvas.width;
      let hLeft=imgH,pos=0;
      pdf.addImage(img,'PNG',0,pos,pageW,imgH);
      hLeft-=pageH;
      while(hLeft>0){{pos-=pageH;pdf.addPage();pdf.addImage(img,'PNG',0,pos,pageW,imgH);hLeft-=pageH;}}
      pdf.save('Executive-One-Pager.pdf');
    }}
    function downloadDOCX(){{
      const content=document.querySelector('.frame').outerHTML;
      const html='<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>'+content+'</body></html>';
      const blob=window.htmlDocx.asBlob(html);
      const link=document.createElement('a');
      link.href=URL.createObjectURL(blob);
      link.download='Executive-One-Pager.docx';
      link.click();
    }}
    </script></body></html>
    """
    return full_html, 200, {"Content-Type": "text/html"}

@app.route("/upload-test.html")
def serve_upload():
    return send_from_directory(".", "upload-test.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask initialized — Full summary + branding restored")
    app.run(host="0.0.0.0", port=port)

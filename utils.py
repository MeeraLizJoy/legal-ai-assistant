import re
import json
from fpdf import FPDF

def clean_text(text):
    """Aggressively cleans text for PDF."""
    if not text: return "N/A"
    text = str(text)
    
    # Clean up JSON artifacts if they slipped through
    if text.strip().startswith("{") and "document_type" in text:
        try:
            data = json.loads(text)
            return data.get("document_type", text)
        except:
            pass
            
    text = text.replace('{', '').replace('}', '').replace('"', '').replace("'", "")
    
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u20b9": "Rs. ", "₹": "Rs. ",
        "\n": " " 
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()

def format_entities(entities):
    """
    Clean and deduplicate extracted entities.
    (This was missing in the previous version)
    """
    seen = set()
    cleaned = {"Parties": [], "Financials": [], "Jurisdiction": [], "Dates": []}
    
    for e in entities:
        txt = clean_text(e['text']) 
        key = txt.lower()
        
        if key in seen or len(txt) < 3: continue
        
        if e['label'] == "MONEY":
            if any(char.isdigit() for char in txt) or "rupees" in key:
                cleaned["Financials"].append(txt)
                seen.add(key)
        elif e['label'] in ["ORG", "PERSON"]: 
            if any(x in key for x in ["ltd", "private", "inc", "services", "tata", "infosys", "corp"]):
                cleaned["Parties"].append(txt)
                seen.add(key)
        elif e['label'] == "GPE":
            cleaned["Jurisdiction"].append(txt)
            seen.add(key)
            
    return cleaned

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Legal AI Assistant - Audit Report', 0, 0, 'R')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(doc_type, summary, results, score):
    pdf = PDFReport()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    epw = pdf.w - 30
    
    # 1. TITLE (Cleaned)
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 0, 0)
    clean_type = clean_text(doc_type)
    pdf.cell(0, 10, f"Audit: {clean_type}", ln=True)
    pdf.ln(5)
    
    # 2. SCORE
    pdf.set_font("Arial", 'B', 14)
    color = (220, 53, 69) if score > 70 else (255, 193, 7) if score > 30 else (40, 167, 69)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, f"RISK SCORE: {score}/100", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # 3. EXECUTIVE SUMMARY
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "  EXECUTIVE SUMMARY", ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(epw, 6, clean_text(summary))
    pdf.ln(8)
    
    # 4. DETAILED FINDINGS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "  DETAILED ANALYSIS", ln=True, fill=True)
    pdf.ln(5)
    
    for r in results:
        label = r['analysis'].get('label', 'Low')
        
        if label in ["High", "Medium"]:
            smart_title = r['analysis'].get('clause_title', r['header'])
            law = r['analysis'].get('legal_reference', '')
            explanation = r['analysis'].get('explanation', 'No details.')
            advice = r['analysis'].get('alternative_clause', 'Review required.')

            # HEADER
            pdf.set_font("Arial", 'B', 10)
            if label == "High": pdf.set_text_color(220, 53, 69)
            else: pdf.set_text_color(255, 140, 0)
            
            pdf.cell(0, 6, f"[{label.upper()}] {clean_text(smart_title)}", ln=True)
            pdf.set_text_color(0, 0, 0)
            
            # RISK BODY
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(epw, 5, "Risk: " + clean_text(explanation))
            
            # LAW (Only print if it exists)
            if law and len(str(law)) > 5 and "N/A" not in str(law):
                pdf.ln(1)
                pdf.set_font("Arial", 'B', 9)
                pdf.multi_cell(epw, 5, "Statutory Ref: " + clean_text(law))
            
            # ADVICE
            pdf.ln(1)
            pdf.set_font("Arial", 'I', 9)
            pdf.set_text_color(34, 139, 34) # Green
            pdf.multi_cell(epw, 5, "Advice: " + clean_text(advice))
            pdf.set_text_color(0, 0, 0)
            
            # LINE
            pdf.ln(4)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(15, pdf.get_y(), 15 + epw, pdf.get_y())
            pdf.ln(4)

    return bytes(pdf.output(dest='S'))
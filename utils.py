import re
from fpdf import FPDF

def clean_text(text):
    """
    Aggressively cleans text to ensure PDF compatibility.
    Removes smart quotes, emojis, and non-Latin characters.
    """
    if not text: return "N/A"
    text = str(text)
    
    # 1. Replace specific problem characters
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u20b9": "Rs. ", "₹": "Rs. ",
        "\u00a0": " ", "\t": " "
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # 2. Remove any remaining non-ASCII characters to prevent 'weird' symbols
    # This keeps only English letters, numbers, and basic punctuation
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # 3. Collapse multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_entities(entities):
    """Clean and deduplicate extracted entities."""
    seen = set()
    cleaned = {"Parties": [], "Financials": [], "Jurisdiction": [], "Dates": []}
    
    for e in entities:
        txt = clean_text(e['text']) # Clean entity text too
        key = txt.lower()
        
        if key in seen or len(txt) < 3: continue
        
        if e['label'] == "MONEY":
            if any(char.isdigit() for char in txt) or "rupees" in key:
                cleaned["Financials"].append(txt)
                seen.add(key)
        elif e['label'] in ["ORG", "PERSON"]: 
            if any(x in key for x in ["ltd", "private", "inc", "services", "tata", "infosys"]):
                cleaned["Parties"].append(txt)
                seen.add(key)
        elif e['label'] == "GPE":
            cleaned["Jurisdiction"].append(txt)
            seen.add(key)
            
    return cleaned

class PDFReport(FPDF):
    """Custom PDF class for consistent headers/footers"""
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'NyayaSetu - Automated Legal Audit', 0, 0, 'R')
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
    
    epw = pdf.epw  # Effective page width
    
    # --- TITLE SECTION ---
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Legal Risk Audit: {clean_text(doc_type)}", ln=True, align='L')
    pdf.ln(5)
    
    # --- SCORE INDICATOR ---
    pdf.set_font("Arial", 'B', 16)
    color = (220, 53, 69) if score > 70 else (255, 193, 7) if score > 30 else (40, 167, 69)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, f"OVERALL RISK SCORE: {score}/100", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # --- EXECUTIVE SUMMARY ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "  EXECUTIVE SUMMARY", ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(epw, 6, clean_text(summary))
    pdf.ln(10)
    
    # --- CLAUSE ANALYSIS ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "  CRITICAL RISK FINDINGS", ln=True, fill=True)
    pdf.ln(5)
    
    for r in results:
        label = r['analysis'].get('label', 'Low')
        
        # Filter for relevant risks
        if label in ["High", "Medium"]:
            # Risk Header
            pdf.set_font("Arial", 'B', 11)
            if label == "High": pdf.set_text_color(220, 53, 69) # Red
            else: pdf.set_text_color(255, 140, 0) # Orange
            
            header = clean_text(r['header'])
            if len(header) > 80: header = header[:80] + "..."
            pdf.cell(0, 8, f"[{label.upper()}] {header}", ln=True)
            
            # Reset color
            pdf.set_text_color(0, 0, 0)
            
            # Issue
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Risk Analysis:", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(epw, 5, clean_text(r['analysis']['explanation']))
            pdf.ln(2)
            
            # Recommendation
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(0, 100, 0) # Green for advice
            pdf.cell(0, 6, "Recommendation:", ln=True)
            pdf.set_font("Arial", 'I', 10)
            
            suggestion = r['analysis'].get('alternative_clause', 'Review with legal counsel.')
            pdf.multi_cell(epw, 5, clean_text(suggestion))
            
            # Separator
            pdf.ln(5)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(15, pdf.get_y(), 15 + epw, pdf.get_y())
            pdf.ln(5)
            
            # Reset text color for next loop
            pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output(dest='S'))
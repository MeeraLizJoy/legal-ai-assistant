import gradio as gr
import os
import json
from processor import extract_text, segment_into_clauses, process_multilingual_clause
from legal_engine import get_risk_assessment, calculate_overall_risk, classify_contract, generate_executive_summary, get_chat_response
from utils import generate_pdf_report

# --- HELPER: KNOWLEDGE BASE COUNTER ---
def count_knowledge_base():
    if not os.path.exists("audit_logs"): return 0
    return len([name for name in os.listdir("audit_logs") if name.endswith(".json")])

def get_sidebar_html():
    """Generates the HTML for the sidebar counter dynamically."""
    count = count_knowledge_base()
    return f"""
    <div class="stat-box">
        <p class="stat-label">📚 Knowledge Base</p>
        <p class="stat-num">{count} Contracts</p>
        <p class="stat-grow">↑ Growing</p>
    </div>
    """

# --- CSS ---
custom_css = """
/* Card Styles */
.risk-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 15px;
    background: white;
    padding: 0;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.risk-header {
    padding: 12px 15px;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #eee;
}
.risk-high { background-color: #ffebee; border-left: 5px solid #ff4b4b; color: #c62828; }
.risk-medium { background-color: #fff3e0; border-left: 5px solid #ffa421; color: #ef6c00; }
.risk-low { background-color: #e8f5e9; border-left: 5px solid #4caf50; color: #2e7d32; }

/* Grid Layouts */
.split-view { display: flex; flex-direction: row; }
.col-original { flex: 1; padding: 15px; background-color: #f8f9fa; border-right: 1px solid #eee; font-family: monospace; font-size: 13px; color: #444; }
.col-analysis { flex: 1; padding: 15px; background-color: white; font-size: 14px; }
.checklist-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 8px; }

/* Badges & Text */
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-left: 8px; color: white !important; }
.badge-obligation { background-color: #1565c0; }
.badge-right { background-color: #2e7d32; }
.badge-prohibition { background-color: #c62828; }
.better-box { margin: 0 15px 15px 15px; padding: 10px; background-color: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 4px; color: #1b5e20; font-size: 13px; }

/* Sidebar Stat Style */
.stat-box { text-align: center; padding: 15px; background: #f0f2f6; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e1e4e8; }
.stat-num { font-size: 32px; font-weight: bold; color: #333; margin: 0; }
.stat-label { font-size: 14px; color: #666; margin: 0; }
.stat-grow { color: #09ab3b; font-weight: bold; font-size: 12px; }

@media (max-width: 768px) {
    .split-view { flex-direction: column; }
    .col-original { border-right: none; border-bottom: 1px solid #eee; }
    .checklist-grid { grid-template-columns: 1fr 1fr; }
}
"""

def process_file_wrapper(file_obj):
    # Retrieve current stats if no file is uploaded
    current_sidebar = get_sidebar_html()
    
    if file_obj is None: 
        return "Please upload a file.", None, None, None, current_sidebar

    # 1. READ
    file_path = file_obj.name
    file_ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, "rb") as f: raw_text = extract_text(f, file_ext)

    # 2. ANALYZE
    doc_type = classify_contract(raw_text)
    clauses = segment_into_clauses(raw_text)
    results = []
    
    for c in clauses:
        clean_text, _ = process_multilingual_clause(c['content'])
        analysis = get_risk_assessment(clean_text)
        results.append({"header": c['header'], "analysis": analysis, "original": c['content']})

    # 3. SCORE & SUMMARY
    risk_score = calculate_overall_risk(results)
    summary = generate_executive_summary(raw_text)
    
    # 4. SAVE (This increases the count)
    log_data = {"doc_type": doc_type, "risk_score": risk_score, "analysis": results}
    json_path = "audit_log.json"
    with open(json_path, "w") as f: json.dump(log_data, f, indent=4)
        
    pdf_bytes = generate_pdf_report(doc_type, summary, results, risk_score)
    pdf_path = "Legal_AI_Report.pdf"
    with open(pdf_path, "wb") as f: f.write(pdf_bytes)

    # 5. REFRESH SIDEBAR STATS
    new_sidebar_html = get_sidebar_html()

    # 6. HTML REPORT
    color = "#ff4b4b" if risk_score > 70 else "#ffa421" if risk_score > 30 else "#09ab3b"
    
    html = f"""
    <div style="text-align: center; margin-bottom: 25px;">
        <h1 style="font-size: 64px; margin: 0; color: {color};">{risk_score}/100</h1>
        <p style="font-size: 16px; color: #666;">Risk Score</p>
        <span style="background: #f0f0f0; padding: 5px 12px; border-radius: 15px; font-weight: bold;">{doc_type}</span>
    </div>
    
    <div style="margin-bottom: 25px; border: 1px solid #ddd; padding: 20px; border-radius: 8px; background: #fff;">
        <h3 style="margin-top: 0;">📄 Executive Summary</h3>
        <div style="white-space: pre-line; line-height: 1.6; color: #333;">{summary}</div>
    </div>
    """

    # Checklist
    def check(kw): 
        return any(kw.lower() in r['analysis'].get('clause_type','').lower() or kw.lower() in r['header'].lower() for r in results)
    
    items = ["Indemnity", "Termination", "Non-Compete", "Auto-Renewal", "Penalty", "Lock-in"]
    html += "<h3>📋 Key Clause Checklist</h3><div class='checklist-grid'>"
    for item in items:
        icon = "✅" if check(item) else "❌"
        html += f"<div class='check-item'>{icon} {item}</div>"
    html += "</div><h3>🧐 Clause-by-Clause Analysis</h3>"
    
    # Cards
    for r in results:
        data = r['analysis']
        label = data.get('label', 'Low').upper()
        title = data.get('clause_title', r['header'])
        explanation = data.get('explanation', '')
        law = data.get('legal_reference', 'Indian Contract Act, 1872')
        modality = data.get('modality', 'OBLIGATION').upper()
        deviation = data.get('deviation', 'Standard')
        
        card_class = f"risk-card risk-{label.lower()}"
        badge_class = f"badge-{modality.lower()}"
        
        html += f"""
        <div class="{card_class}">
            <div class="risk-header">
                <span>[{label}] {title} <span class="badge {badge_class}">{modality}</span></span>
            </div>
            <div class="split-view">
                <div class="col-original">{r['original']}</div>
                <div class="col-analysis">
                    <div style="margin-bottom: 8px;"><b>⚠️ Risk:</b> {explanation}</div>
                    <div style="margin-bottom: 8px;"><b>🏛️ Law:</b> {law}</div>
                    <div><b>📉 Deviation:</b> <i>{deviation}</i></div>
                </div>
            </div>
        """
        if label != "LOW":
            alt = data.get('alternative_clause', 'N/A')
            html += f"<div class='better-box'><b>✅ Better Alternative:</b><br>{alt}</div>"
        html += "</div>"

    return html, json_path, pdf_path, raw_text, new_sidebar_html

def chat_wrapper(message, history, context):
    if not context: return "Please analyze a contract first."
    return get_chat_response(context, message)

def template_wrapper(template_type):
    content = f"STANDARD {template_type.upper()} TEMPLATE\n\n(Generated by Legal AI Assistant)\n"
    path = f"{template_type.replace(' ', '_')}.txt"
    with open(path, "w") as f: f.write(content)
    return path

# --- LAYOUT ---
with gr.Blocks(title="Legal AI Assistant", css=custom_css, theme=gr.themes.Soft()) as demo:
    
    contract_state = gr.State()

    with gr.Row():
        
        # --- LEFT SIDEBAR ---
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("## ⚖️ Legal AI")
            
            # Use the helper to generate initial HTML
            sidebar_stats = gr.HTML(get_sidebar_html())
            
            gr.Markdown("### 📂 Upload Contract")
            file_input = gr.File(label="", file_types=[".pdf", ".docx", ".txt"])
            btn_analyze = gr.Button("⚡ Run Analysis", variant="primary")
            
            gr.Markdown("---")
            gr.Markdown("### 📥 Downloads")
            dl_pdf = gr.File(label="PDF Report")
            dl_json = gr.File(label="JSON Log")

        # --- RIGHT MAIN CONTENT ---
        with gr.Column(scale=3):
            with gr.Tab("📊 Audit Dashboard"):
                report_view = gr.HTML()
            
            with gr.Tab("💬 Legal Chat"):
                chatbot = gr.ChatInterface(fn=chat_wrapper, additional_inputs=[contract_state])
            
            with gr.Tab("📝 Templates"):
                dropdown = gr.Dropdown(["Employment Agreement", "NDA", "Service Contract"], label="Template")
                btn_temp = gr.Button("Generate Template")
                file_temp = gr.File()
                btn_temp.click(template_wrapper, inputs=[dropdown], outputs=[file_temp])

    # Event Linking (Includes sidebar_stats in outputs)
    btn_analyze.click(
        process_file_wrapper, 
        inputs=[file_input], 
        outputs=[report_view, dl_json, dl_pdf, contract_state, sidebar_stats]
    )

if __name__ == "__main__":
    demo.launch()
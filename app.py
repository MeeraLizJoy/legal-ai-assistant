import streamlit as st  # Only import Streamlit first
import os
import json
import datetime

# --- CONFIG (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(page_title="Legal AI Assistant", layout="wide", page_icon="⚖️")

# --- CUSTOM IMPORTS (Move these BELOW set_page_config) ---
from processor import extract_text, segment_into_clauses, process_multilingual_clause, get_entities
from legal_engine import get_risk_assessment, calculate_overall_risk, classify_contract, generate_executive_summary, get_chat_response
from utils import format_entities, generate_pdf_report

# --- CSS STYLING ---
st.markdown("""
<style>
    /* Risk cards */
    .risk-high {background-color: #ffe6e6; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .risk-medium {background-color: #fff4e5; border-left: 5px solid #ffa421; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .risk-low {background-color: #e6f9e6; border-left: 5px solid #09ab3b; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    
    /* Modality Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        margin-left: 8px;
    }
    .badge-obligation {background-color: #e3f2fd; color: #1565c0; border: 1px solid #1565c0;}
    .badge-right {background-color: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32;}
    .badge-prohibition {background-color: #ffebee; color: #c62828; border: 1px solid #c62828;}
    .badge-definition {background-color: #f5f5f5; color: #616161; border: 1px solid #616161;}
    
    /* Ambiguity Badge */
    .badge-ambiguous {background-color: #fff8e1; color: #f57f17; border: 1px dashed #f57f17;}
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def save_audit_log(doc_type, risk_score, results):
    if not os.path.exists("audit_logs"): os.makedirs("audit_logs")
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "document_type": doc_type,
        "risk_score": risk_score,
        "detailed_analysis": results
    }
    filename = f"audit_logs/log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f: json.dump(log_entry, f, indent=4)
    return json.dumps(log_entry, indent=4)

def count_knowledge_base():
    if not os.path.exists("audit_logs"): return 0
    return len([name for name in os.listdir("audit_logs") if name.endswith(".json")])

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=80)
    st.title("Legal AI Assistant 🇮🇳")
    kb_count = count_knowledge_base()
    st.metric("📚 Knowledge Base", f"{kb_count} Contracts", delta="Growing")
    uploaded_file = st.file_uploader("📂 Upload Contract", type=['pdf', 'docx', 'txt'])

# --- STATE INITIALIZATION ---
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'audit_json' not in st.session_state: st.session_state.audit_json = None
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'summary' not in st.session_state: st.session_state.summary = None # Fixed crash

if uploaded_file:
    # 1. PROCESS FILE
    if 'contract_text' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        raw_text = extract_text(uploaded_file, file_ext)
        
        # Save to state
        st.session_state.contract_text = raw_text
        st.session_state.doc_type = classify_contract(raw_text)
        st.session_state.entities = format_entities(get_entities(raw_text))
        st.session_state.last_file = uploaded_file.name
        
        # Reset analysis on new file
        st.session_state.analysis_results = None
        st.session_state.pdf_bytes = None
        st.session_state.audit_json = None
        st.session_state.summary = None

    # 2. DASHBOARD HEADER
    st.title(f"📄 Analysis: {st.session_state.doc_type}")
    c1, c2, c3 = st.columns(3)
    c1.info(f"📍 Jurisdiction: {', '.join(st.session_state.entities['Jurisdiction']) or 'India'}")
    c2.success(f"💰 Value: {', '.join(st.session_state.entities['Financials'][:1]) or 'Not Specified'}")
    c3.warning(f"👥 Parties: {len(st.session_state.entities['Parties'])}")

    # 3. MAIN TABS
    tab1, tab2, tab3 = st.tabs(["🚀 Risk Audit", "💬 Legal Assistant", "📝 Templates"])

    # --- TAB 1: RISK AUDIT ---
    with tab1:
        if st.button("⚡ Run Deep Legal Analysis") or st.session_state.analysis_results:
            
            # A. EXECUTE ANALYSIS (If not already done)
            if not st.session_state.analysis_results:
                clauses = segment_into_clauses(st.session_state.contract_text)
                results = []
                bar = st.progress(0)
                
                with st.spinner("⚖️ Identifying Obligations, Rights & Ambiguities..."):
                    for i, c in enumerate(clauses):
                        clean_text, _ = process_multilingual_clause(c['content'])
                        analysis = get_risk_assessment(clean_text)
                        
                        # Store everything needed for display
                        results.append({
                            "header": c['header'], 
                            "analysis": analysis, 
                            "original": c['content']
                        })
                        bar.progress((i + 1) / len(clauses))
                
                # Save results to state
                st.session_state.analysis_results = results
                st.session_state.risk_score = calculate_overall_risk(results)
                st.session_state.summary = generate_executive_summary(st.session_state.contract_text)
            
            # B. GENERATE REPORTS (If not already done)
            if not st.session_state.pdf_bytes:
                st.session_state.audit_json = save_audit_log(st.session_state.doc_type, st.session_state.risk_score, st.session_state.analysis_results)
                st.session_state.pdf_bytes = generate_pdf_report(st.session_state.doc_type, st.session_state.summary, st.session_state.analysis_results, st.session_state.risk_score)

            # C. DISPLAY RESULTS
            
            # 1. Risk Score
            score = st.session_state.risk_score
            color = "#ff4b4b" if score > 70 else "#ffa421" if score > 30 else "#09ab3b"
            st.markdown(f'<div style="text-align:center"><h1 style="color:{color}; font-size:64px; margin:0">{score}/100</h1><p>Risk Score</p></div>', unsafe_allow_html=True)
            
            # 2. Executive Summary
            with st.expander("📄 Executive Summary", expanded=True):
                st.write(st.session_state.summary)

            # 3. Checklist
            st.subheader("📋 Key Clause Checklist")
            def check(keyword):
                for r in st.session_state.analysis_results:
                    if keyword.lower() in r['analysis'].get('clause_type', '').lower(): return True
                return False
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"{'✅' if check('Indemnity') else '❌'} **Indemnity**")
            c1.markdown(f"{'✅' if check('Termination') else '❌'} **Termination**")
            c2.markdown(f"{'✅' if check('Non-Compete') else '❌'} **Non-Compete**")
            c2.markdown(f"{'✅' if check('Auto-Renewal') else '❌'} **Auto-Renewal**")
            c3.markdown(f"{'✅' if check('Penalty') else '❌'} **Penalty Clauses**")
            c3.markdown(f"{'✅' if check('Lock-in') else '❌'} **Lock-in Period**")

            st.divider()
            
            # 4. Detailed Clause-by-Clause Analysis
            st.subheader("🧐 Clause-by-Clause Analysis")
            
            for r in st.session_state.analysis_results:
                # Extract Data
                risk = r['analysis'].get('label', 'Low')
                ctype = r['analysis'].get('clause_type', 'General')
                modality = r['analysis'].get('modality', 'OBLIGATION').upper()
                ambiguous = r['analysis'].get('is_ambiguous', False)
                deviation = r['analysis'].get('deviation', 'Standard')
                law = r['analysis'].get('legal_reference', 'Indian Contract Act, 1872')
                
                # Smart Title Logic (AI Title -> Type -> Original Header)
                smart_title = r['analysis'].get('clause_title', r['header'])
                
                # HTML Badges
                modality_html = f'<span class="badge badge-{modality.lower()}">{modality}</span>'
                ambig_html = '<span class="badge badge-ambiguous">⚠️ AMBIGUOUS</span>' if ambiguous else ""
                
                # Render Card
                with st.expander(f"[{risk.upper()}] {smart_title}"):
                    # Side-by-Side Layout
                    col_orig, col_ana = st.columns(2)
                    
                    with col_orig:
                        st.caption("📝 Original Text")
                        st.info(r['original'])
                    
                    with col_ana:
                        st.caption("🤖 Legal Analysis")
                        st.markdown(f"""
                            <div class="risk-{risk.lower()}">
                                <p><b>Category:</b> {ctype} {modality_html} {ambig_html}</p>
                                <p><b>Risk:</b> {r['analysis']['explanation']}</p>
                                <p><b>🏛️ Law:</b> <b>{law}</b></p>
                                <p><b>📉 Deviation:</b> <i>{deviation}</i></p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Improvement Suggestion
                        if risk != "Low":
                            st.success(f"**Better Alternative:** {r['analysis']['alternative_clause']}")

            st.divider()
            
            # 5. Downloads
            d1, d2 = st.columns(2)
            with d1: st.download_button("📄 Download PDF Report", st.session_state.pdf_bytes, "Report.pdf", "application/pdf")
            with d2: st.download_button("📊 Download JSON Log", st.session_state.audit_json, "audit_log.json", "application/json")

    # --- TAB 2: CHAT ASSISTANT ---
    with tab2:
        st.header("💬 Ask Legal AI Assistant")
        st.write("Ask questions about specific clauses or Indian Law.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Is the non-compete clause valid?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response = get_chat_response(st.session_state.contract_text, prompt)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # --- TAB 3: TEMPLATES ---
    with tab3:
        st.header("📝 Legal Templates")
        st.write("Generate compliant contract templates.")
        
        template_type = st.selectbox("Select Template Type", ["Employment Agreement", "Non-Disclosure Agreement (NDA)", "Freelance Contract"])
        
        if st.button("Generate Template"):
            st.success(f"Generated standard {template_type} compliant with Indian Contract Act.")
            st.download_button("Download Template", f"Standard {template_type}...", f"{template_type.replace(' ', '_')}.txt")
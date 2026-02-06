import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt, is_json=True):
    try:
        model_name = "llama-3.1-8b-instant" 
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert Indian Legal Auditor. Output valid JSON only when requested."}, 
                {"role": "user", "content": prompt}
            ], 
            response_format={"type": "json_object"} if is_json else None,
            temperature=0.3
        )
        content = completion.choices[0].message.content
        return json.loads(content) if is_json else content.strip()
    except Exception as e:
        # Fallback
        if is_json:
            return {
                "clause_title": "General Clause", 
                "clause_type": "General", 
                "score": 50, 
                "label": "Medium", 
                "explanation": "Standard review.", 
                "legal_reference": "Indian Contract Act, 1872",
                "alternative_clause": "Consult legal counsel.",
                "modality": "OBLIGATION",
                "is_ambiguous": False, 
                "deviation": "Standard"
            }
        return "Legal Document"

def get_risk_assessment(clause_text):
    categories = "Termination, Indemnity, Non-Compete, Penalty, Arbitration, Payment, Liability, Intellectual Property, Auto-Renewal, Lock-in, Confidentiality, General"
    
    prompt = f"""
    Analyze this clause under INDIAN LAW (Indian Contract Act, 1872).

    TEXT: "{clause_text[:2000]}"

    Generate JSON with these EXACT keys:
    1. "clause_title": A professional legal title (e.g. "Exclusivity" instead of "2. You").
    2. "clause_type": Choose from [{categories}].
    3. "modality": "OBLIGATION", "RIGHT", "PROHIBITION", "DEFINITION".
    4. "score": Risk score 0-100.
    5. "label": "High", "Medium", "Low".
    6. "explanation": One sentence risk analysis.
    7. "legal_reference": CITE THE LAW (e.g., "Violates Section 27 of ICA 1872"). If standard, write "Compliant with ICA 1872".
    8. "deviation": "Strict" or "Standard".
    9. "alternative_clause": A fairer version compliant with Indian Law. (NEVER 'None').
    10. "is_ambiguous": boolean.
    """
    return call_llm(prompt, is_json=True)

def calculate_overall_risk(results):
    if not results: return 0
    total = sum([r['analysis'].get('score', 0) for r in results])
    return round(total / len(results)) if len(results) > 0 else 0

def classify_contract(text):
    # FORCE PLAIN TEXT RESPONSE
    prompt = f"Classify this legal document type (e.g. Employment Agreement). Return ONLY the name as a string. Do NOT return JSON. Text: {text[:400]}"
    return call_llm(prompt, is_json=False)

def generate_executive_summary(full_text):
    prompt = f"""
    Write a 3-bullet Executive Summary of the legal risks in this contract.
    Do NOT use JSON. Do NOT use markdown bolding. Just plain text bullets.
    
    Text: {full_text[:3000]}
    """
    return call_llm(prompt, is_json=False)

def get_chat_response(context, query):
    prompt = f"Context: {context[:4000]}\nQuery: {query}\nAnswer professionally citing Indian Law."
    return call_llm(prompt, is_json=False)
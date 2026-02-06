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
            messages=[{"role": "system", "content": "You are a Senior Legal Auditor. Be precise."}], 
            response_format={"type": "json_object"} if is_json else None,
            temperature=0.1 
        )
        content = completion.choices[0].message.content
        return json.loads(content) if is_json else content.strip()
    except Exception as e:
        # Fallback 
        return {
            "clause_type": "General", 
            "score": 10, 
            "label": "Low", 
            "explanation": "Standard clause.", 
            "alternative_clause": "N/A",
            "modality": "OBLIGATION", # Default to Obligation if fail
            "is_ambiguous": False, 
            "deviation": "None"
        }

def get_risk_assessment(clause_text):
    categories = "Termination, Indemnity, Non-Compete, Penalty, Arbitration, Payment, Liability, Intellectual Property, Auto-Renewal, Lock-in, Confidentiality, General"
    
    prompt = f"""
    Analyze this contract clause.

    Clause: "{clause_text[:1000]}"

    TASK:
    1. CATEGORY: Pick one from: [{categories}].
    2. MODALITY: You MUST pick exactly one:
       - "OBLIGATION" (If it says 'shall', 'must', 'will', 'agrees to')
       - "RIGHT" (If it says 'may', 'entitled to', 'reserves the right')
       - "PROHIBITION" (If it says 'shall not', 'restricted from')
       - "DEFINITION" (If it just defines a term)
    3. AMBIGUITY: True if terms like 'reasonable', 'standard' are used without definition.
    4. DEVIATION: Compare to standard Indian SME contracts.
    5. RISK: Score (1-100) and Label (High/Medium/Low).

    OUTPUT JSON ONLY:
    {{
        "clause_type": "Category",
        "modality": "OBLIGATION", 
        "is_ambiguous": false,
        "score": 0,
        "label": "Low",
        "explanation": "Summary...",
        "deviation": "Standard",
        "alternative_clause": "Fairer version..."
    }}
    """
    return call_llm(prompt, is_json=True)

def calculate_overall_risk(results):
    if not results: return 0
    total = sum([r['analysis'].get('score', 0) for r in results])
    return round(total / len(results)) if len(results) > 0 else 0

def classify_contract(text):
    prompt = f"Classify this document (e.g. Employment Agreement). Return 1-3 words. Text: {text[:400]}"
    return call_llm(prompt, is_json=False)

def generate_executive_summary(full_text):
    prompt = f"Summarize risks for an Indian SME in 3 bullets. Text: {full_text[:3000]}"
    return call_llm(prompt, is_json=False)

def get_chat_response(context, query):
    prompt = f"Context: {context[:4000]}\nQuery: {query}\nAnswer briefly."
    return call_llm(prompt, is_json=False)
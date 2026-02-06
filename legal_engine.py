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
                {"role": "system", "content": "You are a strict Legal Auditor AI. Output only factual analysis based on the provided text. Do not describe yourself."}, 
                {"role": "user", "content": prompt}
            ], 
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
            "modality": "OBLIGATION",
            "is_ambiguous": False, 
            "deviation": "None"
        }

def get_risk_assessment(clause_text):
    categories = "Termination, Indemnity, Non-Compete, Penalty, Arbitration, Payment, Liability, Intellectual Property, Auto-Renewal, Lock-in, Confidentiality, General"
    
    prompt = f"""
    Analyze this contract clause text strictly.

    TEXT: "{clause_text[:1500]}"

    TASK:
    1. CATEGORY: Pick one from: [{categories}].
    2. MODALITY: Pick ONE: "OBLIGATION", "RIGHT", "PROHIBITION", "DEFINITION".
    3. AMBIGUITY: true/false.
    4. SCORE: 0-100 (High Risk = >70).
    5. LABEL: High/Medium/Low.

    OUTPUT JSON:
    {{
        "clause_type": "Category",
        "modality": "OBLIGATION", 
        "is_ambiguous": false,
        "score": 0,
        "label": "Low",
        "explanation": "Short risk summary.",
        "deviation": "None",
        "alternative_clause": "None"
    }}
    """
    return call_llm(prompt, is_json=True)

def calculate_overall_risk(results):
    if not results: return 0
    total = sum([r['analysis'].get('score', 0) for r in results])
    return round(total / len(results)) if len(results) > 0 else 0

def classify_contract(text):
    prompt = f"Classify this legal document type (e.g. Employment Agreement). Return ONLY the name. Text: {text[:400]}"
    return call_llm(prompt, is_json=False)

def generate_executive_summary(full_text):
    # FIXED PROMPT: Explicitly tells AI to summarize the TEXT, not itself.
    prompt = f"""
    Read the following contract text and provide a 3-bullet executive summary of the KEY RISKS and TERMS for the signing party.
    Do NOT introduce yourself. Just give the bullets.
    
    CONTRACT TEXT:
    {full_text[:3000]}
    """
    return call_llm(prompt, is_json=False)

def get_chat_response(context, query):
    prompt = f"Context: {context[:4000]}\nQuery: {query}\nAnswer briefly based on context."
    return call_llm(prompt, is_json=False)
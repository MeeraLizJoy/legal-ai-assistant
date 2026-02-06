import pymupdf
import re
import spacy
import os
from langdetect import detect, DetectorFactory
from legal_engine import call_llm
import docx
import streamlit as st

DetectorFactory.seed = 0

@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except:
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")
    
def extract_text(file_obj, file_extension):
    """Extracts text and fixes common formatting issues that confuse AI."""
    text = ""
    if file_extension == '.pdf':
        file_obj.seek(0)
        doc = pymupdf.open(stream=file_obj.read(), filetype="pdf")
        for page in doc:
            text += page.get_text("text") + "\n"
    elif file_extension == '.docx':
        doc = docx.Document(file_obj)
        text = " ".join([para.text for para in doc.paragraphs])
    elif file_extension == '.txt':
        text = file_obj.read().decode('utf-8')
    
    # FIX: Merge hyphenated words and fix currency spacing
    text = text.replace('Rs.\n', 'Rs. ').replace('Rs. ', 'Rs.')
    return text

def segment_into_clauses(raw_text):
    # Regex to catch "1. Title", "ARTICLE 1", "WHEREAS", etc.
    pattern = r'(?:\n|^)(\d+\.\s+[A-Z][a-zA-Z\s]+|\bARTICLE\s+\d+\b|\bWHEREAS\b|[A-Z][A-Z\s]{5,}:)'
    
    parts = re.split(pattern, raw_text)
    clauses = []
    
    # If split failed, treat whole text as one context
    if len(parts) < 2: 
        return [{"header": "Contract Terms", "content": raw_text}]

    # Reconstruct header + content pairs
    # We skip index 0 if it's just preamble text
    start_idx = 1 if len(parts) > 1 else 0
    
    for i in range(start_idx, len(parts)-1, 2):
        header = parts[i].strip()
        content = parts[i+1].strip()
        
        # Clean up header (e.g. remove "WHEREAS" duplicates)
        if header == "WHEREAS":
            header = "Recital (Background)"
            
        if len(content.split()) > 5: # Filter out noise
            clauses.append({"header": header, "content": content})
            
    return clauses

def process_multilingual_clause(content):
    try:
        if detect(content) == "hi":
            prompt = f"Translate this Hindi legal clause to English: {content}"
            return call_llm(prompt, is_json=False), True
    except: pass
    return content, False

def get_entities(text):
    doc = nlp(text)
    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    
    # --- HARDCODED REGEX FIX FOR FINANCIALS ---
    # Spacy misses "Rs. 50,000/-". Regex catches it.
    money_pattern = r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?|Rupees\s+[a-zA-Z\s]+'
    matches = re.findall(money_pattern, text, re.IGNORECASE)
    
    for m in matches:
        clean_money = m.strip()
        # Only add if it looks like a valid amount
        if len(clean_money) > 3:
            entities.append({"text": clean_money, "label": "MONEY"})
            
    return entities

nlp = load_nlp()
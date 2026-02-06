import fitz
import re
import spacy
import os
import docx
import streamlit as st
from langdetect import detect, DetectorFactory
from legal_engine import call_llm

DetectorFactory.seed = 0

@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")
    
nlp = load_nlp()
    
def extract_text(file_obj, file_extension):
    """Extracts text using the safe 'fitz' library."""
    text = ""
    try:
        if file_extension == '.pdf':
            file_obj.seek(0)
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")
            for page in doc:
                text += page.get_text("text") + "\n"
        elif file_extension == '.docx':
            doc = docx.Document(file_obj)
            text = " ".join([para.text for para in doc.paragraphs])
        elif file_extension == '.txt':
            text = file_obj.read().decode('utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
    # Formatting Cleanup
    text = text.replace('Rs.\n', 'Rs. ').replace('Rs. ', 'Rs.')
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text) # Remove page numbers
    return text

def segment_into_clauses(raw_text):
    """
    Robust segmentation that catches 1., 1.1, (a), Article, and All-Caps Headers.
    """
    clauses = []
    
    # Combined regex for multiple numbering styles
    # Group 1: Standard (1. Title)
    # Group 2: Articles (ARTICLE 1)
    # Group 3: Sub-clauses ((a) or 1.1)
    # Group 4: Standard CAPS Headers (WHEREAS)
    pattern = r'(?:\n|^)\s*(?:(\d+\.\s+[A-Za-z]+)|(ARTICLE\s+[IVX0-9]+)|(\([a-z0-9]+\)|[0-9]+\.[0-9]+)|(WHEREAS|NOW THEREFORE|IN WITNESS|DEFINITIONS|[A-Z\s]{5,}:))'
    
    # Split while keeping the delimiters (headers)
    parts = re.split(f"({pattern})", raw_text)
    
    # If regex failed to split anything substantial, fallback to paragraph splitting
    if len(parts) < 3: 
        return [{"header": "Contract Terms", "content": raw_text}]

    current_header = "Preamble / Recital"
    
    for part in parts:
        if not part or part.strip() == "": continue
        
        # Check if this part is a header (matches our regex pattern loosely)
        is_header = re.match(r'^\s*(\d+\.|ARTICLE|\(|WHEREAS|[A-Z\s]{5,}:)', part)
        
        if is_header:
            current_header = part.strip()
            # Normalize "WHEREAS"
            if "WHEREAS" in current_header.upper(): current_header = "Recital (Background)"
        else:
            # It is content
            content = part.strip()
            if len(content) > 20: # Filter out tiny noise
                clauses.append({"header": current_header, "content": content})
            
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
    
    money_pattern = r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?|Rupees\s+[a-zA-Z\s]+'
    matches = re.findall(money_pattern, text, re.IGNORECASE)
    
    for m in matches:
        if len(m.strip()) > 3:
            entities.append({"text": m.strip(), "label": "MONEY"})
            
    return entities
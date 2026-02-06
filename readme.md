# AI Legal Shield for Indian SMEs

**Legal AI Assistant** is a sophisticated GenAI-powered legal assistant designed to help Indian Small and Medium Business (SME) owners understand complex contracts, identify risks, and receive actionable advice in plain language.

Built for the **[HCL GUVI Hackathon]**, this solution specifically addresses the challenges of the Indian legal landscape, including multilingual support (Hindi/English) and compliance with the **Indian Contract Act, 1872**.

---

## 🚀 Key Features

### 🧠 Core Legal AI
* **Automated Risk Scoring:** Instantly calculates a composite risk score (0-100) for any contract.
* **Clause-by-Clause Analysis:** Breaks down complex legalese into simple business English.
* **Modality Detection:** Explicitly identifies **OBLIGATIONS** (Must do), **RIGHTS** (Can do), and **PROHIBITIONS** (Must not do).
* **Ambiguity Flagging:** Detects vague terms (e.g., "reasonable time") that could lead to disputes.

### 🇮🇳 Indian SME Specifics
* **Multilingual Processing:** Seamlessly handles contracts mixed with **Hindi** and English, translating clauses for analysis.
* **Indian Law Compliance:** Checks against specific sections of the *Indian Contract Act, 1872*.
* **Deviation Analysis:** Compares clauses against standard "Fair" templates to spot unfavorable terms.

### 🛠️ Utilities & Compliance
* **Audit Trails:** Automatically saves a JSON log of every analysis for compliance and historical review.
* **Knowledge Base:** Tracks the number of contracts analyzed to build a repository of common issues.
* **Drafting Templates:** Generates standardized, legally compliant templates (NDA, Employment, Service Agreements).
* **PDF Reports:** Exports a professional "Legal Audit Report" for offline review.

---

## ⚙️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/)
* **LLM Engine:** [Groq](https://groq.com/) (Llama-3.1-8b-instant) for high-speed legal reasoning.
* **NLP & Processing:** * `spaCy` for Named Entity Recognition (NER).
    * `PyMuPDF` & `python-docx` for text extraction.
    * `langdetect` for Hindi language identification.
* **Report Generation:** `fpdf2` for creating structured PDF audits.

---

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/nyayasetu-legal-ai.git](https://github.com/your-username/legal-ai-assistant.git)
    cd legal-ai-assistant
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**
    Create a `.env` file in the root directory and add your Groq API key:
    ```bash
    GROQ_API_KEY="gsk_your_api_key_here"
    ```

4.  **Download NLP Models**
    The app will automatically download the required spaCy model, but you can also do it manually:
    ```bash
    python -m spacy download en_core_web_sm
    ```

---

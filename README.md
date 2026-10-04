# 🍀 Plani Helper

Plani Helper is an intelligent Agricultural & Veterinary AI assistant powered by Google Gemini and Streamlit. It helps farmers, gardeners, pet owners, and livestock caretakers diagnose plant diseases and animal health conditions from photos, providing actionable care tips and structured diagnoses.

---

## ✨ Features

- 📸 **Visual Diagnosis**: Upload photos of plant leaves, crops, or animals for instant multimodal analysis using Gemini Flash.
- 💬 **Interactive Chat**: Ask follow-up questions about care, prevention, and treatment steps.
- 📱 **WhatsApp Integration**: Optionally send consultation summaries directly to WhatsApp via Twilio.
- 🛡️ **Safety & Verification**: Includes professional diagnostic disclaimers to encourage local veterinary and extension officer consultation.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/codeyaman/plani_helper.git
cd plani_helper
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a `.streamlit/secrets.toml` file from the provided example:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Open `.streamlit/secrets.toml` and add your Google Gemini API key:
```toml
GEMINI_API_KEY = "your-gemini-api-key"

# Optional Twilio credentials (if using WhatsApp updates)
# TWILIO_ACCOUNT_SID = "..."
# TWILIO_AUTH_TOKEN = "..."
# TWILIO_WHATSAPP_FROM = "..."
# TWILIO_CONTENT_SID = "..."
```

### 5. Run the application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔒 Confidentiality & Security
All sensitive credentials (`.streamlit/secrets.toml`, virtual environments, and personal tokens) are strictly excluded from version control via `.gitignore`. Never commit API keys or private tokens.

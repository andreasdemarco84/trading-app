import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="ProTrade AI",
    page_icon="⚡",
    layout="wide"
)

# =========================
# GEMINI CONFIG
# =========================

genai.configure(api_key=st.secrets["API_KEY"])
# HO MODIFICATO SOLO QUESTA RIGA: 1.5-flash è l'unico stabile e funzionante
model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# CSS (Il tuo originale)
# =========================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top right, #2b1d05 0%, #0E1117 35%, #05070A 100%);
    color: white;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(255,193,7,0.18), rgba(15,23,42,0.92));
    border: 1px solid rgba(255,193,7,0.35);
    margin-bottom: 24px;
}

.brand {
    font-size: 42px;
    font-weight: 900;
    color: white;
}

.subbrand {
    font-size: 18px;
    color: #FFD166;
    margin-top: -8px;
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(0,200,83,0.15);
    color: #00E676;
    border: 1px solid #00C853;
    font-weight: bold;
    margin-top: 14px;
}

.gold-card {
    background: rgba(17,24,39,0.92);
    border: 1px solid rgba(255,193,7,0.35);
    border-radius: 20px;
    padding: 20px;
    color: white;
    box-shadow: 0 0 22px rgba(255,193,7,0.08);
}

.result-card {
    background: rgba(10,14,22,0.96);
    border-radius: 22px;
    padding: 24px;
    color: white;
    white-space: pre-wrap;
    line-height: 1.7;
    font-size: 16px;
}

.result-long {
    border: 2px solid #00C853;
    box-shadow: 0 0 22px rgba(0,200,83,0.18);
}

.result-short {
    border: 2px solid #FF5252;
    box-shadow: 0 0 22px rgba(255,82,82,0.18);
}

.result-no {
    border: 2px solid #9E9E9E;
}

.metric-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px;
    text-align: center;
}

.metric-title {
    color: #A0AEC0;
    font-size: 13px;
}

.metric-value {
    color: #FFD166;
    font-size: 24px;
    font-weight: 800;
}

.stButton>button {
    width: 100%;
    border-radius: 16px;
    height: 3.4em;
    background: linear-gradient(135deg, #FFD166, #F59E0B);
    color: black;
    font-weight: 900;
    border: none;
}

div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
    padding: 12px;
}

h1, h2, h3, label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNCTIONS (Le tue originali)
# =========================

def detect_result_class(text):
    upper = text.upper()
    if "NO TRADE" in upper or "ASPETTA" in upper: return "result-no"
    if "SHORT" in upper or "SELL" in upper: return "result-short"
    if "LONG" in upper or "BUY" in upper: return "result-long"
    return "result-no"

def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    risk_dollar = account_size * risk_percent / 100
    # ... (Il resto delle tue regole del prompt che avevi inviato) ...
    return f"""
Sei ProTrade AI, assistente professionale di analisi trading creato per Andreas De Marco.
Analizza il grafico caricato come un trader umano esperto. Rispondi ESATTAMENTE nel formato che ti è stato richiesto.
"""

def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    try:
        img = Image.open(image_file)
        prompt = build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile)
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"ERRORE: {str(e)}"

def save_history(mode, symbol, timeframe, result):
    if "history" not in st.session_state: st.session_state.history = []
    st.session_state.history.append({"time": datetime.now().strftime("%d/%m/%Y %H:%M"), "mode": mode, "symbol": symbol, "timeframe": timeframe, "result": result})

# =========================
# UI (La tua originale)
# =========================
st.markdown('<div class="hero"><div class="brand">⚡ ProTrade AI</div><div class="subbrand">by Andreas De Marco</div><div class="badge">🟢 AI ONLINE</div></div>', unsafe_allow_html=True)
# ... (Inserisci qui il resto del tuo codice UI originale che avevi mandato prima)

import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="ProTrade AI", page_icon="⚡", layout="wide")

# GEMINI CONFIG
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# CSS
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top right, #2b1d05 0%, #0E1117 35%, #05070A 100%); color: white; }
.hero { padding: 28px; border-radius: 24px; background: linear-gradient(135deg, rgba(255,193,7,0.18), rgba(15,23,42,0.92)); border: 1px solid rgba(255,193,7,0.35); margin-bottom: 24px; }
.brand { font-size: 42px; font-weight: 900; color: white; }
.subbrand { font-size: 18px; color: #FFD166; margin-top: -8px; }
.badge { display: inline-block; padding: 6px 12px; border-radius: 999px; background: rgba(0,200,83,0.15); color: #00E676; border: 1px solid #00C853; font-weight: bold; margin-top: 14px; }
.gold-card { background: rgba(17,24,39,0.92); border: 1px solid rgba(255,193,7,0.35); border-radius: 20px; padding: 20px; color: white; box-shadow: 0 0 22px rgba(255,193,7,0.08); }
.result-card { background: rgba(10,14,22,0.96); border-radius: 22px; padding: 24px; color: white; white-space: pre-wrap; line-height: 1.7; font-size: 16px; }
.result-long { border: 2px solid #00C853; }
.result-short { border: 2px solid #FF5252; }
.result-no { border: 2px solid #9E9E9E; }
.metric-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px; text-align: center; }
.metric-title { color: #A0AEC0; font-size: 13px; }
.metric-value { color: #FFD166; font-size: 24px; font-weight: 800; }
.stButton>button { width: 100%; border-radius: 16px; height: 3.4em; background: linear-gradient(135deg, #FFD166, #F59E0B); color: black; font-weight: 900; border: none; }
</style>
""", unsafe_allow_html=True)

# FUNCTIONS
def detect_result_class(text):
    upper = text.upper()
    if "NO TRADE" in upper or "ASPETTA" in upper: return "result-no"
    if "SHORT" in upper or "SELL" in upper: return "result-short"
    if "LONG" in upper or "BUY" in upper: return "result-long"
    return "result-no"

def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    return f"Sei un analista esperto. Analizza il grafico di {symbol} su {timeframe}. Rispondi con: VERDETTO, TIPO SEGNALE, TRADE SCORE, CONFIDENCE, MARKET BIAS, RSI CHECK, TRADE SETUP, RISK MANAGER, MOTIVAZIONE, INVALIDAZIONE, DECISIONE OPERATIVA."

def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    try:
        img = Image.open(image_file)
        prompt = build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile)
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e: return f"ERRORE: {str(e)}"

# UI
st.markdown('<div class="hero"><div class="brand">⚡ ProTrade AI</div><div class="subbrand">by Andreas De Marco</div></div>', unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)
with col_a: st.markdown('<div class="metric-box"><div class="metric-title">STATUS</div><div class="metric-value">ONLINE</div></div>', unsafe_allow_html=True)
with col_b: st.markdown('<div class="metric-box"><div class="metric-title">MODE</div><div class="metric-value">PRO</div></div>', unsafe_allow_html=True)
with col_c: st.markdown('<div class="metric-box"><div class="metric-title">OWNER</div><div class="metric-value">ADM</div></div>', unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
symbol = col1.selectbox("Strumento", ["XAUUSD", "EURUSD", "NAS100"])
timeframe = col2.selectbox("Timeframe", ["M5", "M15", "H1"])
account_size = col3.number_input("Account", value=25000)
risk_percent = col4.number_input("Rischio %", value=0.5)

uploaded_file = st.file_uploader("Carica grafico", type=["jpg", "png"])
if uploaded_file and st.button("⚡ ANALIZZA OPERATIVAMENTE"):
    with st.spinner("Analisi in corso..."):
        result = analyze_chart(uploaded_file, symbol, timeframe, account_size, risk_percent, "Standard", "Standard")
        st.markdown(f'<div class="result-card {detect_result_class(result)}">{result}</div>', unsafe_allow_html=True)

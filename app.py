import streamlit as st
from PIL import Image
import google.generativeai as genai

# Configurazione API
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# --- UI CSS ---
st.set_page_config(page_title="ProTrade AI", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #05070A; color: white; }
    .metric-card { background: #111827; border: 1px solid #FFD166; border-radius: 15px; padding: 20px; text-align: center; }
    .label { color: #A0AEC0; font-size: 12px; }
    .value { color: #FFD166; font-size: 20px; font-weight: 800; }
    .big-card { background: #0a0e16; border-radius: 20px; padding: 25px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- PROMPT STRUTTURATO ---
def build_prompt():
    return """
Analizza il grafico come un analista pro. Rispondi ESTREMATAMENTE in questo formato chiave-valore per ogni riga (non aggiungere altro):
VERDETTO: [LONG/SHORT/ASPETTA]
ENTRY: [Prezzo]
SL: [Prezzo]
TP1: [Prezzo]
TP2: [Prezzo]
RR: [Rapporto]
MOTIVAZIONE: [Spiegazione breve]
"""

# --- LOGICA ---
def analyze_chart(image_file):
    try:
        img = Image.open(image_file)
        response = model.generate_content([build_prompt(), img])
        return response.text
    except Exception as e:
        return f"ERRORE: {str(e)}"

# --- UI ---
st.title("⚡ ProTrade AI Dashboard")
uploaded_file = st.file_uploader("Carica grafico", type=["png", "jpg"])

if uploaded_file and st.button("⚡ ANALIZZA"):
    with st.spinner("Analisi Tecnica in corso..."):
        result = analyze_chart(uploaded_file)
        
        # Display dati in box grafici
        cols = st.columns(4)
        lines = result.split('\n')
        
        # Estrazione dati semplici
        data = {line.split(': ')[0]: line.split(': ')[1] for line in lines if ': ' in line}
        
        cols[0].markdown(f"<div class='metric-card'><div class='label'>ENTRY</div><div class='value'>{data.get('ENTRY', '-')}</div></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='metric-card'><div class='label'>STOP LOSS</div><div class='value'>{data.get('SL', '-')}</div></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='metric-card'><div class='label'>TAKE PROFIT 1</div><div class='value'>{data.get('TP1', '-')}</div></div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='metric-card'><div class='label'>R/R</div><div class='value'>{data.get('RR', '-')}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-card'><b>MOTIVAZIONE:</b><br>{data.get('MOTIVAZIONE', result)}</div>", unsafe_allow_html=True)

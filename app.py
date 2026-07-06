import streamlit as st
from PIL import Image
import google.generativeai as genai
import os

# Configurazione sicura: legge la chiave dalle impostazioni di Streamlit
# Non devi modificare nulla qui dentro!
genai.configure(api_key=st.secrets["API_KEY"]) 
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# --- CSS PRO ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .signal-card { background-color: #1a1a1a; padding: 20px; border-radius: 15px; border: 2px solid #444; color: white; font-family: sans-serif; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FFD700; color: black; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- ANALISI ---
def analyze_chart(image_file):
    system_prompt = "Sei un analista tecnico senior. Analizza il layout a 3 grafici (H1, M15, M5) e fornisci: SENTIMENT, ENTRY, SL, TP1, TP2, RR e Motivazione Tecnica."
    try:
        img = Image.open(image_file)
        response = model.generate_content([system_prompt, img])
        return response.text
    except Exception as e:
        return f"Errore: {str(e)}"

# --- INTERFACCIA ---
st.title("⚡ Pro-Trade AI Dashboard")
uploaded_file = st.file_uploader("Carica layout (H1, M15, M5)", type=["jpg", "png"])
if uploaded_file and st.button("ANALIZZA"):
    result = analyze_chart(uploaded_file)
    st.markdown(f"<div class='signal-card'>{result}</div>", unsafe_allow_html=True)

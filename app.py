import streamlit as st
from PIL import Image
import google.generativeai as genai

# Configurazione API sicura
genai.configure(api_key=st.secrets["API_KEY"]) 
# Usiamo un modello progettato specificamente per le immagini
model = genai.GenerativeModel('gemini-pro-vision')

# --- CSS PRO ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .signal-card { 
        background-color: #1a1a1a; padding: 20px; border-radius: 15px; 
        border: 2px solid #444; color: white; font-family: sans-serif; 
    }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3em; 
        background-color: #FFD700; color: black; font-weight: bold; 
    }
</style>
""", unsafe_allow_html=True)

# --- ANALISI ---
def analyze_chart(image_file):
    system_prompt = "Sei un analista tecnico. Analizza il grafico: SENTIMENT, ENTRY, SL, TP1, TP2, RR e Motivazione."
    try:
        img = Image.open(image_file)
        response = model.generate_content([system_prompt, img])
        return response.text
    except Exception as e:
        return f"Errore: {str(e)}"

# --- INTERFACCIA ---
st.title("⚡ Pro-Trade AI Dashboard")
uploaded_file = st.file_uploader("Carica grafico", type=["jpg", "png"])

if uploaded_file and st.button("ANALIZZA OPERATIVAMENTE"):
    with st.spinner("Analisi in corso..."):
        result = analyze_chart(uploaded_file)
        st.markdown(f"<div class='signal-card'>{result}</div>", unsafe_allow_html=True)

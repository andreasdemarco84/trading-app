import streamlit as st
import google.generativeai as genai
from PIL import Image

# Configurazione della pagina
st.set_page_config(page_title="Analizzatore Trading Operativo", layout="wide")
st.title("Analizzatore Grafici Trading - Versione Operativa")

# Input chiave API
api_key = st.text_input("Inserisci la tua API Key di Google:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Utilizzo del modello verificato come attivo sul tuo account
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    uploaded_file = st.file_uploader("Carica lo screenshot del grafico...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Grafico in analisi", use_container_width=True)
        
        if st.button("Analizza Operativamente"):
            prompt = """
            Analizza questo grafico di trading in modo estremamente operativo e professionale.
            Non scrivere analisi generiche. Il tuo obiettivo è generare un setup di trading.
            
            Fornisci i dati in questo formato rigido:
            1. ENTRY: [Prezzo di ingresso]
            2. STOP LOSS: [Livello di protezione]
            3. TARGET 1 (TP1): [Primo obiettivo]
            4. TARGET 2 (TP2): [Secondo obiettivo]
            5. RISCHIO/RENDIMENTO: [Rapporto calcolato]
            6. MOTIVAZIONE: [Breve spiegazione tecnica basata su supporti/resistenze o pattern visibili]
            
            Se non vedi un setup chiaro, scrivi: "NESSUN SETUP CHIARO - ATTENDERE".
            """
            
            with st.spinner('Analisi in corso...'):
                response = model.generate_content([prompt, img])
                st.subheader("Risultato Analisi:")
                st.write(response.text)
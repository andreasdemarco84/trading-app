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
 

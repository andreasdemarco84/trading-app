import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime

st.set_page_config(
    page_title="Pro-Trade AI Dashboard",
    page_icon="⚡",
    layout="wide"
)

# API
genai.configure(api_key=st.secrets["API_KEY"])

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# CSS
st.markdown("""
<style>
.stApp {background-color: #0E1117; color: white;}
.main-card {
    background-color: #161B22;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #30363D;
    color: white;
    line-height: 1.6;
    white-space: pre-wrap;
}
.result-long {border: 2px solid #00C853;}
.result-short {border: 2px solid #FF5252;}
.result-no {border: 2px solid #9E9E9E;}
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
    background-color: #FFD700;
    color: black;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode):
    risk_dollar = account_size * risk_percent / 100

    return f"""
Sei un analista tecnico professionale per trading intraday e prop firm.

Analizza SOLO il grafico caricato.
Non inventare dati che non vedi.
Se il setup non è pulito, devi rispondere NO TRADE.
Meglio nessun trade che un trade forzato.

DATI OPERATIVI:
- Strumento: {symbol}
- Timeframe: {timeframe}
- Account: {account_size} USD
- Rischio massimo: {risk_percent}%
- Rischio massimo in dollari: {risk_dollar:.2f} USD
- Modalità prop firm: {prop_mode}

Valuta:
- Trend principale
- Struttura del mercato
- Supporti e resistenze
- Liquidità sopra/sotto
- Possibile BOS / CHOCH
- Spike o false rotture
- Qualità dell'ingresso
- Posizione dello stop loss
- Take profit realistici
- Rapporto rischio/rendimento

Rispondi ESATTAMENTE con questo formato:

VERDETTO:
LONG / SHORT / NO TRADE

CONFIDENCE:
0-100%

QUALITÀ SETUP:
voto da 1 a 10

CONTESTO MERCATO:
Trend:
Struttura:
Volatilità:
Zone chiave:

LIVELLI OPERATIVI:
Entry:
Stop Loss:
TP1:
TP2:
TP3:
Risk/Reward:

GESTIONE RISCHIO:
Rischio massimo:
Size consigliata:
Breakeven:
Parziale:

MOTIVAZIONE:
Spiegazione pratica.

INVALIDAZIONE:
Quando il setup non è più valido.

ATTENZIONE:
Problemi o rischi visibili sul grafico.

REGOLA FINALE:
Se non vedi un setup chiaro, scrivi NO TRADE.
"""


def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode):
    try:
        img = Image.open(image_file)
        prompt = build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode)
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"ERRORE: {str(e)}"


def detect_result_class(text):
    upper = text.upper()
    if "NO TRADE" in upper:
        return "result-no"
    if "SHORT" in upper:
        return "result-short"
    if "LONG" in upper:
        return "result-long"
    return ""


# UI
st.title("⚡ Pro-Trade AI Dashboard")
st.caption("Analisi AI del grafico con Entry, Stop Loss, Take Profit, RR e modalità NO TRADE")

col1, col2, col3, col4 = st.columns(4)

with col1:
    symbol = st.selectbox(
        "Strumento",
        ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"]
    )

with col2:
    timeframe = st.selectbox(
        "Timeframe",
        ["M1", "M5", "M15", "M30", "H1", "H4"]
    )

with col3:
    account_size = st.number_input(
        "Account USD",
        min_value=1000,
        value=25000,
        step=1000
    )

with col4:
    risk_percent = st.number_input(
        "Rischio %",
        min_value=0.1,
        max_value=5.0,
        value=0.5,
        step=0.1
    )

prop_mode = st.selectbox(
    "Modalità",
    ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"]
)

uploaded_file = st.file_uploader(
    "Carica screenshot grafico",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(uploaded_file, caption="Grafico caricato", use_container_width=True)

if uploaded_file and st.button("ANALIZZA OPERATIVAMENTE"):
    with st.spinner("Analisi in corso..."):
        result = analyze_chart(
            uploaded_file,
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode
        )

        css_class = detect_result_class(result)

        st.markdown("## Risultato")
        st.markdown(
            f"<div class='main-card {css_class}'>{result}</div>",
            unsafe_allow_html=True
        )

        if "history" not in st.session_state:
            st.session_state.history = []

        st.session_state.history.append({
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "symbol": symbol,
            "timeframe": timeframe,
            "result": result
        })

if "history" in st.session_state and st.session_state.history:
    st.markdown("---")
    st.markdown("## Storico ultime analisi")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(f"{item['time']} - {item['symbol']} {item['timeframe']}"):
            st.write(item["result"])

st.markdown("---")
st.warning(
    "Questa app è solo uno strumento di supporto. Non è consulenza finanziaria. "
    "La decisione finale resta tua."
)

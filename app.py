import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime

st.set_page_config(
    page_title="ProTrade AI",
    page_icon="⚡",
    layout="wide"
)

genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

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


def detect_result_class(text):
    upper = text.upper()
    if "NO TRADE" in upper or "ASPETTA" in upper:
        return "result-no"
    if "SHORT" in upper or "SELL" in upper:
        return "result-short"
    if "LONG" in upper or "BUY" in upper:
        return "result-long"
    return "result-no"


def build_prompt(symbol, mode, account_size, risk_percent, prop_mode):
    risk_dollar = account_size * risk_percent / 100

    return f"""
Sei ProTrade AI, assistente professionale di analisi trading creato per Andreas De Marco.

Analizza i grafici caricati.
Devi essere prudente, operativo e preciso.
Se il setup non è chiaro, rispondi NO TRADE.
Se il prezzo è già partito, rispondi ASPETTA.
Non inventare livelli non visibili.

DATI:
Strumento: {symbol}
Modalità analisi: {mode}
Account: {account_size} USD
Rischio massimo: {risk_percent}%
Rischio massimo in dollari: {risk_dollar:.2f} USD
Prop Firm: {prop_mode}

Devi valutare:
- Trend H1/H4 se presenti
- Struttura M15
- Timing M5
- Supporti e resistenze
- Liquidità
- Spike
- False rotture
- Momentum
- Qualità ingresso
- Stop loss tecnico
- TP realistici
- Risk reward
- Gestione prop firm

Rispondi ESATTAMENTE così:

VERDETTO:
LONG / SHORT / ASPETTA / NO TRADE

TRADE SCORE:
0-100

CONFIDENCE:
0-100%

MARKET BIAS:
Trend principale:
Struttura:
Momentum:
Volatilità:

AI THINKING:
✔ Punto 1
✔ Punto 2
✔ Punto 3
✔ Punto 4
✔ Punto 5

TRADE SETUP:
Entry:
Stop Loss:
TP1:
TP2:
TP3:
Risk/Reward:

RISK MANAGER:
Rischio massimo:
Size consigliata:
Breakeven:
Parziale:

MOTIVAZIONE:
Spiegazione pratica.

INVALIDAZIONE:
Quando il setup non è più valido.

DECISIONE OPERATIVA:
ENTRA / ASPETTA / NON OPERARE
"""


def analyze_single(image_file, symbol, timeframe, account_size, risk_percent, prop_mode):
    img = Image.open(image_file)
    prompt = build_prompt(symbol, f"Grafico singolo {timeframe}", account_size, risk_percent, prop_mode)
    response = model.generate_content([prompt, img])
    return response.text


def analyze_mtf(h1_file, m15_file, m5_file, symbol, account_size, risk_percent, prop_mode):
    h1 = Image.open(h1_file)
    m15 = Image.open(m15_file)
    m5 = Image.open(m5_file)

    prompt = build_prompt(
        symbol,
        "Multi-Timeframe H1 + M15 + M5",
        account_size,
        risk_percent,
        prop_mode
    )

    response = model.generate_content([
        prompt,
        "Grafico H1 - direzione principale:", h1,
        "Grafico M15 - struttura e setup:", m15,
        "Grafico M5 - timing ingresso:", m5
    ])

    return response.text


def save_history(mode, symbol, result):
    if "history" not in st.session_state:
        st.session_state.history = []

    st.session_state.history.append({
        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "mode": mode,
        "symbol": symbol,
        "result": result
    })


st.markdown("""
<div class="hero">
    <div class="brand">⚡ ProTrade AI</div>
    <div class="subbrand">by Andreas De Marco</div>
    <div class="badge">🟢 AI ONLINE · Gemini 2.5 Ready</div>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-title">AI STATUS</div>
        <div class="metric-value">ONLINE</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-title">MODE</div>
        <div class="metric-value">PRO</div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-title">OWNER</div>
        <div class="metric-value">ADM</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    symbol = st.selectbox("Strumento", ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"])

with col2:
    account_size = st.number_input("Account USD", min_value=1000, value=25000, step=1000)

with col3:
    risk_percent = st.number_input("Rischio %", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

with col4:
    prop_mode = st.selectbox("Prop Firm", ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"])

risk_dollar = account_size * risk_percent / 100

st.markdown(f"""
<div class="gold-card">
    <b>Risk Manager</b><br>
    Account: {account_size:,.0f} USD · Rischio: {risk_percent}% · Perdita massima: <span style="color:#FFD166;">{risk_dollar:.2f} USD</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

mode = st.radio(
    "Tipo analisi",
    ["Grafico singolo", "Multi-Timeframe H1 + M15 + M5"],
    horizontal=True
)

if mode == "Grafico singolo":
    timeframe = st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4"])

    uploaded = st.file_uploader("Carica screenshot grafico", type=["jpg", "jpeg", "png"], key="single")

    if uploaded:
        st.image(uploaded, caption=f"{symbol} {timeframe}", use_container_width=True)

    if uploaded and st.button("⚡ ANALIZZA GRAFICO"):
        with st.spinner("ProTrade AI sta analizzando il mercato..."):
            try:
                result = analyze_single(uploaded, symbol, timeframe, account_size, risk_percent, prop_mode)
                css_class = detect_result_class(result)

                st.markdown("## Risultato Operativo")
                st.markdown(f"<div class='result-card {css_class}'>{result}</div>", unsafe_allow_html=True)

                save_history("Singolo", symbol, result)

            except Exception as e:
                st.error(f"Errore: {e}")

if mode == "Multi-Timeframe H1 + M15 + M5":
    st.markdown("### Carica i 3 timeframe")

    c1, c2, c3 = st.columns(3)

    with c1:
        h1 = st.file_uploader("H1 - Direzione", type=["jpg", "jpeg", "png"], key="h1")
        if h1:
            st.image(h1, use_container_width=True)

    with c2:
        m15 = st.file_uploader("M15 - Setup", type=["jpg", "jpeg", "png"], key="m15")
        if m15:
            st.image(m15, use_container_width=True)

    with c3:
        m5 = st.file_uploader("M5 - Timing", type=["jpg", "jpeg", "png"], key="m5")
        if m5:
            st.image(m5, use_container_width=True)

    if h1 and m15 and m5:
        if st.button("📊 ANALISI MULTI-TIMEFRAME"):
            with st.spinner("Analisi H1 + M15 + M5 in corso..."):
                try:
                    result = analyze_mtf(h1, m15, m5, symbol, account_size, risk_percent, prop_mode)
                    css_class = detect_result_class(result)

                    st.markdown("## Risultato Multi-Timeframe")
                    st.markdown(f"<div class='result-card {css_class}'>{result}</div>", unsafe_allow_html=True)

                    save_history("Multi-Timeframe", symbol, result)

                except Exception as e:
                    st.error(f"Errore: {e}")
    else:
        st.warning("Carica H1, M15 e M5 per fare l'analisi completa.")

if "history" in st.session_state and st.session_state.history:
    st.markdown("---")
    st.markdown("## Storico Analisi")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(f"{item['time']} · {item['mode']} · {item['symbol']}"):
            st.write(item["result"])

st.markdown("---")
st.caption("⚠️ ProTrade AI by Andreas De Marco è uno strumento di supporto. Non è consulenza finanziaria.")

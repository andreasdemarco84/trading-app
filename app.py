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
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# CSS
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
# FUNCTIONS
# =========================

def detect_result_class(text):
    upper = text.upper()

    if "NO TRADE" in upper or "ASPETTA" in upper:
        return "result-no"

    if "SHORT" in upper or "SELL" in upper:
        return "result-short"

    if "LONG" in upper or "BUY" in upper:
        return "result-long"

    return "result-no"


def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    risk_dollar = account_size * risk_percent / 100

    if ai_profile == "Challenge":
        profile_rule = """
Profilo Challenge:
- Non essere troppo restrittivo.
- Cerca opportunità operative valide.
- Accetta setup buoni anche se non perfetti.
- RR minimo consigliato 1:2.
- Evita comunque trade palesemente sporchi o tardivi.
"""
    elif ai_profile == "Funded":
        profile_rule = """
Profilo Funded:
- Priorità proteggere il conto.
- Sii più selettivo.
- Evita ingressi tardivi.
- Evita trade se RSI, trend e struttura non sono coerenti.
- RR minimo consigliato 1:2.5.
"""
    elif ai_profile == "Scalping":
        profile_rule = """
Profilo Scalping:
- Focus su timing rapido.
- Cerca momentum e conferme veloci.
- Adatto a M1/M5.
- Controlla spike e RSI.
- Evita trade se il movimento è già troppo esteso.
"""
    else:
        profile_rule = """
Profilo Standard:
- Approccio bilanciato.
- Serve setup chiaro ma non perfetto.
- Controlla trend, RSI, struttura e RR.
- RR minimo consigliato 1:2.
"""

    return f"""
Sei ProTrade AI, assistente professionale di analisi trading creato per Andreas De Marco.

Analizza il grafico caricato come un trader umano esperto.
Non dare segnali ciechi.
Non inventare dati non visibili.

DATI OPERATIVI:
Strumento: {symbol}
Timeframe: {timeframe}
Account: {account_size} USD
Rischio massimo: {risk_percent}%
Rischio massimo in dollari: {risk_dollar:.2f} USD
Modalità prop firm: {prop_mode}
Profilo AI: {ai_profile}

{profile_rule}

REGOLE IMPORTANTI:
- LONG/SHORT se il setup è buono e il RR è accettabile.
- ASPETTA se la direzione è chiara ma manca solo conferma o il prezzo è entrato male.
- NO TRADE solo se mercato laterale, sporco, spike forti, RR scarso o livelli non leggibili.
- Controlla SEMPRE RSI se visibile.
- Se RSI è sotto 30, evita nuovi SHORT salvo rottura fortissima.
- Se RSI è sopra 70, evita nuovi LONG salvo breakout pulito.
- Se RSI è tra 40 e 60, consideralo neutro.
- Se RSI diverge contro il trade, abbassa la confidence.
- Non comprare dopo una salita già troppo estesa.
- Non vendere dopo una discesa già troppo estesa.
- Se il trade è buono ma tardi, scrivi ASPETTA PULLBACK.

VALUTA:
- Trend principale
- Struttura del mercato
- Supporti e resistenze
- EMA o media mobile se visibile
- RSI se visibile
- Momentum
- Spike e false rotture
- Qualità ingresso
- Stop loss tecnico
- Take profit realistici
- Risk reward
- Gestione prop firm

Rispondi ESATTAMENTE con questo formato:

VERDETTO:
LONG / SHORT / ASPETTA / NO TRADE

TIPO SEGNALE:
AGGRESSIVO / STANDARD / CONSERVATIVO

TRADE SCORE:
0-100

CONFIDENCE:
0-100%

MARKET BIAS:
Trend principale:
Struttura:
Momentum:
Volatilità:

RSI CHECK:
Valore stimato:
Condizione:
Conferma o blocca il trade:
Nota:

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

AI CHECKLIST:
Trend:
EMA:
RSI:
Momentum:
Struttura:
Risk/Reward:

MOTIVAZIONE:
Spiegazione pratica.

INVALIDAZIONE:
Quando il setup non è più valido.

DECISIONE OPERATIVA:
ENTRA / ASPETTA / NON OPERARE
"""


def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile):
    try:
        img = Image.open(image_file)

        prompt = build_prompt(
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            ai_profile
        )

        response = model.generate_content([prompt, img])
        return response.text

    except Exception as e:
        return f"ERRORE: {str(e)}"


def save_history(mode, symbol, timeframe, result):
    if "history" not in st.session_state:
        st.session_state.history = []

    st.session_state.history.append({
        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "mode": mode,
        "symbol": symbol,
        "timeframe": timeframe,
        "result": result
    })

# =========================
# UI
# =========================

st.markdown("""
<div class="hero">
    <div class="brand">⚡ ProTrade AI</div>
    <div class="subbrand">by Andreas De Marco</div>
    <div class="badge">🟢 AI ONLINE · Gemini 2.5 Flash</div>
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

col5, col6 = st.columns(2)

with col5:
    prop_mode = st.selectbox(
        "Prop Firm",
        ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"]
    )

with col6:
    ai_profile = st.selectbox(
        "Profilo AI",
        ["Standard", "Challenge", "Funded", "Scalping"]
    )

risk_dollar = account_size * risk_percent / 100

st.markdown(f"""
<div class="gold-card">
    <b>Risk Manager</b><br>
    Account: {account_size:,.0f} USD · Rischio: {risk_percent}% · Perdita massima:
    <span style="color:#FFD166;">{risk_dollar:.2f} USD</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

uploaded_file = st.file_uploader(
    "Carica screenshot grafico con RSI visibile se possibile",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(
        uploaded_file,
        caption=f"{symbol} {timeframe}",
        use_container_width=True
    )

if uploaded_file and st.button("⚡ ANALIZZA OPERATIVAMENTE"):
    with st.spinner("ProTrade AI sta analizzando il mercato..."):
        result = analyze_chart(
            uploaded_file,
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            ai_profile
        )

        css_class = detect_result_class(result)

        st.markdown("## Risultato Operativo")
        st.markdown(
            f"<div class='result-card {css_class}'>{result}</div>",
            unsafe_allow_html=True
        )

        save_history("Singolo", symbol, timeframe, result)

# =========================
# HISTORY
# =========================

if "history" in st.session_state and st.session_state.history:
    st.markdown("---")
    st.markdown("## Storico Analisi")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(f"{item['time']} · {item['mode']} · {item['symbol']} {item['timeframe']}"):
            st.write(item["result"])

st.markdown("---")
st.caption(
    "⚠️ ProTrade AI by Andreas De Marco è uno strumento di supporto. "
    "Non è consulenza finanziaria. Usa sempre gestione del rischio."
)

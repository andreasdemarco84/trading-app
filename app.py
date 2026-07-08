import streamlit as st
from PIL import Image
import google.generativeai as genai
import re
from datetime import datetime

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="ProTrade AI",
    page_icon="⚡",
    layout="wide"
)

genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# SESSION STATE
# =========================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_update" not in st.session_state:
    st.session_state.last_update = None

if "profile" not in st.session_state:
    st.session_state.profile = "Standard"

# =========================
# CSS
# =========================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top right,#12210d 0%,#0E1117 40%,#05070A 100%);
    color: white;
}

section[data-testid="stSidebar"] {
    background: #0A0D12;
    border-right: 1px solid rgba(255,255,255,.08);
}

h1,h2,h3,h4,label {
    color: white !important;
}

.header {
    padding: 20px;
    border-radius: 22px;
    background: linear-gradient(135deg,rgba(0,200,83,.12),rgba(15,23,42,.95));
    border: 1px solid rgba(0,230,118,.25);
    margin-bottom: 20px;
}

.brand {
    font-size: 32px;
    font-weight: 900;
}

.sub {
    color: #9AE6B4;
    font-size: 14px;
}

.card {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
}

.signal {
    border-radius: 22px;
    padding: 26px;
    margin-bottom: 16px;
}

.long {
    background: rgba(0,60,25,.62);
    border: 2px solid #00C853;
}

.short {
    background: rgba(70,10,10,.62);
    border: 2px solid #FF5252;
}

.no {
    background: rgba(35,35,35,.65);
    border: 2px solid #9E9E9E;
}

.signal-title {
    font-size: 44px;
    font-weight: 900;
    line-height: 1;
}

.small {
    color: #A0AEC0;
    font-size: 13px;
}

.metric {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 16px;
    text-align: center;
    min-height: 115px;
}

.metric-title {
    color: #A0AEC0;
    font-size: 12px;
    font-weight: 800;
}

.metric-value {
    font-size: 20px;
    font-weight: 900;
    margin-top: 8px;
    word-break: break-word;
}

.stButton>button {
    width: 100%;
    border-radius: 12px;
    background: rgba(255,255,255,.06);
    color: white;
    font-weight: 800;
    border: 1px solid rgba(255,255,255,.12);
}
</style>
""", unsafe_allow_html=True)

# =========================
# DEFAULT RESULT
# =========================

def default_result():
    return {
        "VERDETTO": "NO TRADE",
        "BIAS": "NEUTRO",
        "SETUP_QUALITY": "C",
        "SETUP_TYPE": "NESSUN SETUP",
        "TIPO_ORDINE": "NESSUN ORDINE",
        "ENTRY": "N/D",
        "STOP_LOSS": "N/D",
        "INVALIDAZIONE": "N/D",
        "TP1": "N/D",
        "TP2": "N/D",
        "TP3": "N/D",
        "RISK_REWARD": "N/D",
        "CONFIDENCE": "0",
        "TRADE_SCORE": "0",
        "DECISIONE": "NON OPERARE",
        "PARZIALE": "N/D",
        "BREAKEVEN": "N/D",
        "TRAILING": "N/D",
        "ANALISI": "Nessun setup valido.",
        "MOTIVO_NO_TRADE": "Setup non abbastanza chiaro."
    }

# =========================
# UTILS
# =========================

def parse_key_value_response(text):
    result = default_result()

    for raw_line in str(text).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()

        if key in result:
            result[key] = value

    result["VERDETTO"] = result["VERDETTO"].upper()
    result["BIAS"] = result["BIAS"].upper()
    result["SETUP_QUALITY"] = result["SETUP_QUALITY"].upper()
    result["SETUP_TYPE"] = result["SETUP_TYPE"].upper()
    result["TIPO_ORDINE"] = result["TIPO_ORDINE"].upper()
    result["DECISIONE"] = result["DECISIONE"].upper()

    return result


def has_number(value):
    return re.search(r"\d", str(value)) is not None


def extract_number(value, default=0):
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))

    if match:
        try:
            return float(match.group(1))
        except Exception:
            return default

    return default


def is_missing(value):
    value = str(value).strip().upper()
    return value in ["", "N/D", "N/A", "-", "NONE", "NULL"]


def valid_trade(data):
    verdict = data.get("VERDETTO", "").upper()

    if verdict not in ["LONG", "SHORT"]:
        return True

    required_fields = [
        "ENTRY",
        "STOP_LOSS",
        "INVALIDAZIONE",
        "TP1",
        "TP2",
        "TP3",
        "RISK_REWARD"
    ]

    for field in required_fields:
        if is_missing(data.get(field, "")):
            return False

    for field in ["ENTRY", "STOP_LOSS", "INVALIDAZIONE", "TP1", "TP2", "TP3"]:
        if not has_number(data.get(field, "")):
            return False

    confidence = int(extract_number(data.get("CONFIDENCE", "0"), 0))
    score = int(extract_number(data.get("TRADE_SCORE", "0"), 0))
    quality = data.get("SETUP_QUALITY", "C").upper()
    order_type = data.get("TIPO_ORDINE", "").upper()

    if quality == "C":
        return False

    if confidence < 60:
        return False

    if score < 65:
        return False

    if quality == "B" and order_type in ["MARKET BUY", "MARKET SELL"]:
        return False

    return True


def force_no_trade(reason):
    data = default_result()
    data["ANALISI"] = reason
    data["MOTIVO_NO_TRADE"] = reason
    return data


def result_to_text(data):
    order = [
        "VERDETTO",
        "BIAS",
        "SETUP_QUALITY",
        "SETUP_TYPE",
        "TIPO_ORDINE",
        "ENTRY",
        "STOP_LOSS",
        "INVALIDAZIONE",
        "TP1",
        "TP2",
        "TP3",
        "RISK_REWARD",
        "CONFIDENCE",
        "TRADE_SCORE",
        "DECISIONE",
        "PARZIALE",
        "BREAKEVEN",
        "TRAILING",
        "ANALISI",
        "MOTIVO_NO_TRADE"
    ]

    lines = []

    for key in order:
        lines.append(f"{key}={data.get(key, 'N/D')}")

    return "\n".join(lines)


def signal_style(verdict):
    verdict = str(verdict).upper()

    if verdict == "LONG":
        return "long", "#00E676", "🐂"

    if verdict == "SHORT":
        return "short", "#FF5252", "🐻"

    return "no", "#BDBDBD", "⛔"


def get_session():
    hour = datetime.now().hour

    if 0 <= hour < 7:
        return "ASIA"

    if 7 <= hour < 13:
        return "LONDRA"

    if 13 <= hour < 16:
        return "LONDRA/NY"

    if 16 <= hour < 22:
        return "NEW YORK"

    return "CHIUSA"

# =========================
# PROMPT
# =========================

def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, profile,
                 rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):

    risk_dollar = account_size * risk_percent / 100

    if profile == "Challenge":
        profile_rule = """
PROFILO CHALLENGE:
Puoi accettare setup B solo con ordine pendente.
Setup A+ può essere market o pendente.
Setup C è sempre NO TRADE.
"""
    elif profile == "Funded":
        profile_rule = """
PROFILO FUNDED:
Massima selezione.
Solo setup A+ può essere segnale.
Setup B solo ordine pendente molto pulito.
Se hai dubbio, NO TRADE.
"""
    elif profile == "Scalping":
        profile_rule = """
PROFILO SCALPING:
Serve timing chiaro.
Non inseguire candele già esplose.
Setup B solo ordine pendente.
Setup C NO TRADE.
"""
    else:
        profile_rule = """
PROFILO STANDARD:
Setup A+ può essere segnale.
Setup B solo ordine pendente.
Setup C NO TRADE.
"""

    focus = []

    if show_ema:
        focus.append("EMA/media visibile: usala come filtro trend e zona dinamica.")
    if show_rsi:
        focus.append("RSI visibile: sopra/sotto 50 aiuta, estremi evitano entrate tardive.")
    if show_levels:
        focus.append("Livelli visibili: supporti, resistenze, massimi/minimi, retest.")
    if show_volume:
        focus.append("Volumi visibili: usali solo se chiari.")

    focus_block = " ".join(focus) if focus else "Analizza il grafico visibile."

    mtf_block = ""
    if multi_tf:
        mtf_block = """
Se vedi solo un timeframe, lavora su quello.
Se timeframe è H1/H4, evita segnali da scalping.
Se timeframe è M1/M5/M15, dai più peso al timing.
"""

    return f"""
Sei ProTrade AI.

Devi applicare SEMPRE la stessa strategia.
Non devi cambiare ragionamento.
Non devi inventare.
Non devi cercare segnali per forza.

DATI:
Strumento: {symbol}
Timeframe: {timeframe}
Account: {account_size} USD
Rischio massimo: {risk_percent}%
Rischio massimo dollari: {risk_dollar:.2f} USD
Prop firm: {prop_mode}
Profilo: {profile}
RR minimo: {rr_minimo}

{profile_rule}

{mtf_block}

FOCUS:
{focus_block}

==================================================
PROTRADE FIXED STRATEGY
==================================================

La strategia è sempre questa.

FASE 1: TREND
Trend LONG valido solo se:
- massimi e minimi crescenti
- prezzo sopra EMA/media oppure sopra supporto chiave
- struttura rialzista leggibile

Trend SHORT valido solo se:
- massimi e minimi decrescenti
- prezzo sotto EMA/media oppure sotto resistenza chiave
- struttura ribassista leggibile

Se il trend non è chiaro:
NO TRADE.

FASE 2: CERCA SOLO 2 SETUP

SETUP 1: PULLBACK IN TREND
LONG:
- trend long
- prezzo torna su EMA/supporto
- RSI scarica ma non crolla
- prezzo reagisce o riparte
- stop tecnico chiaro
- target realistici

SHORT:
- trend short
- prezzo torna su EMA/resistenza
- RSI rimbalza ma non diventa forte
- prezzo respinge e riparte giù
- stop tecnico chiaro
- target realistici

SETUP 2: BREAKOUT + RETEST
LONG:
- rottura resistenza o massimo
- retest della zona rotta
- zona tiene
- ripartenza long

SHORT:
- rottura supporto o minimo
- retest della zona rotta
- zona respinge
- ripartenza short

Se non vedi PULLBACK IN TREND o BREAKOUT + RETEST:
NO TRADE.

FASE 3: QUALITÀ SETUP

A+:
- trend chiaro
- setup chiaro
- prezzo in zona buona
- momentum coerente
- RR valido
- livelli numerici leggibili
Decisione possibile: ENTRA SUBITO o ORDINE PENDENTE.

B:
- direzione probabile
- serve ancora pullback o conferma
- livelli leggibili
Decisione possibile: solo ORDINE PENDENTE.

C:
- trend confuso
- prezzo in mezzo
- range sporco
- setup non chiaro
- RR scarso
Decisione: NO TRADE.

FASE 4: TIPO ORDINE

MARKET BUY:
solo setup A+ long, prezzo già in zona buona.

MARKET SELL:
solo setup A+ short, prezzo già in zona buona.

BUY LIMIT:
trend long, vuoi comprare su pullback.

SELL LIMIT:
trend short, vuoi vendere su pullback.

BUY STOP:
serve rottura sopra resistenza/massimo.

SELL STOP:
serve rottura sotto supporto/minimo.

NESSUN ORDINE:
nessun setup valido.

FASE 5: FILTRI DURI

Se confidence sotto 60:
NO TRADE.

Se trade score sotto 65:
NO TRADE.

Se setup quality è C:
NO TRADE.

Se non puoi dare entry, stop loss, invalidazione, TP1, TP2, TP3 numerici:
NO TRADE.

Se setup quality è B:
non usare MARKET BUY o MARKET SELL.
Usa solo ordine pendente.

==================================================
GESTIONE TRADE
==================================================

Se dai LONG o SHORT devi dare:
- Entry numerica
- Stop Loss numerico
- Invalidazione numerica
- TP1 numerico
- TP2 numerico
- TP3 numerico
- Risk Reward
- Parziale
- Breakeven
- Trailing

TP1 = target prudente.
TP2 = target principale.
TP3 = estensione.

A TP1 suggerisci parziale 40% o 50%.
Dopo TP1 suggerisci breakeven.
Dopo TP2 suggerisci trailing.

==================================================
FORMATO RISPOSTA
==================================================

Rispondi SOLO con righe KEY=VALUE.
Non usare JSON.
Non usare markdown.
Non usare punti elenco.
Non aggiungere testo fuori dalle righe.
Ogni campo deve stare su una sola riga.
Non andare a capo dentro ANALISI.
Non usare il simbolo = dentro i valori.

Usa ESATTAMENTE questi campi:

VERDETTO=LONG oppure SHORT oppure NO TRADE
BIAS=LONG oppure SHORT oppure NEUTRO
SETUP_QUALITY=A+ oppure B oppure C
SETUP_TYPE=PULLBACK oppure BREAKOUT_RETEST oppure NESSUN SETUP
TIPO_ORDINE=MARKET BUY oppure MARKET SELL oppure BUY LIMIT oppure SELL LIMIT oppure BUY STOP oppure SELL STOP oppure NESSUN ORDINE
ENTRY=prezzo o N/D
STOP_LOSS=prezzo o N/D
INVALIDAZIONE=prezzo o N/D
TP1=prezzo o N/D
TP2=prezzo o N/D
TP3=prezzo o N/D
RISK_REWARD=rapporto o N/D
CONFIDENCE=numero da 0 a 100
TRADE_SCORE=numero da 0 a 100
DECISIONE=ENTRA SUBITO oppure ORDINE PENDENTE oppure NON OPERARE
PARZIALE=regola o N/D
BREAKEVEN=regola o N/D
TRAILING=regola o N/D
ANALISI=frase breve massimo 240 caratteri
MOTIVO_NO_TRADE=frase breve o vuoto
"""

# =========================
# GEMINI
# =========================

def call_gemini(prompt, img):
    response = model.generate_content(
        [prompt, img],
        generation_config={
            "temperature": 0.10,
            "top_p": 0.75,
            "top_k": 20,
            "max_output_tokens": 1200
        }
    )

    if not response or not hasattr(response, "text"):
        raise RuntimeError("Gemini non ha restituito testo.")

    return response.text


def repair_prompt(previous_text, symbol, timeframe, profile):
    return f"""
La risposta precedente non rispetta il formato KEY=VALUE.

Correggi.

Regole:
Rispondi SOLO con righe KEY=VALUE.
Non usare JSON.
Non usare markdown.
Ogni campo una sola riga.
Se non sei sicuro, metti NO TRADE.
Se LONG o SHORT mancano numeri, metti NO TRADE.

Strumento: {symbol}
Timeframe: {timeframe}
Profilo: {profile}

Risposta precedente:
{previous_text}

Campi obbligatori:

VERDETTO=NO TRADE
BIAS=NEUTRO
SETUP_QUALITY=C
SETUP_TYPE=NESSUN SETUP
TIPO_ORDINE=NESSUN ORDINE
ENTRY=N/D
STOP_LOSS=N/D
INVALIDAZIONE=N/D
TP1=N/D
TP2=N/D
TP3=N/D
RISK_REWARD=N/D
CONFIDENCE=0
TRADE_SCORE=0
DECISIONE=NON OPERARE
PARZIALE=N/D
BREAKEVEN=N/D
TRAILING=N/D
ANALISI=Risposta precedente non valida. Segnale annullato per sicurezza.
MOTIVO_NO_TRADE=Formato non valido o setup non chiaro.
"""


def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode,
                  profile, rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):
    try:
        img = Image.open(image_file)

        prompt = build_prompt(
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            profile,
            rr_minimo,
            multi_tf,
            show_ema,
            show_rsi,
            show_levels,
            show_volume
        )

        first_text = call_gemini(prompt, img)
        data = parse_key_value_response(first_text)

        required_keys = list(default_result().keys())
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            repair_text = call_gemini(repair_prompt(first_text, symbol, timeframe, profile), img)
            data = parse_key_value_response(repair_text)

        if not valid_trade(data):
            if data.get("VERDETTO") in ["LONG", "SHORT"]:
                repair_text = call_gemini(repair_prompt(result_to_text(data), symbol, timeframe, profile), img)
                repaired = parse_key_value_response(repair_text)

                if valid_trade(repaired):
                    return result_to_text(repaired)

                data = force_no_trade(
                    "Segnale bloccato. Non ha superato i filtri della ProTrade Fixed Strategy."
                )

        return result_to_text(data)

    except Exception as e:
        data = force_no_trade(
            f"Errore tecnico durante analisi. Segnale annullato per sicurezza. Dettaglio: {e}"
        )
        return result_to_text(data)


def save_history(mode, symbol, timeframe, result):
    st.session_state.history.append({
        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "mode": mode,
        "symbol": symbol,
        "timeframe": timeframe,
        "result": result
    })

# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.markdown("### ⚡ Modalità AI")

    profiles = ["Challenge", "Standard", "Funded", "Scalping"]

    st.session_state.profile = st.radio(
        "Profilo",
        profiles,
        index=profiles.index(st.session_state.profile)
    )

    st.markdown("---")

    symbol = st.selectbox(
        "Strumento",
        ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"]
    )

    timeframe = st.selectbox(
        "Timeframe",
        ["M1", "M5", "M15", "M30", "H1", "H4"]
    )

    multi_tf = st.toggle("Multi-Timeframe", value=True)

    st.markdown("---")

    account_size = st.number_input(
        "Account USD",
        min_value=1000,
        value=25000,
        step=1000
    )

    risk_percent = st.number_input(
        "Rischio %",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1
    )

    rr_minimo = st.selectbox(
        "RR minimo",
        ["1:1.5", "1:1.8", "1:2.0", "1:2.5", "1:3.0"],
        index=2
    )

    prop_mode = st.selectbox(
        "Prop Firm",
        ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"]
    )

    st.markdown("---")

    show_ema = st.toggle("Leggi EMA / Media", value=True)
    show_rsi = st.toggle("Leggi RSI", value=True)
    show_levels = st.toggle("Leggi Supporti/Resistenze", value=True)
    show_volume = st.toggle("Leggi Volumi", value=False)

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Carica screenshot grafico",
        type=["jpg", "jpeg", "png"]
    )

    analyze_clicked = st.button("⚡ ANALIZZA GRAFICO")

# =========================
# HEADER
# =========================

now = datetime.now()

st.markdown(f"""
<div class="header">
    <div class="brand">⚡ ProTrade AI</div>
    <div class="sub">Fixed Strategy · stesso ragionamento sempre · {now.strftime('%d/%m/%Y %H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# CHART
# =========================

st.markdown(f"""
<div class="card">
    <h3>{symbol} · {timeframe}</h3>
    <div class="small">Strategia fissa: Trend → Pullback/Retest → Filtro → Segnale o No Trade.</div>
</div>
""", unsafe_allow_html=True)

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
else:
    st.info("Carica uno screenshot dalla sidebar.")

# =========================
# RUN
# =========================

if analyze_clicked and uploaded_file:
    with st.spinner("Analisi in corso..."):
        result = analyze_chart(
            uploaded_file,
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            st.session_state.profile,
            rr_minimo,
            multi_tf,
            show_ema,
            show_rsi,
            show_levels,
            show_volume
        )

        st.session_state.last_result = result
        st.session_state.last_update = datetime.now().strftime("%H:%M:%S")

        save_history(
            st.session_state.profile,
            symbol,
            timeframe,
            result
        )

elif analyze_clicked and not uploaded_file:
    st.warning("Carica prima uno screenshot.")

# =========================
# OUTPUT
# =========================

if st.session_state.last_result:
    data = parse_key_value_response(st.session_state.last_result)

    verdict = data["VERDETTO"]
    css_class, color, icon = signal_style(verdict)

    st.markdown(f"""
    <div class="signal {css_class}">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div class="signal-title" style="color:{color};">{icon} {verdict}</div>
                <div class="small">
                    {data["TIPO_ORDINE"]} · {data["DECISIONE"]} · Setup {data["SETUP_QUALITY"]} · Confidence {data["CONFIDENCE"]}%
                </div>
            </div>
            <div style="text-align:right;">
                <div class="small">Setup Type</div>
                <div style="font-weight:900;font-size:16px;">{data["SETUP_TYPE"]}</div>
                <div class="small">Score {data["TRADE_SCORE"]}/100</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">ENTRY</div>
            <div class="metric-value" style="color:#00E676;">{data["ENTRY"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">STOP LOSS</div>
            <div class="metric-value" style="color:#FF5252;">{data["STOP_LOSS"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">TP1</div>
            <div class="metric-value" style="color:#4FC3F7;">{data["TP1"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">RISK / REWARD</div>
            <div class="metric-value" style="color:#FFD54F;">{data["RISK_REWARD"]}</div>
        </div>
        """, unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">INVALIDAZIONE</div>
            <div class="metric-value" style="color:#FFB74D;">{data["INVALIDAZIONE"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">TP2</div>
            <div class="metric-value" style="color:#4FC3F7;">{data["TP2"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c7:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">TP3</div>
            <div class="metric-value" style="color:#4FC3F7;">{data["TP3"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c8:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">SESSIONE</div>
            <div class="metric-value">{get_session()}</div>
        </div>
        """, unsafe_allow_html=True)

    left, middle, right = st.columns([1, 1, 1.4])

    with left:
        st.markdown('<div class="card"><h4>Gestione</h4>', unsafe_allow_html=True)
        st.write(f"**Parziale:** {data['PARZIALE']}")
        st.write(f"**Breakeven:** {data['BREAKEVEN']}")
        st.write(f"**Trailing:** {data['TRAILING']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with middle:
        st.markdown('<div class="card"><h4>Filtro</h4>', unsafe_allow_html=True)
        st.write(f"**Bias:** {data['BIAS']}")
        st.write(f"**Setup Quality:** {data['SETUP_QUALITY']}")
        st.write(f"**Tipo ordine:** {data['TIPO_ORDINE']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><h4>Analisi</h4>', unsafe_allow_html=True)
        st.write(data["ANALISI"])

        if data["VERDETTO"] == "NO TRADE":
            st.warning(data["MOTIVO_NO_TRADE"])

        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Risposta completa KEY=VALUE"):
        st.code(st.session_state.last_result, language="text")

# =========================
# HISTORY
# =========================

if st.session_state.history:
    st.markdown("---")
    st.markdown("## Storico")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(f"{item['time']} · {item['mode']} · {item['symbol']} {item['timeframe']}"):
            st.code(item["result"], language="text")

st.markdown("---")
st.caption("⚠️ ProTrade AI è uno strumento di supporto. Non è consulenza finanziaria. Usa sempre gestione del rischio.")

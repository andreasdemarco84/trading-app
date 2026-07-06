import streamlit as st
from PIL import Image
import google.generativeai as genai
import re
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
# SESSION STATE DEFAULTS
# =========================

if "ai_profile" not in st.session_state:
    st.session_state.ai_profile = "Standard"

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_update" not in st.session_state:
    st.session_state.last_update = None

# =========================
# CSS
# =========================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top right, #14210a 0%, #0E1117 35%, #05070A 100%);
    color: white;
}

section[data-testid="stSidebar"] {
    background: #0A0D12;
    border-right: 1px solid rgba(255,255,255,0.06);
}

.top-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 22px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(0,200,83,0.10), rgba(15,23,42,0.92));
    border: 1px solid rgba(0,230,118,0.25);
    margin-bottom: 20px;
}

.brand {
    font-size: 30px;
    font-weight: 900;
    color: white;
}

.subbrand {
    font-size: 14px;
    color: #9AE6B4;
    margin-top: -4px;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(0,200,83,0.15);
    color: #00E676;
    border: 1px solid #00C853;
    font-weight: 700;
    font-size: 13px;
}

.section-label {
    color: #8B98A9;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    margin: 14px 0 8px 0;
}

.mode-card {
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
}

.mode-card.active-challenge {
    border: 1px solid #FFC107;
    background: rgba(255,193,7,0.12);
    box-shadow: 0 0 18px rgba(255,193,7,0.15);
}

.mode-card.active-standard {
    border: 1px solid #4FC3F7;
    background: rgba(79,195,247,0.12);
    box-shadow: 0 0 18px rgba(79,195,247,0.15);
}

.mode-card.active-funded {
    border: 1px solid #00E676;
    background: rgba(0,230,118,0.12);
    box-shadow: 0 0 18px rgba(0,230,118,0.15);
}

.mode-card.active-scalping {
    border: 1px solid #CE93D8;
    background: rgba(206,147,216,0.12);
    box-shadow: 0 0 18px rgba(206,147,216,0.15);
}

.mode-title {
    font-weight: 800;
    font-size: 14px;
}

.mode-desc {
    font-size: 12px;
    color: #A0AEC0;
    margin-top: 2px;
}

.chart-panel {
    border-radius: 20px;
    background: rgba(10,14,22,0.9);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 16px;
    margin-bottom: 16px;
}

.chart-panel-title {
    font-size: 18px;
    font-weight: 800;
    color: white;
}

.chart-panel-sub {
    font-size: 13px;
    color: #8B98A9;
    margin-bottom: 10px;
}

.signal-card {
    border-radius: 22px;
    padding: 26px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.signal-long {
    background: rgba(0,50,25,0.55);
    border: 2px solid #00C853;
    box-shadow: 0 0 26px rgba(0,200,83,0.20);
}

.signal-short {
    background: rgba(60,10,10,0.55);
    border: 2px solid #FF5252;
    box-shadow: 0 0 26px rgba(255,82,82,0.20);
}

.signal-wait {
    background: rgba(40,40,10,0.5);
    border: 2px solid #FFD54F;
    box-shadow: 0 0 26px rgba(255,213,79,0.15);
}

.signal-no {
    background: rgba(30,30,30,0.5);
    border: 2px solid #9E9E9E;
}

.signal-verdict {
    font-size: 46px;
    font-weight: 900;
    line-height: 1;
}

.signal-confidence {
    font-size: 14px;
    color: #C9D6E3;
    margin-top: 6px;
}

.metric-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    text-align: center;
    margin-bottom: 10px;
}

.metric-title {
    color: #A0AEC0;
    font-size: 12px;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 22px;
    font-weight: 800;
    margin-top: 4px;
}

.info-panel {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    height: 100%;
}

.info-panel-title {
    font-size: 13px;
    font-weight: 800;
    color: #E2E8F0;
    margin-bottom: 10px;
}

.checklist-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    padding: 5px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.bottom-bar {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin-top: 16px;
}

.bottom-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 12px;
    text-align: center;
}

.bottom-stat-title {
    color: #8B98A9;
    font-size: 11px;
    letter-spacing: 0.5px;
}

.bottom-stat-value {
    font-size: 15px;
    font-weight: 800;
    margin-top: 4px;
}

.stButton>button {
    width: 100%;
    border-radius: 12px;
    background: rgba(255,255,255,0.06);
    color: white;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.1);
}

div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.04);
    border-radius: 16px;
    padding: 10px;
}

h1, h2, h3, label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# PROMPT BUILDER
# =========================

def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile,
                 rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):

    risk_dollar = account_size * risk_percent / 100

    if ai_profile == "Challenge":
        profile_rule = """
Profilo Challenge:
- Obiettivo primario: trovare opportunità operative valide.
- Accetta setup buoni anche se non perfetti.
- Se trend e struttura sono chiari, puoi dare LONG o SHORT.
- Usa ASPETTA solo se manca una conferma precisa.
- Usa NO TRADE solo se grafico sporco, laterale o rischio/rendimento scarso.
"""
    elif ai_profile == "Funded":
        profile_rule = """
Profilo Funded:
- Obiettivo primario: proteggere il conto.
- Sii più selettivo, ma non bloccato.
- Dai LONG o SHORT solo se trend, struttura, RSI e RR sono abbastanza coerenti.
- Evita ingressi tardivi e trade forzati.
- Usa ASPETTA se serve conferma.
"""
    elif ai_profile == "Scalping":
        profile_rule = """
Profilo Scalping:
- Obiettivo primario: operatività rapida su M1/M5.
- Puoi dare LONG o SHORT se ci sono momentum, timing e struttura leggibile.
- Non inseguire il prezzo se è già partito.
- Evita trade solo se movimento esaurito, spike o rumore eccessivo.
"""
    else:
        profile_rule = """
Profilo Standard:
- Approccio bilanciato.
- Dai LONG o SHORT se il setup è tecnicamente valido.
- Usa ASPETTA se la direzione è buona ma manca timing.
- Usa NO TRADE se mercato confuso o RR insufficiente.
"""

    focus_lines = []
    if show_ema:
        focus_lines.append("- Commenta la posizione del prezzo rispetto a EMA/media mobile se visibile.")
    if show_rsi:
        focus_lines.append("- Commenta obbligatoriamente il valore RSI se visibile.")
    if show_levels:
        focus_lines.append("- Commenta supporti e resistenze visibili.")
    if show_volume:
        focus_lines.append("- Commenta i volumi se visibili nello screenshot.")

    focus_block = "\n".join(focus_lines) if focus_lines else "- Analizza tutti gli elementi visibili nel grafico."

    mtf_block = ""
    if multi_tf:
        mtf_block = """
Considera anche l'ottica multi-timeframe:
- timeframe alto = direzione
- timeframe medio = setup
- timeframe basso = timing
Se dallo screenshot non puoi vedere tutto, dillo chiaramente.
"""

    return f"""
Sei ProTrade AI, assistente professionale di analisi trading creato per Andreas De Marco.

Analizza il grafico caricato come un trader umano esperto.
Non dare segnali ciechi.
Non inventare dati non visibili.
Devi ragionare bene, non sparare a caso.

DATI OPERATIVI:
Strumento: {symbol}
Timeframe: {timeframe}
Account: {account_size} USD
Rischio massimo: {risk_percent}%
Rischio massimo in dollari: {risk_dollar:.2f} USD
Modalità prop firm: {prop_mode}
Profilo AI: {ai_profile}
RR minimo richiesto: {rr_minimo}

{mtf_block}

{profile_rule}

FOCUS RICHIESTI:
{focus_block}

REGOLE IMPORTANTI:
- LONG/SHORT se il setup ha una logica tecnica concreta.
- ASPETTA se manca conferma, candela, pullback o timing.
- NO TRADE solo se il mercato è laterale, sporco, confuso, con spike o RR insufficiente.
- Non usare ASPETTA sempre.
- Non usare LONG/SHORT senza motivazione tecnica.
- Controlla RSI: se RSI è già molto basso, attenzione agli SHORT tardivi; se RSI è molto alto, attenzione ai LONG tardivi.
- Se RSI è 40-60, è neutro.
- Controlla media mobile/EMA se visibile.
- Controlla se il prezzo è troppo lontano dalla media.
- Controlla se l'ingresso è tardivo.
- Controlla il rapporto rischio/rendimento.
- Se scegli ASPETTA, devi dire esattamente cosa aspettare.

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
Trend principale: ...
Struttura: ...
Momentum: ...
Volatilità: Bassa/Media/Alta

RSI CHECK:
Valore stimato: ...
Condizione: ...
Conferma o blocca il trade: ...
Nota: ...

TRADE SETUP:
Entry: ...
Stop Loss: ...
TP1: ...
TP2: ...
TP3: ...
Risk/Reward: ...

RISK MANAGER:
Rischio massimo: ...
Size consigliata: ...
Breakeven: ...
Parziale: ...

AI CHECKLIST:
Trend: ...
EMA: ...
RSI: ...
Momentum: ...
Struttura: ...
Risk/Reward: ...

MOTIVAZIONE:
Spiegazione pratica in 3-5 frasi.

INVALIDAZIONE:
Quando il setup non è più valido.

DECISIONE OPERATIVA:
ENTRA / ASPETTA / NON OPERARE
"""

# =========================
# PARSER
# =========================

SECTION_HEADERS = [
    "VERDETTO", "TIPO SEGNALE", "TRADE SCORE", "CONFIDENCE", "MARKET BIAS",
    "RSI CHECK", "TRADE SETUP", "RISK MANAGER", "AI CHECKLIST",
    "MOTIVAZIONE", "INVALIDAZIONE", "DECISIONE OPERATIVA"
]

SIMPLE_SECTIONS = [
    "VERDETTO", "TIPO SEGNALE", "TRADE SCORE", "CONFIDENCE", "DECISIONE OPERATIVA"
]

FREETEXT_SECTIONS = ["MOTIVAZIONE", "INVALIDAZIONE"]

KEYVALUE_SECTIONS = [
    "MARKET BIAS", "RSI CHECK", "TRADE SETUP", "RISK MANAGER", "AI CHECKLIST"
]


def parse_ai_response(text):
    pattern = r"(?im)^(" + "|".join(SECTION_HEADERS) + r"):\s*$"
    parts = re.split(pattern, text)

    blocks = {}
    i = 1
    while i < len(parts) - 1:
        header = parts[i].strip().upper()
        content = parts[i + 1].strip()
        blocks[header] = content
        i += 2

    parsed = {}

    for h in SIMPLE_SECTIONS:
        content = blocks.get(h, "")
        first_line = content.splitlines()[0].strip() if content else ""
        parsed[h] = first_line

    for h in FREETEXT_SECTIONS:
        parsed[h] = blocks.get(h, "").strip()

    for h in KEYVALUE_SECTIONS:
        kv = {}
        content = blocks.get(h, "")
        for line in content.splitlines():
            m = re.match(r"^\s*([^:]{2,40}):\s*(.+)$", line)
            if m:
                key = m.group(1).strip().lower()
                val = m.group(2).strip()
                kv[key] = val
        parsed[h] = kv

    return parsed


def get_rsi_value(rsi_dict):
    raw = rsi_dict.get("valore stimato", "")
    m = re.search(r"(\d+(\.\d+)?)", raw)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return 50.0
    return 50.0


def verdict_style(verdetto):
    v = verdetto.upper()
    if "LONG" in v or "BUY" in v:
        return "signal-long", "#00E676", "🐂"
    if "SHORT" in v or "SELL" in v:
        return "signal-short", "#FF5252", "🐻"
    if "ASPETTA" in v:
        return "signal-wait", "#FFD54F", "⏸️"
    return "signal-no", "#9E9E9E", "⛔"


def bars(level, max_level=5, color="🟩", empty="⬜"):
    try:
        level = int(round(level))
    except Exception:
        level = 0
    level = max(0, min(max_level, level))
    return color * level + empty * (max_level - level)


def volatility_level(vol_text):
    t = str(vol_text).lower()
    if "molto alta" in t or "estrema" in t:
        return 5
    if "alta" in t:
        return 4
    if "media" in t:
        return 3
    if "bassa" in t:
        return 2
    return 1


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
# IMAGE / GEMINI
# =========================

def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode,
                  ai_profile, rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):
    try:
        img = Image.open(image_file)

        prompt = build_prompt(
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            ai_profile,
            rr_minimo,
            multi_tf,
            show_ema,
            show_rsi,
            show_levels,
            show_volume
        )

        response = model.generate_content([prompt, img])
        return response.text

    except Exception as e:
        return f"ERRORE: {str(e)}"


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
    st.markdown('<div class="section-label">MODALITÀ AI</div>', unsafe_allow_html=True)

    modes = [
        ("Challenge", "🏆", "CHALLENGE", "Più opportunità · RR min 1:1.5", "active-challenge"),
        ("Standard", "📊", "STANDARD", "Equilibrato · RR min 1:2", "active-standard"),
        ("Funded", "🛡️", "FUNDED", "Massima selettività · RR min 1:2", "active-funded"),
        ("Scalping", "⚡", "SCALPING", "Ingressi rapidi · M1-M5", "active-scalping"),
    ]

    for key, icon, title, desc, active_class in modes:
        is_active = st.session_state.ai_profile == key
        css_class = f"mode-card {active_class}" if is_active else "mode-card"

        st.markdown(f"""
        <div class="{css_class}">
            <div class="mode-title">{icon} {title}</div>
            <div class="mode-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Seleziona {title}", key=f"btn_{key}", use_container_width=True):
            st.session_state.ai_profile = key
            st.rerun()

    st.markdown('<div class="section-label">ASSET E TIMEFRAME</div>', unsafe_allow_html=True)
    symbol = st.selectbox("Strumento", ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"])
    timeframe = st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4"])
    multi_tf = st.toggle("Analisi Multi-Timeframe", value=True)

    st.markdown('<div class="section-label">IMPOSTAZIONI RISCHIO</div>', unsafe_allow_html=True)
    account_size = st.number_input("Account USD", min_value=1000, value=25000, step=1000)
    risk_percent = st.number_input("Rischio %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    risk_dollar = account_size * risk_percent / 100
    st.caption(f"Rischio $: {risk_dollar:,.2f} USD")

    rr_minimo = st.selectbox("RR Minimo", ["1:1.5", "1:2.0", "1:2.5", "1:3.0"], index=1)
    prop_mode = st.selectbox("Prop Firm", ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"])

    st.markdown('<div class="section-label">PREFERENZE DISPLAY</div>', unsafe_allow_html=True)
    show_ema = st.toggle("Mostra EMA", value=True)
    show_rsi = st.toggle("Mostra RSI", value=True)
    show_levels = st.toggle("Mostra Livelli", value=True)
    show_volume = st.toggle("Mostra Volumi", value=False)

    st.markdown('<div class="section-label">CARICA GRAFICO</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "JPG, PNG",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    analyze_clicked = st.button("⚡ CARICA GRAFICO E ANALIZZA", use_container_width=True)

# =========================
# TOP HEADER
# =========================

now = datetime.now()

st.markdown(f"""
<div class="top-header">
    <div>
        <div class="brand">⚡ ProTrade AI</div>
        <div class="subbrand">by Andreas De Marco</div>
    </div>
    <div style="text-align:right;">
        <div class="live-badge">🟢 LIVE ANALYSIS</div>
        <div style="color:#8B98A9; font-size:12px; margin-top:6px;">
            {now.strftime('%H:%M:%S')} ORA · {now.strftime('%d/%m/%Y')} DATA
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# CHART PANEL
# =========================

st.markdown(f"""
<div class="chart-panel">
    <div class="chart-panel-title">{symbol} · {timeframe}</div>
    <div class="chart-panel-sub">Screenshot caricato dall'utente per analisi AI</div>
""", unsafe_allow_html=True)

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
else:
    st.info("Carica uno screenshot del grafico dalla sidebar per iniziare l'analisi.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RUN ANALYSIS
# =========================

if analyze_clicked and uploaded_file:
    with st.spinner("ProTrade AI sta analizzando il mercato..."):
        result = analyze_chart(
            uploaded_file,
            symbol,
            timeframe,
            account_size,
            risk_percent,
            prop_mode,
            st.session_state.ai_profile,
            rr_minimo,
            multi_tf,
            show_ema,
            show_rsi,
            show_levels,
            show_volume
        )

        st.session_state.last_result = result
        st.session_state.last_update = datetime.now().strftime("%H:%M:%S")
        save_history(st.session_state.ai_profile, symbol, timeframe, result)

elif analyze_clicked and not uploaded_file:
    st.warning("Carica prima uno screenshot del grafico.")

# =========================
# RESULTS
# =========================

if st.session_state.last_result:
    result = st.session_state.last_result

    if result.startswith("ERRORE"):
        st.error(result)
    else:
        parsed = parse_ai_response(result)

        verdetto = parsed.get("VERDETTO", "N/D") or "N/D"
        tipo_segnale = parsed.get("TIPO SEGNALE", "N/D") or "N/D"
        trade_score_raw = parsed.get("TRADE SCORE", "0") or "0"
        confidence_raw = parsed.get("CONFIDENCE", "0%") or "0%"

        market_bias = parsed.get("MARKET BIAS", {})
        rsi_check = parsed.get("RSI CHECK", {})
        trade_setup = parsed.get("TRADE SETUP", {})
        checklist = parsed.get("AI CHECKLIST", {})
        motivazione = parsed.get("MOTIVAZIONE", "N/D")
        invalidazione = parsed.get("INVALIDAZIONE", "N/D")
        decisione = parsed.get("DECISIONE OPERATIVA", "N/D")

        css_class, accent_color, icon = verdict_style(verdetto)

        score_num_match = re.search(r"(\d+)", str(trade_score_raw))
        score_num = int(score_num_match.group(1)) if score_num_match else 0

        conf_num_match = re.search(r"(\d+)", str(confidence_raw))
        conf_num = int(conf_num_match.group(1)) if conf_num_match else 0

        st.markdown(f"""
        <div class="signal-card {css_class}">
            <div style="display:flex; align-items:center; gap:20px;">
                <div style="font-size:44px;">{icon}</div>
                <div>
                    <div class="signal-verdict" style="color:{accent_color};">{verdetto}</div>
                    <div class="signal-confidence">CONFIDENCE {conf_num}%</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#8B98A9; font-size:12px;">TIPO SEGNALE</div>
                <div style="font-weight:800; font-size:16px;">{tipo_segnale}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">ENTRY</div>
                <div class="metric-value" style="color:#00E676;">{trade_setup.get('entry', 'N/D')}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">STOP LOSS</div>
                <div class="metric-value" style="color:#FF5252;">{trade_setup.get('stop loss', 'N/D')}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">TAKE PROFIT</div>
                <div class="metric-value" style="color:#4FC3F7;">{trade_setup.get('tp1', 'N/D')}</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">RISK / REWARD</div>
                <div class="metric-value" style="color:#FFD166;">{trade_setup.get('risk/reward', 'N/D')}</div>
            </div>
            """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns([1.3, 1, 1.3])

        with col_a:
            rows = ""
            labels_map = [
                ("trend", "Trend"),
                ("ema", "EMA"),
                ("rsi", "RSI"),
                ("momentum", "Momentum"),
                ("struttura", "Struttura"),
                ("risk/reward", "Risk/Reward")
            ]

            for key, label in labels_map:
                if key == "ema" and not show_ema:
                    continue
                if key == "rsi" and not show_rsi:
                    continue

                value = checklist.get(key, "—")
                rows += f'<div class="checklist-row"><span>{label}</span><span>✅ {value}</span></div>'

            st.markdown(f"""
            <div class="info-panel">
                <div class="info-panel-title">⚠️ ANALISI TECNICA</div>
                {rows}
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            rsi_val = get_rsi_value(rsi_check)
            rsi_condizione = rsi_check.get("condizione", "N/D")
            rsi_conferma = rsi_check.get("conferma o blocca il trade", "N/D")

            st.markdown(f"""
            <div class="info-panel" style="text-align:center;">
                <div class="info-panel-title">RSI CHECK</div>
                <div style="font-size:32px; font-weight:900; color:#00E676; margin-top:8px;">
                    {rsi_val:.1f}
                </div>
                <div style="font-size:12px; color:#8B98A9;">{rsi_condizione}</div>
                <div style="margin-top:10px; font-size:12px; color:#C9D6E3;">{rsi_conferma}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            st.markdown(f"""
            <div class="info-panel">
                <div class="info-panel-title">💬 SPIEGAZIONE AI</div>
                <div style="font-size:13px; line-height:1.6; color:#E2E8F0;">
                    {motivazione}
                    <br><br>
                    <b>Invalidazione:</b><br>
                    {invalidazione}
                    <br><br>
                    <b>Decisione:</b> {decisione}
                </div>
            </div>
            """, unsafe_allow_html=True)

        vol_text = market_bias.get("volatilità", "Media")
        vol_lvl = volatility_level(vol_text)
        session = get_session()
        last_update = st.session_state.last_update or "--:--:--"

        st.markdown(f"""
        <div class="bottom-bar">
            <div class="bottom-stat">
                <div class="bottom-stat-title">PROBABILITÀ</div>
                <div class="bottom-stat-value" style="color:#00E676;">{conf_num}%</div>
            </div>
            <div class="bottom-stat">
                <div class="bottom-stat-title">FORZA TREND</div>
                <div class="bottom-stat-value">{bars(round(score_num / 20), color="🟩")}</div>
            </div>
            <div class="bottom-stat">
                <div class="bottom-stat-title">VOLATILITÀ</div>
                <div class="bottom-stat-value">{bars(vol_lvl, color="🟧")}</div>
            </div>
            <div class="bottom-stat">
                <div class="bottom-stat-title">SESSIONE</div>
                <div class="bottom-stat-value">{session}</div>
            </div>
            <div class="bottom-stat">
                <div class="bottom-stat-title">NEWS FILTER</div>
                <div class="bottom-stat-value" style="font-size:12px;">N/D locale</div>
            </div>
            <div class="bottom-stat">
                <div class="bottom-stat-title">ULTIMO UPDATE</div>
                <div class="bottom-stat-value" style="font-size:13px;">{last_update}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================
# HISTORY
# =========================

if st.session_state.history:
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

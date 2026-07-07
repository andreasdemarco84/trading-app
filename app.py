import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import re
from datetime import datetime

st.set_page_config(page_title="ProTrade AI", page_icon="⚡", layout="wide")

genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

if "ai_profile" not in st.session_state:
    st.session_state.ai_profile = "Standard"
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top right,#12210d 0%,#0E1117 38%,#05070A 100%);
    color:white;
}

section[data-testid="stSidebar"] {
    background:#0A0D12;
    border-right:1px solid rgba(255,255,255,.08);
}

h1,h2,h3,h4,label {
    color:white!important;
}

.top-header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:18px 22px;
    border-radius:20px;
    background:linear-gradient(135deg,rgba(0,200,83,.12),rgba(15,23,42,.95));
    border:1px solid rgba(0,230,118,.25);
    margin-bottom:20px;
}

.brand {
    font-size:30px;
    font-weight:900;
    color:white;
}

.subbrand {
    font-size:14px;
    color:#9AE6B4;
}

.live-badge {
    padding:6px 14px;
    border-radius:999px;
    background:rgba(0,200,83,.15);
    color:#00E676;
    border:1px solid #00C853;
    font-weight:800;
    font-size:13px;
}

.section-label {
    color:#8B98A9;
    font-size:12px;
    font-weight:800;
    letter-spacing:1px;
    margin:14px 0 8px 0;
}

.mode-card {
    border-radius:16px;
    padding:14px 16px;
    margin-bottom:8px;
    border:1px solid rgba(255,255,255,.08);
    background:rgba(255,255,255,.03);
}

.mode-card-active {
    border:1px solid #FFD54F;
    background:rgba(255,213,79,.12);
    box-shadow:0 0 18px rgba(255,213,79,.16);
}

.mode-title {
    font-weight:800;
    font-size:14px;
}

.mode-desc {
    font-size:12px;
    color:#A0AEC0;
    margin-top:2px;
}

.chart-panel {
    border-radius:20px;
    background:rgba(10,14,22,.92);
    border:1px solid rgba(255,255,255,.08);
    padding:16px;
    margin-bottom:16px;
}

.chart-panel-title {
    font-size:18px;
    font-weight:800;
}

.chart-panel-sub {
    font-size:13px;
    color:#8B98A9;
    margin-bottom:10px;
}

.signal-card {
    border-radius:22px;
    padding:26px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:16px;
}

.signal-long {
    background:rgba(0,50,25,.58);
    border:2px solid #00C853;
    box-shadow:0 0 26px rgba(0,200,83,.20);
}

.signal-short {
    background:rgba(60,10,10,.58);
    border:2px solid #FF5252;
    box-shadow:0 0 26px rgba(255,82,82,.20);
}

.signal-no {
    background:rgba(35,35,35,.62);
    border:2px solid #9E9E9E;
}

.signal-verdict {
    font-size:44px;
    font-weight:900;
    line-height:1;
}

.signal-confidence {
    font-size:14px;
    color:#C9D6E3;
    margin-top:8px;
}

.metric-box {
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.08);
    border-radius:18px;
    padding:16px;
    text-align:center;
    margin-bottom:10px;
    min-height:110px;
}

.metric-title {
    color:#A0AEC0;
    font-size:12px;
    letter-spacing:.5px;
}

.metric-value {
    font-size:20px;
    font-weight:800;
    margin-top:8px;
    word-break:break-word;
}

.info-panel {
    background:rgba(255,255,255,.035);
    border:1px solid rgba(255,255,255,.08);
    border-radius:18px;
    padding:16px;
    height:100%;
}

.info-panel-title {
    font-size:13px;
    font-weight:800;
    color:#E2E8F0;
    margin-bottom:10px;
}

.checklist-row {
    display:flex;
    justify-content:space-between;
    gap:8px;
    font-size:13px;
    padding:7px 0;
    border-bottom:1px solid rgba(255,255,255,.05);
}

.bottom-bar {
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:10px;
    margin-top:16px;
}

.bottom-stat {
    background:rgba(255,255,255,.035);
    border:1px solid rgba(255,255,255,.07);
    border-radius:14px;
    padding:12px;
    text-align:center;
}

.bottom-stat-title {
    color:#8B98A9;
    font-size:11px;
    letter-spacing:.5px;
}

.bottom-stat-value {
    font-size:15px;
    font-weight:800;
    margin-top:4px;
}

.stButton>button {
    width:100%;
    border-radius:12px;
    background:rgba(255,255,255,.06);
    color:white;
    font-weight:700;
    border:1px solid rgba(255,255,255,.12);
}

div[data-testid="stFileUploader"] {
    background:rgba(255,255,255,.04);
    border-radius:16px;
    padding:10px;
}

@media(max-width:900px) {
    .bottom-bar {
        grid-template-columns:repeat(2,1fr);
    }
    .signal-verdict {
        font-size:34px;
    }
}
</style>
""", unsafe_allow_html=True)


def build_prompt(symbol, timeframe, account_size, risk_percent, prop_mode, ai_profile,
                 rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):

    risk_dollar = account_size * risk_percent / 100

    if ai_profile == "Challenge":
        profile_rule = """
PROFILO CHALLENGE:
- Cerca opportunità valide ma non forzare.
- Puoi accettare setup B se hanno RR buono e livello chiaro.
- A+ può essere ENTRA SUBITO o ORDINE PENDENTE.
- B deve essere solo ORDINE PENDENTE.
- C deve essere NON OPERARE.
- Non fare market su setup mediocre.
"""
    elif ai_profile == "Funded":
        profile_rule = """
PROFILO FUNDED:
- Priorità protezione conto.
- Solo setup A+ possono essere ENTRA SUBITO.
- Setup B solo ORDINE PENDENTE.
- Setup C sempre NON OPERARE.
- RR minimo ideale 1:2.
- Evita entrate tardive e prezzi in mezzo al range.
"""
    elif ai_profile == "Scalping":
        profile_rule = """
PROFILO SCALPING:
- Cerca timing rapido ma selettivo.
- A+ con momentum chiaro può essere ENTRA SUBITO.
- B solo ordine pendente su breakout/pullback.
- C non operare.
- Non inseguire movimenti già esplosi.
"""
    else:
        profile_rule = """
PROFILO STANDARD:
- Equilibrio tra operatività e filtro qualità.
- A+ può essere ENTRA SUBITO o ORDINE PENDENTE.
- B solo ORDINE PENDENTE.
- C NON OPERARE.
- Market order solo con zona, timing e RR coerenti.
"""

    focus = []
    if show_ema:
        focus.append("- Analizza EMA/media mobile: sopra, sotto, distanza, retest, supporto/resistenza dinamica.")
    if show_rsi:
        focus.append("- Analizza RSI: sopra/sotto 50, ipercomprato/ipervenduto, divergenze, momentum.")
    if show_levels:
        focus.append("- Analizza supporti, resistenze, massimi/minimi, liquidità, retest.")
    if show_volume:
        focus.append("- Analizza volumi se visibili.")
    focus_block = "\n".join(focus) if focus else "- Analizza tutti gli elementi visibili."

    mtf_block = """
OTTICA MULTI-TIMEFRAME:
- Timeframe alto = direzione principale.
- Timeframe medio = setup.
- Timeframe basso = timing.
- Se c'è un solo timeframe, lavora su quello ma sii più prudente.
""" if multi_tf else ""

    return f"""
Sei ProTrade AI, assistente di analisi trading per Andreas De Marco.

OBIETTIVO:
Fare meno segnali ma migliori.
Non devi cercare ogni movimento.
Devi filtrare solo setup tecnicamente validi.
Meglio perdere un'occasione che prendere un trade brutto.

REGOLA CENTRALE:
Devi scegliere sempre una sola decisione operativa:
1. ENTRA SUBITO
2. ORDINE PENDENTE
3. NON OPERARE

VIETATO:
- Usare ASPETTA.
- Dare LONG o SHORT senza numeri.
- Dare MARKET BUY/SELL su setup mediocre.
- Dare trade se il prezzo è in mezzo al nulla.
- Dare trade se RR è scarso.
- Dare trade solo perché RSI o EMA sono favorevoli.

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

FOCUS:
{focus_block}

==================================================
PROTRADE PRECISION TREND STRATEGY
==================================================

La strategia deve seguire questo ordine:

1. MARKET REGIME
Prima identifica il regime di mercato:
- TREND LONG
- TREND SHORT
- PULLBACK LONG
- PULLBACK SHORT
- BREAKOUT
- BREAKOUT + RETEST
- RANGE
- REVERSAL
- CHOPPY / SPORCO

Regole:
- Se CHOPPY / SPORCO = NO TRADE.
- Se RANGE = operare solo estremi chiari, mai in mezzo.
- Se TREND LONG = cercare long su pullback, retest o breakout pulito.
- Se TREND SHORT = cercare short su pullback, retest o breakdown pulito.
- Se REVERSAL = serve conferma forte, altrimenti NO TRADE.

2. TREND REALE
Non basta EMA.
Devi leggere:
- massimi crescenti
- minimi crescenti
- massimi decrescenti
- minimi decrescenti
- rottura ultimo massimo
- rottura ultimo minimo
- pullback su zona precedente
- reazione su supporto/resistenza
- candela di spinta o rifiuto

3. ZONA DI INGRESSO
Devi capire se il prezzo è:
- in zona buona
- troppo alto per comprare
- troppo basso per vendere
- vicino a resistenza
- vicino a supporto
- in mezzo al range
- lontano dalla EMA/media

Regole:
- Se prezzo in mezzo al nulla = NON OPERARE.
- Se prezzo lontano dalla zona buona = ORDINE PENDENTE, non market.
- Se prezzo vicino a resistenza, non dare long market se non c'è breakout.
- Se prezzo vicino a supporto, non dare short market se non c'è breakdown.

4. TIMING
Scegli il tipo ordine:
- MARKET BUY: solo A+, trend long, zona buona, momentum, RR buono.
- MARKET SELL: solo A+, trend short, zona buona, momentum, RR buono.
- BUY LIMIT: trend long, serve pullback su supporto/EMA/retest.
- SELL LIMIT: trend short, serve pullback su resistenza/EMA/retest.
- BUY STOP: trend long, serve rottura sopra massimo/resistenza.
- SELL STOP: trend short, serve rottura sotto minimo/supporto.
- NESSUN ORDINE: setup C, mercato sporco, RR scarso o numeri non leggibili.

5. RSI INTELLIGENTE
RSI non decide da solo.
- RSI 40-60 = neutro.
- RSI sopra 50 aiuta long.
- RSI sotto 50 aiuta short.
- RSI sopra 70 = evita long market tardivo; preferisci buy limit o no trade.
- RSI sotto 30 = evita short market tardivo; preferisci sell limit o no trade.
- Divergenza contro il trade = abbassa qualità.
- RSI estremo non blocca sempre, ma cambia tipo ordine.

6. RISK / REWARD
Regole dure:
- RR sotto 1:1.5 = NON OPERARE.
- RR 1:1.5 / 1:1.8 = accettabile solo Challenge o Scalping.
- RR sopra 1:2 = buono.
- Funded deve preferire RR almeno 1:2.
- Se lo stop è troppo largo e TP vicino, NON OPERARE.

7. SETUP QUALITY
Classifica sempre il setup:

A+:
- Trend chiaro.
- Struttura coerente.
- Prezzo in zona buona.
- Momentum favorevole.
- RSI non contrario.
- RR almeno buono.
- Spazio fino ai target.
Decisione: ENTRA SUBITO oppure ORDINE PENDENTE.

B:
- Direzione probabile.
- Setup interessante ma timing non perfetto.
- Serve pullback o breakout.
- RR potenzialmente buono.
Decisione: solo ORDINE PENDENTE.

C:
- Trend confuso.
- Prezzo in mezzo.
- RSI neutro senza spinta.
- RR scarso.
- Livelli non chiari.
Decisione: NON OPERARE.

8. GESTIONE POSIZIONE
Non usare 2 stop veri.
Usa:
- 1 Stop Loss reale.
- 1 Invalidazione tecnica.
- 3 Take Profit.
- Breakeven.
- Parziale.
- Trailing.

Regole gestione:
- TP1 = target prudente / primo ostacolo.
- TP2 = target tecnico principale.
- TP3 = estensione.
- A TP1: suggerisci parziale 40% o 50%.
- Dopo TP1: porta SL a BE se ha senso.
- Dopo TP2: trailing sotto minimo M5/M15 per long, sopra massimo M5/M15 per short.
- Invalidazione = livello tecnico dove il setup perde senso, anche se lo SL è già definito.

==================================================
REGOLE NUMERI OBBLIGATORI
==================================================

Se verdetto è LONG o SHORT devi dare:
- entry numerica
- stop_loss numerico
- invalidation_level numerico
- tp1 numerico
- tp2 numerico
- tp3 numerico
- risk_reward

Se non riesci a stimare numeri:
- verdetto = NO TRADE
- tipo_ordine = NESSUN ORDINE
- decisione_operativa = NON OPERARE

I numeri devono essere realistici per lo strumento:
- XAUUSD esempio 4151.80, 4139.00, 4174.50.
- EURUSD esempio 1.08450.
- NAS100 esempio 22250.00.

==================================================
FORMATO RISPOSTA OBBLIGATORIO
==================================================

Rispondi SOLO con JSON valido.
Non usare markdown.
Non scrivere ```json.
Non aggiungere testo fuori dal JSON.

JSON richiesto:
{{
  "verdetto": "LONG oppure SHORT oppure NO TRADE",
  "setup_quality": "A+ oppure B oppure C",
  "market_regime": "TREND LONG oppure TREND SHORT oppure PULLBACK LONG oppure PULLBACK SHORT oppure BREAKOUT oppure BREAKOUT + RETEST oppure RANGE oppure REVERSAL oppure CHOPPY / SPORCO",
  "tipo_segnale": "AGGRESSIVO oppure STANDARD oppure CONSERVATIVO",
  "tipo_ordine": "MARKET BUY oppure MARKET SELL oppure BUY LIMIT oppure SELL LIMIT oppure BUY STOP oppure SELL STOP oppure NESSUN ORDINE",
  "trade_score": 0,
  "confidence": 0,
  "market_bias": {{
    "trend_principale": "",
    "struttura": "",
    "zona_prezzo": "",
    "momentum": "",
    "volatilita": ""
  }},
  "rsi_check": {{
    "valore_stimato": "",
    "condizione": "",
    "conferma_o_blocca": "",
    "nota": ""
  }},
  "trade_setup": {{
    "entry": "",
    "stop_loss": "",
    "invalidation_level": "",
    "tp1": "",
    "tp2": "",
    "tp3": "",
    "risk_reward": ""
  }},
  "gestione": {{
    "parziale": "",
    "breakeven": "",
    "trailing": ""
  }},
  "risk_manager": {{
    "rischio_massimo": "{risk_dollar:.2f} USD",
    "size_consigliata": "da calcolare in base alla distanza SL",
    "nota_rischio": ""
  }},
  "ai_checklist": {{
    "trend": "OK / NEUTRO / CONTRO",
    "struttura": "OK / NEUTRO / CONTRO",
    "zona": "OK / NEUTRO / CONTRO",
    "ema": "OK / NEUTRO / CONTRO / NON VISIBILE",
    "rsi": "OK / NEUTRO / CONTRO / NON VISIBILE",
    "momentum": "OK / NEUTRO / CONTRO",
    "risk_reward": "OK / NEUTRO / SCARSO"
  }},
  "motivazione": "",
  "invalidazione": "",
  "decisione_operativa": "ENTRA SUBITO oppure ORDINE PENDENTE oppure NON OPERARE"
}}
"""


def safe_json_loads(text):
    cleaned = str(text).strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def empty_parsed():
    return {
        "VERDETTO": "N/D",
        "SETUP QUALITY": "N/D",
        "MARKET REGIME": "N/D",
        "TIPO SEGNALE": "N/D",
        "TIPO ORDINE": "N/D",
        "TRADE SCORE": "0",
        "CONFIDENCE": "0",
        "MARKET BIAS": {},
        "RSI CHECK": {},
        "TRADE SETUP": {},
        "GESTIONE": {},
        "RISK MANAGER": {},
        "AI CHECKLIST": {},
        "MOTIVAZIONE": "N/D",
        "INVALIDAZIONE": "N/D",
        "DECISIONE OPERATIVA": "N/D"
    }


def parse_ai_response(text):
    parsed = empty_parsed()
    try:
        data = safe_json_loads(text)

        parsed["VERDETTO"] = str(data.get("verdetto", "N/D")).upper()
        parsed["SETUP QUALITY"] = str(data.get("setup_quality", "N/D")).upper()
        parsed["MARKET REGIME"] = str(data.get("market_regime", "N/D")).upper()
        parsed["TIPO SEGNALE"] = str(data.get("tipo_segnale", "N/D")).upper()
        parsed["TIPO ORDINE"] = str(data.get("tipo_ordine", "N/D")).upper()
        parsed["TRADE SCORE"] = str(data.get("trade_score", "0"))
        parsed["CONFIDENCE"] = str(data.get("confidence", "0"))

        mb = data.get("market_bias", {}) or {}
        parsed["MARKET BIAS"] = {
            "trend principale": str(mb.get("trend_principale", "N/D")),
            "struttura": str(mb.get("struttura", "N/D")),
            "zona prezzo": str(mb.get("zona_prezzo", "N/D")),
            "momentum": str(mb.get("momentum", "N/D")),
            "volatilità": str(mb.get("volatilita", "N/D"))
        }

        rsi = data.get("rsi_check", {}) or {}
        parsed["RSI CHECK"] = {
            "valore stimato": str(rsi.get("valore_stimato", "N/D")),
            "condizione": str(rsi.get("condizione", "N/D")),
            "conferma o blocca il trade": str(rsi.get("conferma_o_blocca", "N/D")),
            "nota": str(rsi.get("nota", "N/D"))
        }

        ts = data.get("trade_setup", {}) or {}
        parsed["TRADE SETUP"] = {
            "entry": str(ts.get("entry", "N/D")),
            "stop loss": str(ts.get("stop_loss", "N/D")),
            "invalidation level": str(ts.get("invalidation_level", "N/D")),
            "tp1": str(ts.get("tp1", "N/D")),
            "tp2": str(ts.get("tp2", "N/D")),
            "tp3": str(ts.get("tp3", "N/D")),
            "risk/reward": str(ts.get("risk_reward", "N/D"))
        }

        gestione = data.get("gestione", {}) or {}
        parsed["GESTIONE"] = {
            "parziale": str(gestione.get("parziale", "N/D")),
            "breakeven": str(gestione.get("breakeven", "N/D")),
            "trailing": str(gestione.get("trailing", "N/D"))
        }

        rm = data.get("risk_manager", {}) or {}
        parsed["RISK MANAGER"] = {
            "rischio massimo": str(rm.get("rischio_massimo", "N/D")),
            "size consigliata": str(rm.get("size_consigliata", "N/D")),
            "nota rischio": str(rm.get("nota_rischio", "N/D"))
        }

        ck = data.get("ai_checklist", {}) or {}
        parsed["AI CHECKLIST"] = {
            "trend": str(ck.get("trend", "N/D")),
            "struttura": str(ck.get("struttura", "N/D")),
            "zona": str(ck.get("zona", "N/D")),
            "ema": str(ck.get("ema", "N/D")),
            "rsi": str(ck.get("rsi", "N/D")),
            "momentum": str(ck.get("momentum", "N/D")),
            "risk/reward": str(ck.get("risk_reward", "N/D"))
        }

        parsed["MOTIVAZIONE"] = str(data.get("motivazione", "N/D"))
        parsed["INVALIDAZIONE"] = str(data.get("invalidazione", "N/D"))
        parsed["DECISIONE OPERATIVA"] = str(data.get("decisione_operativa", "N/D")).upper()
        return parsed

    except Exception as e:
        parsed["MOTIVAZIONE"] = f"Errore parser JSON: {e}"
        parsed["INVALIDAZIONE"] = str(text)
        return parsed


def clean_value(value):
    if value is None:
        return "N/D"
    value = str(value).strip()
    if value == "" or value.lower() in ["none", "null", "nan"]:
        return "N/D"
    return value


def is_missing(value):
    return clean_value(value).upper() in ["N/D", "N/A", "", "-", "NONE", "NULL"]


def extract_number(value, default=0):
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return default
    return default


def has_number(value):
    return re.search(r"\d", str(value)) is not None


def get_rsi_value(rsi_dict):
    return extract_number(rsi_dict.get("valore stimato", ""), 50.0)


def verdict_style(verdetto, tipo_ordine):
    text = f"{verdetto} {tipo_ordine}".upper()
    if "LONG" in text or "BUY" in text:
        return "signal-long", "#00E676", "🐂"
    if "SHORT" in text or "SELL" in text:
        return "signal-short", "#FF5252", "🐻"
    return "signal-no", "#9E9E9E", "⛔"


def bars(level, max_level=5, full="🟩", empty="⬜"):
    try:
        level = int(round(level))
    except Exception:
        level = 0
    level = max(0, min(max_level, level))
    return full * level + empty * (max_level - level)


def volatility_level(vol_text):
    text = str(vol_text).lower()
    if "alta" in text:
        return 4
    if "media" in text:
        return 3
    if "bassa" in text:
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


def repair_needed(parsed):
    verdict = str(parsed.get("VERDETTO", "")).upper()
    setup = parsed.get("TRADE SETUP", {}) or {}

    if verdict not in ["LONG", "SHORT"]:
        return False

    required_fields = [
        setup.get("entry", ""),
        setup.get("stop loss", ""),
        setup.get("invalidation level", ""),
        setup.get("tp1", ""),
        setup.get("tp2", ""),
        setup.get("tp3", ""),
        setup.get("risk/reward", "")
    ]

    for field in required_fields:
        if is_missing(field):
            return True

    for field in required_fields[:6]:
        if not has_number(field):
            return True

    return False


def force_no_trade(parsed, reason):
    parsed["VERDETTO"] = "NO TRADE"
    parsed["SETUP QUALITY"] = "C"
    parsed["MARKET REGIME"] = "CHOPPY / SPORCO"
    parsed["TIPO ORDINE"] = "NESSUN ORDINE"
    parsed["TIPO SEGNALE"] = "CONSERVATIVO"
    parsed["TRADE SCORE"] = "0"
    parsed["CONFIDENCE"] = "0"
    parsed["DECISIONE OPERATIVA"] = "NON OPERARE"
    parsed["TRADE SETUP"] = {
        "entry": "N/D",
        "stop loss": "N/D",
        "invalidation level": "N/D",
        "tp1": "N/D",
        "tp2": "N/D",
        "tp3": "N/D",
        "risk/reward": "N/D"
    }
    parsed["GESTIONE"] = {
        "parziale": "N/D",
        "breakeven": "N/D",
        "trailing": "N/D"
    }
    parsed["MOTIVAZIONE"] = reason
    return parsed


def parsed_to_json(parsed):
    setup = parsed.get("TRADE SETUP", {}) or {}
    mb = parsed.get("MARKET BIAS", {}) or {}
    rsi = parsed.get("RSI CHECK", {}) or {}
    ck = parsed.get("AI CHECKLIST", {}) or {}
    rm = parsed.get("RISK MANAGER", {}) or {}
    gestione = parsed.get("GESTIONE", {}) or {}

    data = {
        "verdetto": parsed.get("VERDETTO", "NO TRADE"),
        "setup_quality": parsed.get("SETUP QUALITY", "C"),
        "market_regime": parsed.get("MARKET REGIME", "CHOPPY / SPORCO"),
        "tipo_segnale": parsed.get("TIPO SEGNALE", "CONSERVATIVO"),
        "tipo_ordine": parsed.get("TIPO ORDINE", "NESSUN ORDINE"),
        "trade_score": int(extract_number(parsed.get("TRADE SCORE", 0), 0)),
        "confidence": int(extract_number(parsed.get("CONFIDENCE", 0), 0)),
        "market_bias": {
            "trend_principale": mb.get("trend principale", "N/D"),
            "struttura": mb.get("struttura", "N/D"),
            "zona_prezzo": mb.get("zona prezzo", "N/D"),
            "momentum": mb.get("momentum", "N/D"),
            "volatilita": mb.get("volatilità", "N/D")
        },
        "rsi_check": {
            "valore_stimato": rsi.get("valore stimato", "N/D"),
            "condizione": rsi.get("condizione", "N/D"),
            "conferma_o_blocca": rsi.get("conferma o blocca il trade", "N/D"),
            "nota": rsi.get("nota", "N/D")
        },
        "trade_setup": {
            "entry": setup.get("entry", "N/D"),
            "stop_loss": setup.get("stop loss", "N/D"),
            "invalidation_level": setup.get("invalidation level", "N/D"),
            "tp1": setup.get("tp1", "N/D"),
            "tp2": setup.get("tp2", "N/D"),
            "tp3": setup.get("tp3", "N/D"),
            "risk_reward": setup.get("risk/reward", "N/D")
        },
        "gestione": {
            "parziale": gestione.get("parziale", "N/D"),
            "breakeven": gestione.get("breakeven", "N/D"),
            "trailing": gestione.get("trailing", "N/D")
        },
        "risk_manager": {
            "rischio_massimo": rm.get("rischio massimo", "N/D"),
            "size_consigliata": rm.get("size consigliata", "N/D"),
            "nota_rischio": rm.get("nota rischio", "N/D")
        },
        "ai_checklist": {
            "trend": ck.get("trend", "N/D"),
            "struttura": ck.get("struttura", "N/D"),
            "zona": ck.get("zona", "N/D"),
            "ema": ck.get("ema", "N/D"),
            "rsi": ck.get("rsi", "N/D"),
            "momentum": ck.get("momentum", "N/D"),
            "risk_reward": ck.get("risk/reward", "N/D")
        },
        "motivazione": parsed.get("MOTIVAZIONE", "N/D"),
        "invalidazione": parsed.get("INVALIDAZIONE", "N/D"),
        "decisione_operativa": parsed.get("DECISIONE OPERATIVA", "NON OPERARE")
    }

    return json.dumps(data, ensure_ascii=False)


def analyze_chart(image_file, symbol, timeframe, account_size, risk_percent, prop_mode,
                  ai_profile, rr_minimo, multi_tf, show_ema, show_rsi, show_levels, show_volume):
    try:
        img = Image.open(image_file)

        prompt = build_prompt(
            symbol=symbol,
            timeframe=timeframe,
            account_size=account_size,
            risk_percent=risk_percent,
            prop_mode=prop_mode,
            ai_profile=ai_profile,
            rr_minimo=rr_minimo,
            multi_tf=multi_tf,
            show_ema=show_ema,
            show_rsi=show_rsi,
            show_levels=show_levels,
            show_volume=show_volume
        )

        response = model.generate_content([prompt, img])

        if not response or not hasattr(response, "text"):
            return json.dumps({"error": "Gemini non ha restituito testo."}, ensure_ascii=False)

        first_text = response.text
        parsed_first = parse_ai_response(first_text)

        if not repair_needed(parsed_first):
            return parsed_to_json(parsed_first)

        repair_prompt = f"""
Hai dato {parsed_first.get('VERDETTO')} ma mancano numeri obbligatori.

REGOLE ASSOLUTE:
- Rispondi SOLO con JSON valido.
- Se LONG o SHORT: entry, stop_loss, invalidation_level, tp1, tp2, tp3, risk_reward devono contenere numeri.
- Se non puoi dare numeri, devi mettere NO TRADE, C, NESSUN ORDINE, NON OPERARE.
- Non usare markdown.
- Non usare ASPETTA.
- Non inventare segnale se il grafico non è leggibile.

Strumento: {symbol}
Timeframe: {timeframe}
Profilo AI: {ai_profile}
Rischio massimo: {account_size * risk_percent / 100:.2f} USD

Risposta precedente errata:
{first_text}

Restituisci SOLO questo JSON:
{{
  "verdetto": "LONG oppure SHORT oppure NO TRADE",
  "setup_quality": "A+ oppure B oppure C",
  "market_regime": "TREND LONG oppure TREND SHORT oppure PULLBACK LONG oppure PULLBACK SHORT oppure BREAKOUT oppure BREAKOUT + RETEST oppure RANGE oppure REVERSAL oppure CHOPPY / SPORCO",
  "tipo_segnale": "AGGRESSIVO oppure STANDARD oppure CONSERVATIVO",
  "tipo_ordine": "MARKET BUY oppure MARKET SELL oppure BUY LIMIT oppure SELL LIMIT oppure BUY STOP oppure SELL STOP oppure NESSUN ORDINE",
  "trade_score": 0,
  "confidence": 0,
  "market_bias": {{"trend_principale":"", "struttura":"", "zona_prezzo":"", "momentum":"", "volatilita":""}},
  "rsi_check": {{"valore_stimato":"", "condizione":"", "conferma_o_blocca":"", "nota":""}},
  "trade_setup": {{"entry":"", "stop_loss":"", "invalidation_level":"", "tp1":"", "tp2":"", "tp3":"", "risk_reward":""}},
  "gestione": {{"parziale":"", "breakeven":"", "trailing":""}},
  "risk_manager": {{"rischio_massimo":"{account_size * risk_percent / 100:.2f} USD", "size_consigliata":"da calcolare in base alla distanza SL", "nota_rischio":""}},
  "ai_checklist": {{"trend":"", "struttura":"", "zona":"", "ema":"", "rsi":"", "momentum":"", "risk_reward":""}},
  "motivazione":"",
  "invalidazione":"",
  "decisione_operativa":"ENTRA SUBITO oppure ORDINE PENDENTE oppure NON OPERARE"
}}
"""

        repair_response = model.generate_content([repair_prompt, img])

        if repair_response and hasattr(repair_response, "text"):
            parsed_repair = parse_ai_response(repair_response.text)
            if not repair_needed(parsed_repair):
                return parsed_to_json(parsed_repair)

        forced = force_no_trade(
            parsed_first,
            "Segnale annullato: l'AI non ha fornito Entry, Stop Loss, invalidazione, TP1, TP2, TP3 e RR numerici. Meglio non operare che prendere un trade incompleto."
        )
        return parsed_to_json(forced)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def save_history(mode, symbol, timeframe, result):
    st.session_state.history.append({
        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "mode": mode,
        "symbol": symbol,
        "timeframe": timeframe,
        "result": result
    })


with st.sidebar:
    st.markdown('<div class="section-label">MODALITÀ AI</div>', unsafe_allow_html=True)

    modes = [
        ("Challenge", "🏆", "CHALLENGE", "Operativa ma filtrata"),
        ("Standard", "📊", "STANDARD", "Equilibrata"),
        ("Funded", "🛡️", "FUNDED", "Prudente e selettiva"),
        ("Scalping", "⚡", "SCALPING", "Rapida M1/M5"),
    ]

    for key, icon, title, desc in modes:
        active = st.session_state.ai_profile == key
        css_class = "mode-card mode-card-active" if active else "mode-card"

        st.markdown(
            f'<div class="{css_class}"><div class="mode-title">{icon} {title}</div><div class="mode-desc">{desc}</div></div>',
            unsafe_allow_html=True
        )

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
    st.caption(f"Rischio massimo: {risk_dollar:,.2f} USD")

    rr_minimo = st.selectbox("RR Minimo", ["1:1.5", "1:1.8", "1:2.0", "1:2.5", "1:3.0"], index=2)
    prop_mode = st.selectbox("Prop Firm", ["Standard", "FTMO", "FTUK", "Prop Firm Conservativa"])

    st.markdown('<div class="section-label">ELEMENTI DA ANALIZZARE</div>', unsafe_allow_html=True)

    show_ema = st.toggle("EMA / Media", value=True)
    show_rsi = st.toggle("RSI", value=True)
    show_levels = st.toggle("Supporti e Resistenze", value=True)
    show_volume = st.toggle("Volumi", value=False)

    st.markdown('<div class="section-label">CARICA GRAFICO</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Carica screenshot", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    analyze_clicked = st.button("⚡ ANALIZZA GRAFICO", use_container_width=True)


now = datetime.now()

st.markdown(f"""
<div class="top-header">
    <div>
        <div class="brand">⚡ ProTrade AI</div>
        <div class="subbrand">Precision Trend Strategy · by Andreas De Marco</div>
    </div>
    <div style="text-align:right;">
        <div class="live-badge">🟢 LIVE ANALYSIS</div>
        <div style="color:#8B98A9;font-size:12px;margin-top:6px;">{now.strftime('%H:%M:%S')} · {now.strftime('%d/%m/%Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="chart-panel"><div class="chart-panel-title">{symbol} · {timeframe}</div><div class="chart-panel-sub">Screenshot caricato per analisi ProTrade AI</div>',
    unsafe_allow_html=True
)

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
else:
    st.info("Carica uno screenshot del grafico dalla sidebar per iniziare.")

st.markdown("</div>", unsafe_allow_html=True)

if analyze_clicked and uploaded_file:
    with st.spinner("ProTrade AI sta analizzando il grafico..."):
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

        save_history(
            st.session_state.ai_profile,
            symbol,
            timeframe,
            result
        )

elif analyze_clicked and not uploaded_file:
    st.warning("Carica prima uno screenshot del grafico.")

if st.session_state.last_result:
    result = st.session_state.last_result

    try:
        error_data = safe_json_loads(result)
        if isinstance(error_data, dict) and "error" in error_data:
            st.error(error_data["error"])
            st.stop()
    except Exception:
        pass

    parsed = parse_ai_response(result)

    if repair_needed(parsed):
        parsed = force_no_trade(
            parsed,
            "Segnale bloccato: mancano Entry, Stop Loss, invalidazione, TP1, TP2, TP3 o Risk/Reward numerici."
        )

    verdetto = clean_value(parsed.get("VERDETTO", "N/D"))
    setup_quality = clean_value(parsed.get("SETUP QUALITY", "N/D"))
    market_regime = clean_value(parsed.get("MARKET REGIME", "N/D"))
    tipo_segnale = clean_value(parsed.get("TIPO SEGNALE", "N/D"))
    tipo_ordine = clean_value(parsed.get("TIPO ORDINE", "N/D"))
    trade_score_raw = clean_value(parsed.get("TRADE SCORE", "0"))
    confidence_raw = clean_value(parsed.get("CONFIDENCE", "0"))
    decisione = clean_value(parsed.get("DECISIONE OPERATIVA", "N/D"))

    market_bias = parsed.get("MARKET BIAS", {}) or {}
    rsi_check = parsed.get("RSI CHECK", {}) or {}
    trade_setup = parsed.get("TRADE SETUP", {}) or {}
    checklist = parsed.get("AI CHECKLIST", {}) or {}
    gestione = parsed.get("GESTIONE", {}) or {}

    motivazione = clean_value(parsed.get("MOTIVAZIONE", "N/D"))
    invalidazione = clean_value(parsed.get("INVALIDAZIONE", "N/D"))

    score_num = int(extract_number(trade_score_raw, 0))
    conf_num = int(extract_number(confidence_raw, 0))

    css_class, accent_color, icon = verdict_style(verdetto, tipo_ordine)

    entry_value = clean_value(trade_setup.get("entry", "N/D"))
    sl_value = clean_value(trade_setup.get("stop loss", "N/D"))
    invalidation_value = clean_value(trade_setup.get("invalidation level", "N/D"))
    tp1_value = clean_value(trade_setup.get("tp1", "N/D"))
    tp2_value = clean_value(trade_setup.get("tp2", "N/D"))
    tp3_value = clean_value(trade_setup.get("tp3", "N/D"))
    rr_value = clean_value(trade_setup.get("risk/reward", "N/D"))

    st.markdown(f"""
    <div class="signal-card {css_class}">
        <div style="display:flex;align-items:center;gap:20px;">
            <div style="font-size:44px;">{icon}</div>
            <div>
                <div class="signal-verdict" style="color:{accent_color};">{verdetto}</div>
                <div class="signal-confidence">CONFIDENCE {conf_num}% · {tipo_ordine}</div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:#8B98A9;font-size:12px;">DECISIONE</div>
            <div style="font-weight:800;font-size:16px;">{decisione}</div>
            <div style="color:#8B98A9;font-size:12px;margin-top:6px;">SETUP {setup_quality} · {market_regime}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'<div class="metric-box"><div class="metric-title">ENTRY</div><div class="metric-value" style="color:#00E676;">{entry_value}</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f'<div class="metric-box"><div class="metric-title">STOP LOSS</div><div class="metric-value" style="color:#FF5252;">{sl_value}</div></div>', unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="metric-box"><div class="metric-title">TP1</div><div class="metric-value" style="color:#4FC3F7;">{tp1_value}</div></div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f'<div class="metric-box"><div class="metric-title">RISK / REWARD</div><div class="metric-value" style="color:#FFD166;">{rr_value}</div></div>', unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.markdown(f'<div class="metric-box"><div class="metric-title">INVALIDAZIONE</div><div class="metric-value" style="color:#FFB74D;">{invalidation_value}</div></div>', unsafe_allow_html=True)

    with c6:
        st.markdown(f'<div class="metric-box"><div class="metric-title">TP2</div><div class="metric-value" style="color:#4FC3F7;">{tp2_value}</div></div>', unsafe_allow_html=True)

    with c7:
        st.markdown(f'<div class="metric-box"><div class="metric-title">TP3</div><div class="metric-value" style="color:#4FC3F7;">{tp3_value}</div></div>', unsafe_allow_html=True)

    with c8:
        st.markdown(f'<div class="metric-box"><div class="metric-title">SETUP QUALITY</div><div class="metric-value" style="color:#FFD54F;">{setup_quality}</div></div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1.2, 1, 1.4])

    with col_a:
        rows = ""
        for key, label in [
            ("trend", "Trend"),
            ("struttura", "Struttura"),
            ("zona", "Zona"),
            ("ema", "EMA"),
            ("rsi", "RSI"),
            ("momentum", "Momentum"),
            ("risk/reward", "Risk/Reward")
        ]:
            value = clean_value(checklist.get(key, "—"))
            rows += f'<div class="checklist-row"><span>{label}</span><span>{value}</span></div>'

        st.markdown(f'<div class="info-panel"><div class="info-panel-title">⚠️ CHECKLIST TECNICA</div>{rows}</div>', unsafe_allow_html=True)

    with col_b:
        rsi_val = get_rsi_value(rsi_check)
        rsi_condition = clean_value(rsi_check.get("condizione", "N/D"))
        rsi_confirm = clean_value(rsi_check.get("conferma o blocca il trade", "N/D"))

        st.markdown(f"""
        <div class="info-panel" style="text-align:center;">
            <div class="info-panel-title">RSI CHECK</div>
            <div style="font-size:34px;font-weight:900;color:#00E676;margin-top:8px;">{rsi_val:.1f}</div>
            <div style="font-size:12px;color:#8B98A9;">{rsi_condition}</div>
            <div style="margin-top:10px;font-size:12px;color:#C9D6E3;">{rsi_confirm}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        parziale = clean_value(gestione.get("parziale", "N/D"))
        breakeven = clean_value(gestione.get("breakeven", "N/D"))
        trailing = clean_value(gestione.get("trailing", "N/D"))

        st.markdown(f"""
        <div class="info-panel">
            <div class="info-panel-title">💬 SPIEGAZIONE AI</div>
            <div style="font-size:13px;line-height:1.6;color:#E2E8F0;">
                {motivazione}
                <br><br>
                <b>Gestione:</b><br>
                Parziale: {parziale}<br>
                Breakeven: {breakeven}<br>
                Trailing: {trailing}
                <br><br>
                <b>Invalidazione:</b><br>{invalidazione}
            </div>
        </div>
        """, unsafe_allow_html=True)

    vol_text = clean_value(market_bias.get("volatilità", "Media"))
    vol_lvl = volatility_level(vol_text)
    session = get_session()
    last_update = st.session_state.last_update or "--:--:--"

    st.markdown(f"""
    <div class="bottom-bar">
        <div class="bottom-stat"><div class="bottom-stat-title">PROBABILITÀ</div><div class="bottom-stat-value" style="color:#00E676;">{conf_num}%</div></div>
        <div class="bottom-stat"><div class="bottom-stat-title">SCORE</div><div class="bottom-stat-value">{score_num}/100</div></div>
        <div class="bottom-stat"><div class="bottom-stat-title">FORZA TREND</div><div class="bottom-stat-value">{bars(score_num / 20)}</div></div>
        <div class="bottom-stat"><div class="bottom-stat-title">VOLATILITÀ</div><div class="bottom-stat-value">{bars(vol_lvl, full="🟧")}</div></div>
        <div class="bottom-stat"><div class="bottom-stat-title">SESSIONE</div><div class="bottom-stat-value">{session}</div></div>
        <div class="bottom-stat"><div class="bottom-stat-title">UPDATE</div><div class="bottom-stat-value">{last_update}</div></div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Risposta completa AI / JSON"):
        st.code(result, language="json")

if st.session_state.history:
    st.markdown("---")
    st.markdown("## Storico Analisi")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(f"{item['time']} · {item['mode']} · {item['symbol']} {item['timeframe']}"):
            st.code(item["result"], language="json")

st.markdown("---")
st.caption("⚠️ ProTrade AI by Andreas De Marco è uno strumento di supporto. Non è consulenza finanziaria. Usa sempre gestione del rischio.")

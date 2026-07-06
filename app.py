import json
import re
from datetime import datetime
from typing import Any, Dict

import google.generativeai as genai
import streamlit as st
from PIL import Image

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="ProTrade AI", page_icon="⚡", layout="wide")

try:
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
st.error(f"Errore configurazione Gemini/API_KEY: {e}")
st.stop()

# =========================
# CSS
# =========================
st.markdown(
"""
<style>
:root {
--bg: #02070d;
--panel: #07111d;
--panel2: #0b1624;
--line: #14283a;
--gold: #f5b82e;
--green: #00ff7b;
--red: #ff3b4e;
--orange: #ffb020;
--gray: #a7b0bc;
--text: #f8fafc;
--muted: #94a3b8;
}
.stApp {
background:
radial-gradient(circle at top right, rgba(245,184,46,0.16), transparent 28%),
radial-gradient(circle at 20% 10%, rgba(0,255,123,0.10), transparent 24%),
linear-gradient(180deg, #02070d 0%, #030914 55%, #010409 100%);
color: var(--text);
}
.block-container {padding-top: 16px; padding-bottom: 30px; max-width: 1500px;}
section[data-testid="stSidebar"] {
background: linear-gradient(180deg, #040b13 0%, #070f1a 100%);
border-right: 1px solid #13283a;
}
section[data-testid="stSidebar"] * {color: #eef2f7 !important;}
.header {
display:flex; justify-content:space-between; align-items:center; gap:16px;
padding:20px 24px; border-radius:24px;
background: linear-gradient(135deg, rgba(8,20,33,0.98), rgba(5,12,20,0.96));
border:1px solid rgba(245,184,46,0.34);
box-shadow:0 0 35px rgba(0,0,0,0.35), inset 0 0 30px rgba(245,184,46,0.04);
margin-bottom:16px;
}
.logo {font-size:38px; font-weight:950; letter-spacing:-1px;}
.sublogo {font-size:15px; color:#d7a82d; margin-top:-5px; font-weight:700;}
.status-pill {padding:10px 16px; border-radius:999px; background:rgba(0,255,123,0.10); border:1px solid rgba(0,255,123,0.45); color:#00ff7b; font-weight:900; white-space:nowrap;}
.panel {
background: linear-gradient(145deg, rgba(7,17,29,0.95), rgba(10,22,36,0.88));
border:1px solid rgba(20,40,58,0.95);
border-radius:22px;
padding:18px;
box-shadow:0 18px 40px rgba(0,0,0,0.25);
margin-bottom:16px;
}
.panel h3 {margin-top:0; margin-bottom:12px; color:#fff !important;}
.chart-box {
border:1px solid #14304a;
border-radius:22px;
background:#030914;
padding:12px;
box-shadow: inset 0 0 35px rgba(0,0,0,0.35);
}
.signal {
min-height:210px;
border-radius:28px;
padding:28px;
text-align:center;
border:2px solid #273647;
position:relative;
overflow:hidden;
box-shadow:0 0 45px rgba(0,0,0,0.35);
}
.signal::before {
content:""; position:absolute; inset:-60px; opacity:.16; filter: blur(6px);
background: conic-gradient(from 90deg, transparent, currentColor, transparent, currentColor, transparent);
animation: spin 7s linear infinite;
}
@keyframes spin {to {transform: rotate(360deg);}}
.signal > * {position:relative; z-index:2;}
.sig-long {color:var(--green); border-color:var(--green); background: radial-gradient(circle, rgba(0,255,123,0.20), rgba(4,11,18,0.96) 62%);}
.sig-short {color:var(--red); border-color:var(--red); background: radial-gradient(circle, rgba(255,59,78,0.22), rgba(4,11,18,0.96) 62%);}
.sig-wait {color:var(--orange); border-color:var(--orange); background: radial-gradient(circle, rgba(255,176,32,0.20), rgba(4,11,18,0.96) 62%);}
.sig-no {color:var(--gray); border-color:#7d8794; background: radial-gradient(circle, rgba(150,160,175,0.15), rgba(4,11,18,0.96) 62%);}
.signal-label {font-size:13px; letter-spacing:2px; color:#cbd5e1; font-weight:900;}
.signal-main {font-size:72px; line-height:1; font-weight:1000; margin:12px 0 10px;}
.signal-sub {font-weight:800; color:#e2e8f0;}
.progress-bg {height:12px; border-radius:999px; background:#172333; margin-top:16px; overflow:hidden;}
.progress-fill {height:12px; border-radius:999px; background:linear-gradient(90deg, currentColor, #f5b82e);}
.metric-grid {display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px;}
.metric {
background:linear-gradient(145deg, #07111d, #0c1827);
border:1px solid #183249;
border-radius:20px;
padding:18px;
min-height:110px;
}
.metric .label {font-size:12px; letter-spacing:1px; color:#93a4b8; font-weight:900;}
.metric .value {font-size:28px; font-weight:1000; margin-top:10px; color:#fff; overflow-wrap:anywhere;}
.entry {border-color:rgba(0,255,123,.55)} .entry .value{color:var(--green)}
.stop {border-color:rgba(255,59,78,.55)} .stop .value{color:var(--red)}
.tp {border-color:rgba(0,210,255,.45)} .tp .value{color:#7dd3fc}
.rr {border-color:rgba(245,184,46,.65)} .rr .value{color:var(--gold)}
.gauge-wrap {display:flex; align-items:center; justify-content:center; flex-direction:column; gap:12px;}
.gauge {
width:170px; height:170px; border-radius:50%;
display:flex; align-items:center; justify-content:center;
background: radial-gradient(circle at center,#07111d 56%, transparent 57%), conic-gradient(currentColor 0deg, currentColor var(--deg), #1d2b3a var(--deg), #1d2b3a 360deg);
box-shadow: 0 0 28px rgba(0,0,0,.3);
}
.gauge .inner {text-align:center;}
.gauge .num {font-size:38px; font-weight:1000; color:#fff;}
.gauge .txt {font-size:12px; color:#94a3b8; font-weight:900; letter-spacing:1px;}
.check {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #13283a; padding:10px 0; font-weight:800;}
.ok {color:var(--green)} .warn {color:var(--orange)} .bad {color:var(--red)}
.reason {line-height:1.6; color:#e2e8f0; font-size:15px;}
.small-title {font-size:13px; color:#94a3b8; font-weight:900; letter-spacing:1px;}
.big-value {font-size:24px; font-weight:1000; margin-top:8px;}
.stButton>button {height:3.4rem; border-radius:18px; border:0; background:linear-gradient(135deg,#f5b82e,#ff9f1c); color:#04101a; font-weight:1000; font-size:16px;}
div[data-testid="stFileUploader"] {background:rgba(7,17,29,0.8); border:1px solid #14283a; border-radius:18px; padding:10px;}
label, h1, h2, h3 {color:white !important;}
@media (max-width: 900px) {.metric-grid {grid-template-columns:repeat(2, minmax(0,1fr));}.signal-main{font-size:48px}.header{flex-direction:column;align-items:flex-start}.gauge{width:140px;height:140px}}
</style>
""",
unsafe_allow_html=True,
)

# =========================
# UTILITIES
# =========================
def clamp_int(value: Any, default: int = 0, lo: int = 0, hi: int = 100) -> int:
try:
n = int(float(str(value).replace("%", "").strip()))
return max(lo, min(hi, n))
except Exception:
return default


def extract_json(text: str) -> Dict[str, Any] | None:
if not text:
return None
cleaned = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()
start = cleaned.find("{")
end = cleaned.rfind("}")
if start == -1 or end == -1 or end <= start:
return None
try:
return json.loads(cleaned[start : end + 1])
except Exception:
return None


def signal_style(signal: str) -> tuple[str, str]:
s = (signal or "NO TRADE").upper()
if "LONG" in s or "BUY" in s:
return "sig-long", "LONG"
if "SHORT" in s or "SELL" in s:
return "sig-short", "SHORT"
if "ASPETTA" in s or "WAIT" in s:
return "sig-wait", "ASPETTA"
return "sig-no", "NO TRADE"


def check_class(value: str) -> str:
v = (value or "WARN").upper()
if v == "OK":
return "ok"
if v == "BAD":
return "bad"
return "warn"


def fallback(raw: str) -> Dict[str, Any]:
return {
"signal": "NO TRADE",
"signal_type": "CONSERVATIVO",
"confidence": 0,
"trade_score": 0,
"entry": "N/A",
"stop_loss": "N/A",
"tp1": "N/A",
"tp2": "N/A",
"risk_reward": "N/A",
"rsi_value": "N/A",
"rsi_condition": "NON VISIBILE",
"rsi_decision": "NEUTRO",
"trend": "N/A",
"ema_check": "N/A",
"momentum": "N/A",
"structure": "N/A",
"volatility": "N/A",
"liquidity": "N/A",
"decision": "NON OPERARE",
"reason": raw or "Risposta AI non leggibile.",
"invalidation": "N/A",
"checklist": {"Trend": "WARN", "EMA": "WARN", "RSI": "WARN", "Momentum": "WARN", "Struttura": "WARN", "RR": "WARN"},
}

# =========================
# PROMPT
# =========================
def build_prompt(symbol: str, timeframe: str, profile: str, account: int, risk: float) -> str:
risk_usd = account * risk / 100
rules = {
"Challenge": "Profilo più operativo: accetta setup buoni anche se non perfetti. RR minimo 1:1.8/2.0. Non bloccare troppo i segnali.",
"Standard": "Profilo bilanciato: richiede trend/struttura coerenti, RSI non contrario e RR minimo 1:2.",
"Funded": "Profilo conservativo: proteggi il conto. Evita trade tardivi, RR minimo 1:2.5, no setup sporchi.",
"Scalping": "Profilo veloce: focus momentum e timing su M1/M5, ma evita RSI estremo e spike.",
}
return f"""
Sei ProTrade AI by Andreas De Marco. Analizzi screenshot di grafici trading.
Rispondi SOLO in JSON valido. Nessun markdown, nessun testo fuori dal JSON.

DATI OPERATIVI:
- Simbolo: {symbol}
- Timeframe: {timeframe}
- Profilo AI: {profile}
- Regola profilo: {rules[profile]}
- Account: {account} USD
- Rischio max: {risk}% = {risk_usd:.2f} USD

RAGIONAMENTO UMANO OBBLIGATORIO:
- Non essere troppo restrittivo: LONG/SHORT se il setup è buono e RR accettabile.
- ASPETTA se direzione buona ma manca conferma o ingresso è tardivo.
- NO TRADE solo se mercato laterale/sporco, livelli confusi, spike forti, RR scarso.
- Controlla RSI se visibile.
- Se RSI < 30 evita nuovi SHORT salvo breakdown fortissimo confermato.
- Se RSI > 70 evita nuovi LONG salvo breakout fortissimo confermato.
- RSI 40-60 = neutro, non bloccare da solo.
- Se RSI è contrario o diverge, abbassa confidence.
- Non vendere dopo discesa già estesa; non comprare dopo salita già estesa.
- Se trade buono ma tardi, decisione ASPETTA e spiega pullback/conferma.

JSON obbligatorio:
{{
"signal": "LONG oppure SHORT oppure ASPETTA oppure NO TRADE",
"signal_type": "AGGRESSIVO oppure STANDARD oppure CONSERVATIVO",
"confidence": 0,
"trade_score": 0,
"entry": "prezzo o zona",
"stop_loss": "prezzo o zona",
"tp1": "prezzo o zona",
"tp2": "prezzo o zona",
"risk_reward": "es. 1:2.3",
"rsi_value": "numero stimato oppure NON VISIBILE",
"rsi_condition": "IPERCOMPRATO/IPERVENDUTO/NEUTRO/FORTE/DEBOLE/NON VISIBILE",
"rsi_decision": "CONFERMA/BLOCCA/NEUTRO/ATTENDI",
"trend": "RIALZISTA/RIBASSISTA/NEUTRO",
"ema_check": "FAVOREVOLE/CONTRARIA/NEUTRA/NON VISIBILE",
"momentum": "POSITIVO/NEGATIVO/NEUTRO",
"structure": "BULLISH/BEARISH/LATERALE",
"volatility": "BASSA/MEDIA/ALTA",
"liquidity": "OK/ATTENZIONE/NON CHIARA",
"decision": "ENTRA/ASPETTA/NON OPERARE",
"reason": "spiegazione pratica in massimo 3 frasi",
"invalidation": "quando il setup non è più valido",
"checklist": {{
"Trend": "OK/WARN/BAD",
"EMA": "OK/WARN/BAD",
"RSI": "OK/WARN/BAD",
"Momentum": "OK/WARN/BAD",
"Struttura": "OK/WARN/BAD",
"RR": "OK/WARN/BAD"
}}
}}
"""


def analyze_image(uploaded_file, symbol: str, timeframe: str, profile: str, account: int, risk: float) -> Dict[str, Any]:
img = Image.open(uploaded_file)
prompt = build_prompt(symbol, timeframe, profile, account, risk)
response = model.generate_content([prompt, img])
data = extract_json(getattr(response, "text", ""))
return data if isinstance(data, dict) else fallback(getattr(response, "text", ""))

# =========================
# SIDEBAR
# =========================
with st.sidebar:
st.markdown("## ⚙️ ProTrade AI")
st.caption("by Andreas De Marco")
profile = st.radio("Profilo operativo", ["Challenge", "Standard", "Funded", "Scalping"], index=1)
st.markdown("---")
symbol = st.selectbox("Asset", ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"])
timeframe = st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4"])
st.markdown("---")
account = st.number_input("Account USD", min_value=1000, value=25000, step=1000)
risk = st.number_input("Rischio %", min_value=0.1, max_value=5.0, value=0.5, step=0.1)
st.info(f"Rischio max: {account * risk / 100:.2f} USD")
uploaded = st.file_uploader("Carica screenshot grafico", type=["jpg", "jpeg", "png"])

# =========================
# HEADER
# =========================
st.markdown(
"""
<div class="header">
<div>
<div class="logo">⚡ ProTrade AI</div>
<div class="sublogo">by Andreas De Marco · AI Trading Dashboard</div>
</div>
<div class="status-pill">● AI ONLINE</div>
</div>
""",
unsafe_allow_html=True,
)

# =========================
# MAIN
# =========================
left, right = st.columns([1.45, 1.0], gap="large")

with left:
st.markdown("<div class='panel'><h3>📈 Chart Input</h3>", unsafe_allow_html=True)
if uploaded:
st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
st.image(uploaded, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
else:
st.markdown("<div class='chart-box' style='height:360px;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-weight:900;'>Carica screenshot con candele + RSI visibile</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded and st.button("⚡ ANALIZZA MERCATO", use_container_width=True):
with st.spinner("ProTrade AI sta analizzando grafico, RSI, struttura e rischio..."):
try:
st.session_state.result = analyze_image(uploaded, symbol, timeframe, profile, account, risk)
st.session_state.updated = datetime.now().strftime("%H:%M:%S")
except Exception as e:
st.error(f"Errore analisi: {e}")

with right:
r = st.session_state.get("result")
if not r:
r = {
"signal": "WAIT", "signal_type": profile.upper(), "confidence": 0, "trade_score": 0,
"entry": "--", "stop_loss": "--", "tp1": "--", "tp2": "--", "risk_reward": "--",
"rsi_value": "--", "rsi_condition": "--", "rsi_decision": "--", "trend": "--", "ema_check": "--",
"momentum": "--", "structure": "--", "volatility": "--", "liquidity": "--", "decision": "--",
"reason": "Carica un grafico e premi Analizza Mercato.", "invalidation": "--",
"checklist": {"Trend":"WARN", "EMA":"WARN", "RSI":"WARN", "Momentum":"WARN", "Struttura":"WARN", "RR":"WARN"}
}

sig_class, sig_text = signal_style(str(r.get("signal", "NO TRADE")))
conf = clamp_int(r.get("confidence", 0))
score = clamp_int(r.get("trade_score", 0))

st.markdown(
f"""
<div class="signal {sig_class}">
<div class="signal-label">SEGNALE AI</div>
<div class="signal-main">{sig_text}</div>
<div class="signal-sub">{r.get('signal_type','')} · Confidence {conf}% · Trade Score {score}/100</div>
<div class="progress-bg"><div class="progress-fill" style="width:{conf}%"></div></div>
</div>
""",
unsafe_allow_html=True,
)

st.markdown(
f"""
<div class="metric-grid">
<div class="metric entry"><div class="label">ENTRY</div><div class="value">{r.get('entry','--')}</div></div>
<div class="metric stop"><div class="label">STOP LOSS</div><div class="value">{r.get('stop_loss','--')}</div></div>
<div class="metric tp"><div class="label">TP1 / TP2</div><div class="value">{r.get('tp1','--')}<br><span style='font-size:18px;color:#94a3b8'>{r.get('tp2','--')}</span></div></div>
<div class="metric rr"><div class="label">RISK/REWARD</div><div class="value">{r.get('risk_reward','--')}</div></div>
</div>
""",
unsafe_allow_html=True,
)

st.markdown("---")
a, b, c = st.columns([1, 1, 1.2], gap="large")

with a:
st.markdown("<div class='panel'><h3>🎯 Confidence</h3>", unsafe_allow_html=True)
deg = conf * 3.6
st.markdown(f"<div class='gauge-wrap'><div class='gauge {sig_class}' style='--deg:{deg}deg;'><div class='inner'><div class='num'>{conf}%</div><div class='txt'>CONFIDENCE</div></div></div><div class='big-value'>{r.get('decision','--')}</div></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

with b:
st.markdown("<div class='panel'><h3>RSI Check</h3>", unsafe_allow_html=True)
raw_rsi = str(r.get("rsi_value", "50"))
nums = re.findall(r"\d+\.?\d*", raw_rsi.replace(",", "."))
rsi_num = float(nums[0]) if nums else 50.0
rsi_num = max(0, min(100, rsi_num))
rsi_deg = rsi_num * 3.6
rsi_color_class = "sig-wait" if rsi_num > 70 or rsi_num < 30 else "sig-long"
st.markdown(f"<div class='gauge-wrap'><div class='gauge {rsi_color_class}' style='--deg:{rsi_deg}deg;'><div class='inner'><div class='num'>{r.get('rsi_value','--')}</div><div class='txt'>RSI</div></div></div><div class='big-value'>{r.get('rsi_condition','--')}</div><div style='color:#94a3b8;font-weight:800'>{r.get('rsi_decision','--')}</div></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

with c:
st.markdown("<div class='panel'><h3>✅ AI Checklist</h3>", unsafe_allow_html=True)
for k, v in (r.get("checklist") or {}).items():
cls = check_class(str(v))
st.markdown(f"<div class='check'><span>{k}</span><span class='{cls}'>{v}</span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

x1, x2, x3, x4, x5 = st.columns(5)
small_items = [
("Trend", r.get("trend", "--")),
("EMA", r.get("ema_check", "--")),
("Momentum", r.get("momentum", "--")),
("Volatilità", r.get("volatility", "--")),
("Update", st.session_state.get("updated", "--")),
]
for col, (title, value) in zip([x1, x2, x3, x4, x5], small_items):
with col:
st.markdown(f"<div class='panel'><div class='small-title'>{title}</div><div class='big-value'>{value}</div></div>", unsafe_allow_html=True)

st.markdown(
f"""
<div class="panel">
<h3>🧠 AI Thinking</h3>
<div class="reason">{r.get('reason','')}</div>
<br>
<div class="small-title">INVALIDAZIONE</div>
<div class="reason">{r.get('invalidation','')}</div>
</div>
""",
unsafe_allow_html=True,
)

st.caption("⚠️ ProTrade AI è uno strumento di supporto. Non è consulenza finanziaria. Gestisci sempre il rischio.")


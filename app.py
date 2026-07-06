import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime
import json
import re

st.set_page_config(page_title="ProTrade AI", page_icon="⚡", layout="wide")

genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ================= CSS =================

st.markdown("""
<style>
.stApp {
background: #03070d;
color: white;
}

.block-container {
padding-top: 1rem;
max-width: 1500px;
}

.header {
display:flex;
justify-content:space-between;
align-items:center;
padding:18px 22px;
border:1px solid #102333;
border-radius:22px;
background:linear-gradient(135deg,#061018,#08131f);
margin-bottom:16px;
}

.logo {
font-size:34px;
font-weight:900;
}

.sublogo {
color:#b7c0cc;
font-size:15px;
}

.live {
color:#27ff75;
border:1px solid #164f31;
background:#07190f;
padding:12px 22px;
border-radius:18px;
font-weight:800;
}

.side-card, .main-card, .small-card {
background:linear-gradient(145deg,#061018,#0b1420);
border:1px solid #13293a;
border-radius:18px;
padding:18px;
margin-bottom:14px;
box-shadow:0 0 20px rgba(0,0,0,0.35);
}

.profile-card {
padding:16px;
border-radius:16px;
margin-bottom:10px;
background:#0b1622;
border:1px solid #142b3c;
}

.profile-selected {
border:1px solid #f5b82e;
background:linear-gradient(135deg,#302207,#111827);
}

.chart-box {
border:1px solid #123047;
border-radius:20px;
padding:12px;
background:#040b12;
}

.signal-box {
border-radius:22px;
padding:26px;
text-align:center;
margin-top:16px;
margin-bottom:16px;
font-weight:900;
}

.signal-long {
border:2px solid #00ff66;
background:radial-gradient(circle,#063d1b,#061018);
box-shadow:0 0 30px rgba(0,255,102,0.35);
}

.signal-short {
border:2px solid #ff3838;
background:radial-gradient(circle,#3d0606,#061018);
box-shadow:0 0 30px rgba(255,56,56,0.35);
}

.signal-wait {
border:2px solid #ffb020;
background:radial-gradient(circle,#3a2805,#061018);
box-shadow:0 0 30px rgba(255,176,32,0.25);
}

.signal-no {
border:2px solid #8b98a5;
background:radial-gradient(circle,#242b33,#061018);
}

.signal-title {
font-size:20px;
color:#cfd8e3;
}

.signal-main {
font-size:76px;
line-height:1;
}

.long-text {color:#22ff72;}
.short-text {color:#ff4b4b;}
.wait-text {color:#ffbd45;}
.no-text {color:#aeb8c2;}

.metric-card {
border-radius:18px;
padding:18px;
text-align:center;
background:#07111b;
border:1px solid #173044;
}

.metric-label {
color:#9aa7b5;
font-size:14px;
font-weight:700;
}

.metric-value {
font-size:32px;
font-weight:900;
margin-top:6px;
}

.entry {border-color:#00c896;}
.sl {border-color:#ff3b3b;}
.tp {border-color:#00ff66;}
.rr {border-color:#f5b82e;}

.progress-bg {
height:10px;
border-radius:999px;
background:#17212c;
overflow:hidden;
margin-top:10px;
}

.progress-fill {
height:10px;
border-radius:999px;
background:linear-gradient(90deg,#00ff66,#f5b82e);
}

.gauge {
width:145px;
height:145px;
border-radius:50%;
margin:auto;
display:flex;
align-items:center;
justify-content:center;
background:
radial-gradient(circle at center,#07111b 55%,transparent 56%),
conic-gradient(#22ff72 0deg, #22ff72 var(--deg), #1b2b36 var(--deg), #1b2b36 360deg);
}

.gauge-inner {
text-align:center;
}

.gauge-value {
font-size:34px;
font-weight:900;
}

.gauge-label {
color:#cbd5e1;
font-size:13px;
}

.check-row {
display:flex;
justify-content:space-between;
border-bottom:1px solid #13293a;
padding:8px 0;
}

.ok {color:#22ff72;font-weight:800;}
.warn {color:#ffbd45;font-weight:800;}
.bad {color:#ff4b4b;font-weight:800;}

.stButton>button {
background:linear-gradient(135deg,#f5b82e,#ff9f1c);
color:#061018;
border-radius:16px;
height:3.4rem;
font-weight:900;
border:none;
}

div[data-testid="stFileUploader"] {
background:#07111b;
border:1px solid #13293a;
border-radius:18px;
padding:10px;
}

label, h1, h2, h3 {
color:white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================

def safe_json(text):
try:
cleaned = re.sub(r"```json|```", "", text).strip()
start = cleaned.find("{")
end = cleaned.rfind("}") + 1
return json.loads(cleaned[start:end])
except Exception:
return None


def signal_class(signal):
s = str(signal).upper()
if "LONG" in s or "BUY" in s:
return "signal-long", "long-text"
if "SHORT" in s or "SELL" in s:
return "signal-short", "short-text"
if "ASPETTA" in s or "WAIT" in s:
return "signal-wait", "wait-text"
return "signal-no", "no-text"


def build_prompt(symbol, timeframe, profile, account_size, risk_percent):
risk_dollar = account_size * risk_percent / 100

profile_rules = {
"Challenge": "Più operativo. Cerca opportunità buone anche se non perfette. RR minimo 1:2. Evita solo setup davvero sporchi.",
"Standard": "Bilanciato. Serve struttura chiara, RSI coerente e RR minimo 1:2.",
"Funded": "Conservativo. Proteggi il conto. Serve alta qualità, RR minimo 1:2.5, no ingressi tardivi.",
"Scalping": "Più rapido. Focus M1/M5, momentum e timing. Accetta setup veloci ma controlla RSI e spike."
}

return f"""
Sei ProTrade AI by Andreas De Marco.
Devi analizzare il grafico come un trader umano esperto, non come un generatore cieco di segnali.

DATI:
Simbolo: {symbol}
Timeframe: {timeframe}
Profilo operativo: {profile}
Regole profilo: {profile_rules[profile]}
Account: {account_size}
Rischio percentuale: {risk_percent}
Rischio dollari: {risk_dollar:.2f}

REGOLE IMPORTANTI:
- Non essere troppo restrittivo.
- LONG/SHORT se il setup è buono e il rapporto rischio/rendimento è accettabile.
- ASPETTA se manca solo conferma o il prezzo è entrato male.
- NO TRADE solo se mercato laterale/sporco, spike forti, livelli confusi, RR scarso.
- Controlla SEMPRE RSI se visibile.
- Se RSI sotto 30 evita nuovi SHORT salvo breakdown fortissimo.
- Se RSI sopra 70 evita nuovi LONG salvo breakout forte.
- Se RSI 40-60 è neutro.
- Se RSI diverge contro il trade, abbassa confidence.
- Non comprare dopo salita troppo estesa.
- Non vendere dopo discesa troppo estesa.
- Se ingresso è tardivo scrivi ASPETTA PULLBACK.

Rispondi SOLO in JSON valido, senza markdown.

Schema:
{{
"signal": "LONG/SHORT/ASPETTA/NO TRADE",
"signal_type": "AGGRESSIVO/STANDARD/CONSERVATIVO",
"confidence": 0,
"trade_score": 0,
"entry": "prezzo o zona",
"stop_loss": "prezzo",
"take_profit": "prezzo",
"tp2": "prezzo",
"risk_reward": "1:2.0",
"trend_h1": "RIALZISTA/RIBASSISTA/NEUTRO/NON VISIBILE",
"trend_h4": "RIALZISTA/RIBASSISTA/NEUTRO/NON VISIBILE",
"ema_check": "SOPRA/SOTTO/NEUTRO/NON VISIBILE",
"rsi_value": "numero stimato o NON VISIBILE",
"rsi_condition": "IPERCOMPRATO/IPERVENDUTO/NEUTRO/DEBOLE/FORTE/NON VISIBILE",
"rsi_decision": "CONFERMA/BLOCCA/NEUTRO/ATTENDI",
"momentum": "POSITIVO/NEGATIVO/NEUTRO",
"structure": "BULLISH/BEARISH/LATERALE",
"volatility": "BASSA/MEDIA/ALTA",
"liquidity": "OK/ATTENZIONE/NON CHIARA",
"technical_checklist": {{
"Trend": "OK/WARN/BAD",
"EMA": "OK/WARN/BAD",
"RSI": "OK/WARN/BAD",
"Momentum": "OK/WARN/BAD",
"Struttura": "OK/WARN/BAD",
"RR": "OK/WARN/BAD"
}},
"reason": "spiegazione breve pratica",
"invalidation": "quando il setup non vale più",
"decision": "ENTRA/ASPETTA/NON OPERARE"
}}
"""


def analyze(image_file, symbol, timeframe, profile, account_size, risk_percent):
img = Image.open(image_file)
prompt = build_prompt(symbol, timeframe, profile, account_size, risk_percent)
response = model.generate_content([prompt, img])
data = safe_json(response.text)

if data is None:
return {
"signal": "NO TRADE",
"signal_type": "CONSERVATIVO",
"confidence": 0,
"trade_score": 0,
"entry": "N/A",
"stop_loss": "N/A",
"take_profit": "N/A",
"tp2": "N/A",
"risk_reward": "N/A",
"trend_h1": "N/A",
"trend_h4": "N/A",
"ema_check": "N/A",
"rsi_value": "N/A",
"rsi_condition": "N/A",
"rsi_decision": "N/A",
"momentum": "N/A",
"structure": "N/A",
"volatility": "N/A",
"liquidity": "N/A",
"technical_checklist": {},
"reason": response.text,
"invalidation": "N/A",
"decision": "NON OPERARE"
}

return data


def check_class(v):
v = str(v).upper()
if v == "OK":
return "ok"
if v == "BAD":
return "bad"
return "warn"


# ================= UI =================

st.markdown("""
<div class="header">
<div>
<div class="logo">⚡ ProTrade AI</div>
<div class="sublogo">by Andreas De Marco</div>
</div>
<div class="live">● LIVE ANALYSIS</div>
</div>
""", unsafe_allow_html=True)

left, center = st.columns([0.95, 3.05])

with left:
st.markdown("<div class='side-card'><h3>⚙️ Modalità AI</h3>", unsafe_allow_html=True)

profile = st.radio(
"Profilo",
["Challenge", "Standard", "Funded", "Scalping"],
index=1,
label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='side-card'><h3>📊 Asset e timeframe</h3>", unsafe_allow_html=True)
symbol = st.selectbox("Asset", ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30", "BTCUSD"])
timeframe = st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4"])
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='side-card'><h3>🛡️ Risk Manager</h3>", unsafe_allow_html=True)
account_size = st.number_input("Account USD", min_value=1000, value=25000, step=1000)
risk_percent = st.number_input("Rischio %", min_value=0.1, max_value=5.0, value=0.5, step=0.1)
risk_dollar = account_size * risk_percent / 100
st.markdown(f"<b>Rischio max:</b> <span style='color:#f5b82e'>{risk_dollar:.2f} USD</span>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

uploaded = st.file_uploader("📤 Carica grafico", type=["jpg", "jpeg", "png"])

with center:
if uploaded:
st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
st.image(uploaded, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded and st.button("⚡ ANALIZZA MERCATO"):
with st.spinner("ProTrade AI sta ragionando come un trader umano..."):
result = analyze(uploaded, symbol, timeframe, profile, account_size, risk_percent)
st.session_state["last_result"] = result
st.session_state["last_update"] = datetime.now().strftime("%H:%M:%S")

if "last_result" in st.session_state:
r = st.session_state["last_result"]
signal = r.get("signal", "NO TRADE")
box_class, text_class = signal_class(signal)
confidence = int(float(r.get("confidence", 0) or 0))
score = int(float(r.get("trade_score", 0) or 0))

st.markdown(f"""
<div class="signal-box {box_class}">
<div class="signal-title">SEGNALE AI</div>
<div class="signal-main {text_class}">{signal}</div>
<div>CONFIDENCE {confidence}% · TRADE SCORE {score}/100 · {r.get("signal_type","")}</div>
<div class="progress-bg">
<div class="progress-fill" style="width:{confidence}%"></div>
</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
st.markdown(f"""
<div class="metric-card entry">
<div class="metric-label">ENTRY</div>
<div class="metric-value">{r.get("entry","N/A")}</div>
</div>
""", unsafe_allow_html=True)

with c2:
st.markdown(f"""
<div class="metric-card sl">
<div class="metric-label">STOP LOSS</div>
<div class="metric-value short-text">{r.get("stop_loss","N/A")}</div>
</div>
""", unsafe_allow_html=True)

with c3:
st.markdown(f"""
<div class="metric-card tp">
<div class="metric-label">TAKE PROFIT</div>
<div class="metric-value long-text">{r.get("take_profit","N/A")}</div>
</div>
""", unsafe_allow_html=True)

with c4:
st.markdown(f"""
<div class="metric-card rr">
<div class="metric-label">RISK / REWARD</div>
<div class="metric-value" style="color:#f5b82e">{r.get("risk_reward","N/A")}</div>
</div>
""", unsafe_allow_html=True)

a, b, c = st.columns([1.2, 0.85, 1.15])

with a:
st.markdown("<div class='main-card'><h3>⚠️ Analisi tecnica</h3>", unsafe_allow_html=True)
checklist = r.get("technical_checklist", {})
for k, v in checklist.items():
cls = check_class(v)
st.markdown(f"<div class='check-row'><span>{k}</span><span class='{cls}'>{v}</span></div>", unsafe_allow_html=True)

st.markdown(f"""
<div class='check-row'><span>Trend H1</span><span class='ok'>{r.get("trend_h1","N/A")}</span></div>
<div class='check-row'><span>EMA</span><span class='ok'>{r.get("ema_check","N/A")}</span></div>
<div class='check-row'><span>Struttura</span><span class='ok'>{r.get("structure","N/A")}</span></div>
</div>
""", unsafe_allow_html=True)

with b:
rsi_raw = str(r.get("rsi_value", "0")).replace(",", ".")
try:
rsi = float(re.findall(r"\d+\.?\d*", rsi_raw)[0])
except Exception:
rsi = 50

deg = max(0, min(360, rsi * 3.6))

st.markdown(f"""
<div class='main-card'>
<h3>RSI Check</h3>
<div class="gauge" style="--deg:{deg}deg;">
<div class="gauge-inner">
<div class="gauge-value">{r.get("rsi_value","N/A")}</div>
<div class="gauge-label">{r.get("rsi_condition","")}</div>
</div>
</div>
<br>
<b>Decisione:</b> {r.get("rsi_decision","N/A")}
</div>
""", unsafe_allow_html=True)

with c:
st.markdown(f"""
<div class='main-card'>
<h3>🧠 Spiegazione AI</h3>
<p>{r.get("reason","")}</p>
<hr>
<b>Invalidazione:</b><br>
{r.get("invalidation","")}
<br><br>
<b>Decisione:</b> <span class="{text_class}">{r.get("decision","")}</span>
</div>
""", unsafe_allow_html=True)

d1, d2, d3, d4, d5 = st.columns(5)

with d1:
st.markdown(f"<div class='small-card'><b>Probabilità</b><br><h2>{confidence}%</h2></div>", unsafe_allow_html=True)
with d2:
st.markdown(f"<div class='small-card'><b>Momentum</b><br><h2>{r.get('momentum','N/A')}</h2></div>", unsafe_allow_html=True)
with d3:
st.markdown(f"<div class='small-card'><b>Volatilità</b><br><h2>{r.get('volatility','N/A')}</h2></div>", unsafe_allow_html=True)
with d4:
st.markdown(f"<div class='small-card'><b>Liquidità</b><br><h2>{r.get('liquidity','N/A')}</h2></div>", unsafe_allow_html=True)
with d5:
st.markdown(f"<div class='small-card'><b>Update</b><br><h2>{st.session_state.get('last_update','')}</h2></div>", unsafe_allow_html=True)

st.caption("⚠️ ProTrade AI non fornisce consulenza finanziaria. Usa sempre giudizio e gestione del rischio.")

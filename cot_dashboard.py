"""
cot_dashboard.py — Streamlit dashboard
Čte data z GitHub raw URL (data/cot_supplemental.csv ve tvém repozitáři).

DŮLEŽITÉ: Před prvním spuštěním nastav svůj GitHub username a název repozitáře:
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ════════════════════════════════════════════════════════════════════
# ⚙️  NASTAV TYTO DVĚ HODNOTY na svůj GitHub username a název repa
GITHUB_USER = "tvuj-github-username"      # ← změň
GITHUB_REPO = "cot-dashboard"             # ← změň (název repozitáře)
# ════════════════════════════════════════════════════════════════════

DATA_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/data/cot_supplemental.csv"

st.set_page_config(
    page_title="COT Supplemental Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0d0f0e; color: #e8e4dc; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }
.dash-header { display:flex; align-items:baseline; justify-content:space-between;
    border-bottom:1px solid #2a2e2b; padding-bottom:1rem; margin-bottom:1.5rem; }
.dash-title { font-family:'IBM Plex Mono',monospace; font-size:20px; font-weight:500;
    color:#c8f5a0; letter-spacing:0.08em; text-transform:uppercase; }
.dash-sub { font-size:12px; color:#5a6358; font-family:'IBM Plex Mono',monospace; }
.metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:1.5rem; }
.metric-card { background:#131714; border:1px solid #1f2420; border-radius:8px; padding:14px 16px; }
.metric-label { font-size:10px; font-family:'IBM Plex Mono',monospace; color:#4a5248;
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px; }
.metric-value { font-size:22px; font-weight:500; font-family:'IBM Plex Mono',monospace; color:#e8e4dc; }
.metric-sub { font-size:11px; color:#4a5248; margin-top:2px; }
.metric-pos { color:#7ed957; }
.metric-neg { color:#e05a3a; }
.section-title { font-family:'IBM Plex Mono',monospace; font-size:11px; text-transform:uppercase;
    letter-spacing:0.12em; color:#3a4038; margin:1.5rem 0 0.75rem 0;
    border-bottom:1px solid #1a1e1b; padding-bottom:6px; }
.com-name { font-family:'IBM Plex Sans',sans-serif; font-weight:500; font-size:13px; color:#e8e4dc; }
.stButton > button { font-family:'IBM Plex Mono',monospace !important; font-size:11px !important;
    letter-spacing:0.08em !important; text-transform:uppercase !important;
    border:1px solid #2a2e2b !important; background:transparent !important;
    color:#5a6358 !important; border-radius:4px !important; padding:4px 14px !important; }
.stButton > button:hover { border-color:#c8f5a0 !important; color:#c8f5a0 !important; background:#0d150a !important; }
#MainMenu, footer, header { visibility:hidden; }
.stDeployButton { display:none; }
</style>
""", unsafe_allow_html=True)

COMMODITIES = [
    {"name": "Pšenice SRW",   "keyword": "WHEAT-SRW"},
    {"name": "Pšenice HRW",   "keyword": "WHEAT-HRW"},
    {"name": "Kukuřice",      "keyword": "CORN"},
    {"name": "Sója",          "keyword": "SOYBEANS"},
    {"name": "Sójový olej",   "keyword": "SOYBEAN OIL"},
    {"name": "Sójový šrot",   "keyword": "SOYBEAN MEAL"},
    {"name": "Živý skot",     "keyword": "LIVE CATTLE"},
    {"name": "Vepřové",       "keyword": "LEAN HOGS"},
    {"name": "Káva",          "keyword": "COFFEE"},
    {"name": "Kakao",         "keyword": "COCOA"},
    {"name": "Cukr č.11",     "keyword": "SUGAR NO. 11"},
    {"name": "Bavlna č.2",    "keyword": "COTTON NO. 2"},
    {"name": "Feeder Cattle", "keyword": "FEEDER CATTLE"},
]

@st.cache_data(ttl=3600 * 6, show_spinner=False)
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        df["Report_Date"]   = pd.to_datetime(df["Report_Date"], errors="coerce")
        df["NonComm_Long"]  = pd.to_numeric(df["NonComm_Long"],  errors="coerce")
        df["NonComm_Short"] = pd.to_numeric(df["NonComm_Short"], errors="coerce")
        df["Net"]           = df["NonComm_Long"] - df["NonComm_Short"]
        df["market_upper"]  = df["Market_and_Exchange_Names"].str.upper().str.strip()
        return df.dropna(subset=["Report_Date", "NonComm_Long", "NonComm_Short"]).sort_values("Report_Date").reset_index(drop=True)
    except Exception as e:
        return None

def get_commodity_data(df, keyword):
    mask = df["market_upper"].str.contains(keyword.upper(), na=False)
    return df[mask].drop_duplicates(subset=["Report_Date"]).sort_values("Report_Date").copy()

def cot_index(series, lookback_weeks):
    vals   = series.values
    result = pd.Series(index=series.index, dtype=float)
    for i in range(len(vals)):
        start  = max(0, i - lookback_weeks + 1)
        window = vals[start:i+1]
        mn, mx = window.min(), window.max()
        result.iloc[i] = 50.0 if mx == mn else (vals[i] - mn) / (mx - mn) * 100.0
    return result

def fmt_net(v):
    return f"{v/1000:+.1f}k" if abs(v) >= 1000 else f"{v:+.0f}"

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <div class="dash-title">📊 COT Supplemental · Non-Commercial</div>
  <div class="dash-sub">CFTC CIT Supplement · {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

# ── KONTROLA KONFIGURACE ──────────────────────────────────────────────────────
if GITHUB_USER == "tvuj-github-username":
    st.error("⚙️ Nastav svůj GitHub username v souboru `cot_dashboard.py` na řádku s `GITHUB_USER`.")
    st.code(f'GITHUB_USER = "tvuj-github-username"   # ← změň na svůj username\nGITHUB_REPO = "cot-dashboard"           # ← název repozitáře', language="python")
    st.stop()

# ── NAČTENÍ DAT ──────────────────────────────────────────────────────────────
with st.spinner("Načítám COT data z GitHubu…"):
    df_all = load_data()

if df_all is None or df_all.empty:
    st.error("❌ Data nenalezena. Zkontroluj:")
    st.markdown(f"""
- Spustil jsi `python update_data.py` lokálně?
- Nahral jsi soubor `data/cot_supplemental.csv` na GitHub?
- Je správně nastaven `GITHUB_USER = "{GITHUB_USER}"` a `GITHUB_REPO = "{GITHUB_REPO}"`?
- URL dat: `{DATA_URL}`
    """)
    st.stop()

last_date = df_all["Report_Date"].max()
st.markdown(
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:11px;color:#3a4038;margin-bottom:1.5rem'>"
    f"Poslední report: {last_date.strftime('%d.%m.%Y')} · {len(df_all):,} záznamů · Cache: 6h</div>",
    unsafe_allow_html=True
)

# ── LOOKBACK ─────────────────────────────────────────────────────────────────
c1, c2, c3, _ = st.columns([1, 1, 1, 6])
with c1:
    if st.button("1 rok"):  st.session_state["lookback"] = 52
with c2:
    if st.button("3 roky"): st.session_state["lookback"] = 156
with c3:
    if st.button("5 let"):  st.session_state["lookback"] = 260

lookback = st.session_state.get("lookback", 156)
lb_label = {52: "1 rok", 156: "3 roky", 260: "5 let"}.get(lookback, "3 roky")
st.markdown(
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;margin-bottom:1rem'>"
    f"COT Index lookback: <span style='color:#c8f5a0'>{lb_label} ({lookback} týdnů)</span></div>",
    unsafe_allow_html=True
)

# ── VÝPOČET ───────────────────────────────────────────────────────────────────
summary = []
for c in COMMODITIES:
    sub = get_commodity_data(df_all, c["keyword"])
    if len(sub) < 5:
        continue
    idx_s = cot_index(sub["Net"], lookback)
    summary.append({
        "key":        c["keyword"],
        "name":       c["name"],
        "net":        float(sub["Net"].iloc[-1]),
        "delta":      float(sub["Net"].iloc[-1] - sub["Net"].iloc[-2]) if len(sub) > 1 else 0.0,
        "long":       float(sub["NonComm_Long"].iloc[-1]),
        "short":      float(sub["NonComm_Short"].iloc[-1]),
        "cot_index":  float(idx_s.iloc[-1]),
        "data":       sub,
        "idx_series": idx_s,
    })

if not summary:
    st.error("Žádná data pro zobrazené komodity.")
    st.stop()

# ── SUMMARY CARDS ─────────────────────────────────────────────────────────────
bulls    = sum(1 for r in summary if r["cot_index"] <= 20)
bears    = sum(1 for r in summary if r["cot_index"] >= 80)
neuts    = len(summary) - bulls - bears
top_bull = min(summary, key=lambda x: x["cot_index"])
top_bear = max(summary, key=lambda x: x["cot_index"])

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Komodit</div>
    <div class="metric-value">{len(summary)}</div>
    <div class="metric-sub">CIT Supplemental</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Signály</div>
    <div class="metric-value">
      <span class="metric-pos">{bulls}▲</span>&nbsp;
      <span style="color:#3a4038;font-size:16px">{neuts}◆</span>&nbsp;
      <span class="metric-neg">{bears}▼</span>
    </div>
    <div class="metric-sub">bull · neu · bear</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Nejbullish</div>
    <div class="metric-value metric-pos" style="font-size:15px;margin-top:4px">{top_bull['name']}</div>
    <div class="metric-sub">Index {top_bull['cot_index']:.0f} · {lb_label}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Nejbearish</div>
    <div class="metric-value metric-neg" style="font-size:15px;margin-top:4px">{top_bear['name']}</div>
    <div class="metric-sub">Index {top_bear['cot_index']:.0f} · {lb_label}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── TABULKA ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Přehled · seřazeno od nejbullish</div>', unsafe_allow_html=True)

for r in sorted(summary, key=lambda x: x["cot_index"]):
    idx = r["cot_index"]
    ic  = "#7ed957" if idx <= 20 else ("#e05a3a" if idx >= 80 else "#c8c4bc")
    nc  = "pos" if r["net"] >= 0 else "neg"
    dc  = "pos" if r["delta"] >= 0 else "neg"
    da  = "▲" if r["delta"] >= 0 else "▼"
    if idx <= 20:
        sig = '<span style="background:#0d2010;color:#7ed957;padding:3px 8px;border-radius:4px;font-family:IBM Plex Mono,monospace;font-size:11px">▲ BULL</span>'
    elif idx >= 80:
        sig = '<span style="background:#2a0d0a;color:#e05a3a;padding:3px 8px;border-radius:4px;font-family:IBM Plex Mono,monospace;font-size:11px">▼ BEAR</span>'
    else:
        sig = '<span style="background:#1a1e1b;color:#5a6358;padding:3px 8px;border-radius:4px;font-family:IBM Plex Mono,monospace;font-size:11px">◆ NEU</span>'

    col1,col2,col3,col4,col5,col6,col7,col8 = st.columns([2.0,1.2,1.2,1.3,1.3,1.1,1.0,0.8])
    with col1: st.markdown(f'<div style="padding:9px 0"><div class="com-name">{r["name"]}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px;color:#5a6358'>Long: <span style='color:#7ed957'>{r['long']/1000:.1f}k</span></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px;color:#5a6358'>Short: <span style='color:#e05a3a'>{r['short']/1000:.1f}k</span></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:13px' class='{nc}'>Net: {fmt_net(r['net'])}</div>", unsafe_allow_html=True)
    with col5: st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px' class='{dc}'>{da} {fmt_net(r['delta'])}/t</div>", unsafe_allow_html=True)
    with col6: st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:14px;font-weight:500;color:{ic}'>IDX {idx:.0f}</div>", unsafe_allow_html=True)
    with col7: st.markdown(f"<div style='padding:9px 0'>{sig}</div>", unsafe_allow_html=True)
    with col8:
        if st.button("Graf", key=f"d_{r['key']}"):
            st.session_state["cot_detail"] = r["key"]
    st.markdown("<div style='border-bottom:1px solid #131714'></div>", unsafe_allow_html=True)

st.markdown("""
<div style='margin-top:1rem;font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;display:flex;gap:20px;flex-wrap:wrap'>
  <span><span style='color:#7ed957'>▲ IDX 0–20</span> Bullish — spekulanti přeprodáni</span>
  <span><span style='color:#e05a3a'>▼ IDX 80–100</span> Bearish — spekulanti překoupeni</span>
  <span><span style='color:#5a6358'>◆ IDX 20–80</span> Neutrální</span>
  <span>Net/t = týdenní změna net pozice</span>
</div>
""", unsafe_allow_html=True)

# ── DETAIL GRAF ───────────────────────────────────────────────────────────────
if "cot_detail" in st.session_state:
    key = st.session_state["cot_detail"]
    det = next((r for r in summary if r["key"] == key), None)
    if det:
        st.markdown(f'<div class="section-title" style="margin-top:2rem">{det["name"]} · detail</div>', unsafe_allow_html=True)
        _, close_col = st.columns([10, 1])
        with close_col:
            if st.button("✕ Zavřít"):
                del st.session_state["cot_detail"]
                st.rerun()

        sub    = det["data"]
        idx_s  = det["idx_series"]
        cutoff = sub["Report_Date"].max() - timedelta(weeks=lookback)
        sp     = sub[sub["Report_Date"] >= cutoff]
        ip     = idx_s[sub["Report_Date"] >= cutoff]

        dates   = sp["Report_Date"].dt.strftime("%d.%m.%y").tolist()
        net_v   = sp["Net"].tolist()
        long_v  = sp["NonComm_Long"].tolist()
        short_n = [-v for v in sp["NonComm_Short"].tolist()]
        idx_v   = ip.tolist()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.55, 0.45], vertical_spacing=0.06,
            subplot_titles=["Net pozice Non-Commercial (Long − Short)",
                            f"COT Index · lookback {lb_label}"])
        fig.add_trace(go.Bar(x=dates, y=net_v,
            marker_color=["#7ed957" if v >= 0 else "#e05a3a" for v in net_v],
            name="Net", hovertemplate="%{x}<br>Net: %{y:,.0f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=long_v, mode="lines", name="Long",
            line=dict(color="#7ed957", width=1, dash="dot"),
            hovertemplate="%{x}<br>Long: %{y:,.0f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=short_n, mode="lines", name="Short (neg.)",
            line=dict(color="#e05a3a", width=1, dash="dot"),
            hovertemplate="%{x}<br>Short: %{y:,.0f}<extra></extra>"), row=1, col=1)
        fig.add_hrect(y0=80, y1=100, fillcolor="rgba(224,90,58,0.07)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=0, y1=20, fillcolor="rgba(126,217,87,0.07)", line_width=0, row=2, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="#e05a3a", line_width=0.8, row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#7ed957", line_width=0.8, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot",  line_color="#2a2e2b", line_width=0.6, row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=idx_v, mode="lines",
            line=dict(color="#c8f5a0", width=2), fill="tozeroy",
            fillcolor="rgba(200,245,160,0.06)", name="COT Index",
            hovertemplate="%{x}<br>Index: %{y:.1f}<extra></extra>"), row=2, col=1)
        cc = "#7ed957" if idx_v[-1] <= 20 else ("#e05a3a" if idx_v[-1] >= 80 else "#c8f5a0")
        fig.add_trace(go.Scatter(x=[dates[-1]], y=[idx_v[-1]], mode="markers",
            marker=dict(color=cc, size=8, line=dict(color="#0d0f0e", width=2)),
            name=f"Aktuálně: {idx_v[-1]:.0f}"), row=2, col=1)
        ax = dict(showgrid=True, gridcolor="#131714", color="#3a4038",
                  tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038"),
                  zeroline=True, zerolinecolor="#1f2420")
        fig.update_layout(height=540, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d0f0e",
            margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
            legend=dict(font=dict(family="IBM Plex Mono", size=10, color="#5a6358"),
                        bgcolor="rgba(0,0,0,0)", orientation="h", y=1.02),
            hoverlabel=dict(bgcolor="#131714", bordercolor="#2a2e2b",
                            font=dict(family="IBM Plex Mono", size=11, color="#e8e4dc")))
        fig.update_xaxes(**ax)
        fig.update_yaxes(**ax)
        fig.update_yaxes(range=[0,100], row=2, col=1,
            tickvals=[0,20,50,80,100], ticktext=["0","20 ▲","50","80 ▼","100"])
        fig.update_annotations(font=dict(family="IBM Plex Mono", size=11, color="#5a6358"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        s1,s2,s3,s4 = st.columns(4)
        sc  = "#7ed957" if idx_v[-1] <= 20 else ("#e05a3a" if idx_v[-1] >= 80 else "#e8e4dc")
        sig = "BULLISH" if idx_v[-1] <= 20 else ("BEARISH" if idx_v[-1] >= 80 else "NEUTRÁL")
        for col, lbl, val, sub_v in [
            (s1, "COT Index",  f"{idx_v[-1]:.1f}", f"předchozí: {idx_v[-2]:.1f}" if len(idx_v)>1 else ""),
            (s2, "Net pozice", f"{net_v[-1]/1000:+.1f}k", "kontraktů"),
            (s3, "Rozsah",     f"{min(net_v)/1000:.0f}k / {max(net_v)/1000:.0f}k", lb_label),
            (s4, "Signál",     sig, f"lookback {lb_label}"),
        ]:
            vc = sc if lbl == "Signál" else "#e8e4dc"
            with col:
                st.markdown(f"""
                <div class="metric-card" style='margin-top:8px'>
                  <div class="metric-label">{lbl}</div>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:15px;color:{vc}'>{val}</div>
                  <div class="metric-sub">{sub_v}</div>
                </div>""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:2.5rem;padding-top:1rem;border-top:1px solid #1a1e1b;
  font-family:IBM Plex Mono,monospace;font-size:10px;color:#2a2e2b;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px'>
  <span>Zdroj: CFTC Commodity Index Trader Supplement · aktualizuj každý pátek přes update_data.py</span>
  <span>COT Index = (net − min) / (max − min) × 100 · Non-Commercial = Large Speculators</span>
</div>
""", unsafe_allow_html=True)

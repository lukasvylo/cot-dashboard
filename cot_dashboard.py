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
GITHUB_USER = "lukasvylo"      # ← změň
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
.barchart-table { width:100%; border-collapse:collapse; font-size:12px; margin-top:0.5rem; }
.barchart-table th { font-family:'IBM Plex Mono',monospace; font-size:9px; text-transform:uppercase;
    letter-spacing:0.1em; color:#3a4038; padding:6px 10px; text-align:right;
    border-bottom:1px solid #1a1e1b; font-weight:500; }
.barchart-table th:first-child { text-align:left; }
.barchart-table td { font-family:'IBM Plex Mono',monospace; font-size:12px;
    padding:7px 10px; text-align:right; color:#c8c4bc;
    border-bottom:1px solid #0f1210; }
.barchart-table td:first-child { text-align:left; font-family:'IBM Plex Sans',sans-serif;
    font-weight:500; font-size:13px; color:#e8e4dc; }
.barchart-table tr:hover td { background:#131714; }
.cell-high { color:#7ed957 !important; font-weight:500; }
.cell-low  { color:#e05a3a !important; font-weight:500; }
.cell-pos  { color:#7ed957; }
.cell-neg  { color:#e05a3a; }
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
        df = pd.read_csv(DATA_URL, parse_dates=["Report_Date"])
        df["NonComm_Long"]  = pd.to_numeric(df["NonComm_Long"],  errors="coerce")
        df["NonComm_Short"] = pd.to_numeric(df["NonComm_Short"], errors="coerce")
        df["Net"]           = df["NonComm_Long"] - df["NonComm_Short"]
        df["market_upper"]  = df["Market_and_Exchange_Names"].str.upper().str.strip()
        df = df.dropna(subset=["Report_Date", "NonComm_Long", "NonComm_Short"])
        df = df.drop_duplicates(subset=["market_upper", "Report_Date"])
        df = df.sort_values(["market_upper", "Report_Date"]).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Chyba načítání: {e}")
        return None

def get_commodity_data(df, keyword):
    mask = df["market_upper"].str.contains(keyword.upper(), na=False)
    sub = df[mask].drop_duplicates(subset=["Report_Date"]).sort_values("Report_Date")
    return sub.reset_index(drop=True).copy()

def cot_index(series, lookback_weeks):
    vals   = series.reset_index(drop=True).values
    result = pd.Series(index=range(len(vals)), dtype=float)
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

# ── COT TABULKA ───────────────────────────────────────────────────
st.markdown('<div class="section-title">COT Tabulka · Non-Commercial Net pozice</div>', unsafe_allow_html=True)

# Posledních 6 reportních dat — společná osa pro všechny komodity
all_dates_set = set()
for r in summary:
    for d in r["data"]["Report_Date"].tolist():
        all_dates_set.add(d)
last6_dates = sorted(all_dates_set)[-6:]
date_headers = [d.strftime("%d.%m.%y") for d in last6_dates]

th_dates = "".join([f"<th>{d}</th>" for d in date_headers])
html_rows = ""

for r in sorted(summary, key=lambda x: x["name"]):
    sub = r["data"]
    cutoff_52w = sub["Report_Date"].max() - pd.Timedelta(weeks=52)
    w52    = sub[sub["Report_Date"] >= cutoff_52w]["Net"]
    hi52   = float(w52.max()) if not w52.empty else None
    lo52   = float(w52.min()) if not w52.empty else None
    last_n = float(sub["Net"].iloc[-1])

    def fmt_v(v):
        if v is None:
            return "—"
        return f"{v/1000:+.1f}k" if abs(v) >= 1000 else f"{v:+.0f}"

    tol = max(500, abs((hi52 or 0) - (lo52 or 0)) * 0.015)
    def td(v, hi, lo):
        f = fmt_v(v)
        if hi is not None and abs(v - hi) <= tol:
            return f'<td class="cell-low">{f} ▲</td>'  # High = BEARISH = cervena
        if lo is not None and abs(v - lo) <= tol:
            return f'<td class="cell-high">{f} ▼</td>'  # Low = BULLISH = zelena
        c = "cell-pos" if v >= 0 else "cell-neg"
        return f'<td class="{c}">{f}</td>'

    cells = ""
    for d in last6_dates:
        match = sub[sub["Report_Date"] == d]
        if not match.empty:
            cells += td(float(match["Net"].iloc[0]), hi52, lo52)
        else:
            cells += '<td style="color:#3a4038">—</td>'

    # Podbarvení řádku jen pokud je aktuální hodnota na 52W High nebo Low
    # High = zelená jen pokud je hodnota nejvyšší za rok (bez ohledu na znaménko)
    # Low = červená jen pokud je hodnota nejnižší za rok
    row_bg = ""
    if lo52 is not None and abs(last_n - lo52) <= tol:
        row_bg = "background:#0d2010;"  # zelena = Low = BULLISH
    elif hi52 is not None and abs(last_n - hi52) <= tol:
        row_bg = "background:#1a0a08;"  # cervena = High = BEARISH

    html_rows += f"""<tr style="{row_bg}">
  <td>{r["name"]}</td>
  <td class="cell-low">{fmt_v(hi52)}</td>
  <td class="cell-high">{fmt_v(lo52)}</td>
  {cells}
</tr>"""

html_table = f"""
<table class="barchart-table">
<thead><tr>
  <th>Komodita</th>
  <th>52W High</th>
  <th>52W Low</th>
  {th_dates}
</tr></thead>
<tbody>{html_rows}</tbody>
</table>
<div style='margin-top:0.5rem;font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;
  display:flex;gap:20px'>
  <span><span style='color:#7ed957'>▼ 52W Low = BULLISH (spekulanti přeprodáni)</span></span>
  <span><span style='color:#e05a3a'>▲ 52W High = BEARISH (spekulanti překoupeni)</span></span>
  <span>Net = Non-Commercial Long − Short · Supplemental CIT</span>
</div>
<div style='margin-bottom:1.5rem'></div>
"""
st.markdown(html_table, unsafe_allow_html=True)


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

        sub    = det["data"].reset_index(drop=True).copy()
        idx_s  = det["idx_series"].reset_index(drop=True).copy()
        cutoff = sub["Report_Date"].max() - timedelta(weeks=lookback)
        mask   = sub["Report_Date"] >= cutoff
        sp     = sub[mask].reset_index(drop=True).copy()
        ip     = idx_s[mask].reset_index(drop=True).copy()

        # Použij datetime přímo — ne string formát
        dates   = sp["Report_Date"].tolist()
        net_v   = sp["Net"].tolist()
        long_v  = sp["NonComm_Long"].tolist()
        short_n = [-v for v in sp["NonComm_Short"].tolist()]
        idx_v   = ip.tolist()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.5, 0.5], vertical_spacing=0.08,
            subplot_titles=["Net pozice Non-Commercial (Long − Short)",
                            f"COT Index · lookback {lb_label}"])

        # Graf 1 — Net pozice jako bary
        fig.add_trace(go.Bar(x=dates, y=net_v,
            marker_color=["#7ed957" if v >= 0 else "#e05a3a" for v in net_v],
            name="Net", hovertemplate="%{x|%d.%m.%Y}<br>Net: %{y:,.0f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=long_v, mode="lines", name="Long",
            line=dict(color="#7ed957", width=1.5),
            hovertemplate="%{x|%d.%m.%Y}<br>Long: %{y:,.0f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=short_n, mode="lines", name="Short (neg.)",
            line=dict(color="#e05a3a", width=1.5),
            hovertemplate="%{x|%d.%m.%Y}<br>Short: %{y:,.0f}<extra></extra>"), row=1, col=1)

        # Graf 2 — COT Index čárový
        fig.add_hrect(y0=80, y1=100, fillcolor="rgba(224,90,58,0.10)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=0,  y1=20,  fillcolor="rgba(126,217,87,0.10)", line_width=0, row=2, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="#e05a3a", line_width=1.0, row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#7ed957", line_width=1.0, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot",  line_color="#3a4038", line_width=0.8, row=2, col=1)

        # Barevný gradient čáry podle hodnoty — rozdělíme na bull/neu/bear segmenty
        fig.add_trace(go.Scatter(x=dates, y=idx_v, mode="lines",
            line=dict(color="#c8f5a0", width=2.5),
            name="COT Index",
            hovertemplate="%{x|%d.%m.%Y}<br>Index: %{y:.1f}<extra></extra>"), row=2, col=1)

        # Neviditelné body na 0 a 100 aby osa byla vždy celá
        fig.add_trace(go.Scatter(x=[dates[0], dates[0]], y=[0, 100], mode="markers",
            marker=dict(color="rgba(0,0,0,0)", size=1),
            showlegend=False, hoverinfo="skip"), row=2, col=1)
        # Aktuální hodnota jako bod
        cc = "#7ed957" if idx_v[-1] <= 20 else ("#e05a3a" if idx_v[-1] >= 80 else "#c8f5a0")
        fig.add_trace(go.Scatter(x=[dates[-1]], y=[idx_v[-1]], mode="markers",
            marker=dict(color=cc, size=10, line=dict(color="#0d0f0e", width=2)),
            name=f"Aktuálně: {idx_v[-1]:.0f}",
            hovertemplate=f"%{{x|%d.%m.%Y}}<br>Index: {idx_v[-1]:.1f}<extra></extra>"), row=2, col=1)
        ax = dict(showgrid=True, gridcolor="#131714", color="#3a4038",
                  tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038"),
                  zeroline=True, zerolinecolor="#1f2420")
        fig.update_layout(height=540, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d0f0e",
            margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
            legend=dict(font=dict(family="IBM Plex Mono", size=10, color="#5a6358"),
                        bgcolor="rgba(0,0,0,0)", orientation="h", y=1.02),
            hoverlabel=dict(bgcolor="#131714", bordercolor="#2a2e2b",
                            font=dict(family="IBM Plex Mono", size=11, color="#e8e4dc")),
            yaxis2=dict(range=[0, 100], fixedrange=True,
                tickvals=[0, 20, 50, 80, 100],
                ticktext=["0", "20 ▲", "50", "80 ▼", "100"],
                showgrid=True, gridcolor="#131714", color="#3a4038",
                tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038")))
        fig.update_xaxes(**ax)
        fig.update_yaxes(**ax)
        # Přepíše row=2 po obecném nastavení — musí být jako poslední
        fig.update_yaxes(range=[0, 100], fixedrange=True,
            tickvals=[0, 20, 50, 80, 100],
            ticktext=["0", "20 ▲", "50", "80 ▼", "100"],
            row=2, col=1)
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


# ── SEASONAL TENDENCIES ───────────────────────────────────────────────────────
st.markdown('<div class="section-title" style="margin-top:2rem">Seasonal Tendencies · průměrný výnos v průběhu roku</div>', unsafe_allow_html=True)

SEASONAL_TICKERS = {
    "Pšenice SRW":   "ZW=F",
    "Pšenice HRW":   "KE=F",
    "Kukuřice":      "ZC=F",
    "Sója":          "ZS=F",
    "Sójový olej":   "ZL=F",
    "Sójový šrot":   "ZM=F",
    "Živý skot":     "LE=F",
    "Vepřové":       "HE=F",
    "Káva":          "KC=F",
    "Kakao":         "CC=F",
    "Cukr č.11":     "SB=F",
    "Bavlna č.2":    "CT=F",
    "Feeder Cattle": "GF=F",
}

SEASONAL_YEARS  = [2, 5, 10, 15, 20]
SEASONAL_COLORS = {2: "#e05a3a", 5: "#f0a030", 10: "#c8f5a0", 15: "#7ed957", 20: "#3a9e55"}

@st.cache_data(ttl=3600 * 12, show_spinner=False)
def fetch_seasonal(ticker, years):
    try:
        import yfinance as yf
        df = yf.download(ticker, period=f"{years + 1}y", interval="1d",
                         progress=False, auto_adjust=True)
        if df.empty:
            return None
        close = df["Close"].copy()
        close.index = pd.to_datetime(close.index)
        pct = close.pct_change() * 100
        doy  = close.index.dayofyear
        year = close.index.year
        tmp = pd.DataFrame({"pct": pct.values, "doy": doy, "year": year},
                           index=close.index)
        cutoff_year = close.index[-1].year - years
        tmp = tmp[tmp["year"] > cutoff_year]
        seasonal = tmp.groupby("doy")["pct"].mean().reset_index()
        seasonal["cumsum"] = seasonal["pct"].cumsum()
        mn, mx = seasonal["cumsum"].min(), seasonal["cumsum"].max()
        seasonal["norm"] = 50.0 if mx == mn else (seasonal["cumsum"] - mn) / (mx - mn) * 100
        return seasonal
    except Exception:
        return None

sc1, sc2 = st.columns([2, 7])
with sc1:
    sel_name = st.selectbox(
        "Komodita",
        list(SEASONAL_TICKERS.keys()),
        key="seasonal_commodity",
        label_visibility="collapsed",
    )

ticker_s = SEASONAL_TICKERS[sel_name]

with st.spinner(f"Načítám sezónní data pro {sel_name}…"):
    seasonal_data = {y: fetch_seasonal(ticker_s, y) for y in SEASONAL_YEARS}

current_year = datetime.now().year
current_doy  = datetime.now().timetuple().tm_yday

doy_to_date = {}
for doy in range(1, 367):
    try:
        doy_to_date[doy] = datetime(current_year, 1, 1) + timedelta(days=doy - 1)
    except Exception:
        pass

fig_s = go.Figure()

for y in SEASONAL_YEARS:
    data = seasonal_data.get(y)
    if data is None or data.empty:
        continue
    xs = [doy_to_date[int(d)] for d in data["doy"] if int(d) in doy_to_date]
    ys = data["norm"].tolist()[:len(xs)]
    fig_s.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        name=f"{y} let",
        line=dict(color=SEASONAL_COLORS[y], width=2.5 if y == 5 else 1.5),
        opacity=0.9,
        hovertemplate=f"{y}r · %{{x|%d.%m}}: %{{y:.1f}}<extra></extra>",
    ))

today_dt = doy_to_date.get(current_doy)
if today_dt:
    fig_s.add_vline(
        x=today_dt.timestamp() * 1000,
        line_dash="dash", line_color="#5a6358", line_width=1,
    )
    fig_s.add_annotation(
        x=today_dt, y=105,
        text="dnes", showarrow=False,
        font=dict(family="IBM Plex Mono", size=10, color="#5a6358"),
        xanchor="center",
    )

fig_s.add_hrect(y0=80, y1=100, fillcolor="rgba(224,90,58,0.05)", line_width=0)
fig_s.add_hrect(y0=0,  y1=20,  fillcolor="rgba(126,217,87,0.05)", line_width=0)

fig_s.update_layout(
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d0f0e",
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    legend=dict(
        font=dict(family="IBM Plex Mono", size=10, color="#5a6358"),
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
        orientation="h", y=1.05,
    ),
    hoverlabel=dict(
        bgcolor="#131714", bordercolor="#2a2e2b",
        font=dict(family="IBM Plex Mono", size=11, color="#e8e4dc"),
    ),
    xaxis=dict(
        showgrid=True, gridcolor="#131714", color="#3a4038",
        tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038"),
        tickformat="%b", dtick="M1", ticklabelmode="period",
        zeroline=False,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#131714", color="#3a4038",
        tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038"),
        range=[-5, 110],
        tickvals=[0, 20, 50, 80, 100],
        ticktext=["0", "20", "50", "80", "100"],
        zeroline=False,
    ),
)

st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

st.markdown(
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;"
    "display:flex;gap:20px;flex-wrap:wrap;margin-top:0.25rem'>"
    "<span>Normalizováno 0–100 · kumulativní průměrný výnos v průběhu roku</span>"
    "<span>Zdroj: yfinance · nearest futures · svislá linka = dnes</span>"
    "</div>",
    unsafe_allow_html=True,
)


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:2.5rem;padding-top:1rem;border-top:1px solid #1a1e1b;
  font-family:IBM Plex Mono,monospace;font-size:10px;color:#2a2e2b;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px'>
  <span>Zdroj: CFTC Commodity Index Trader Supplement · aktualizuj každý pátek přes update_data.py</span>
  <span>COT Index = (net − min) / (max − min) × 100 · Non-Commercial = Large Speculators</span>
</div>
""", unsafe_allow_html=True)

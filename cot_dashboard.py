import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import zipfile
import io
from datetime import datetime, timedelta

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

.dash-header {
    display: flex; align-items: baseline; justify-content: space-between;
    border-bottom: 1px solid #2a2e2b; padding-bottom: 1rem; margin-bottom: 1.5rem;
}
.dash-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 500;
    color: #c8f5a0; letter-spacing: 0.08em; text-transform: uppercase;
}
.dash-sub { font-size: 12px; color: #5a6358; font-family: 'IBM Plex Mono', monospace; letter-spacing: 0.06em; }

.metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.5rem; }
.metric-card { background: #131714; border: 1px solid #1f2420; border-radius: 8px; padding: 14px 16px; }
.metric-label { font-size: 10px; font-family: 'IBM Plex Mono', monospace; color: #4a5248;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.metric-value { font-size: 22px; font-weight: 500; font-family: 'IBM Plex Mono', monospace; color: #e8e4dc; }
.metric-sub { font-size: 11px; color: #4a5248; margin-top: 2px; }
.metric-pos { color: #7ed957; }
.metric-neg { color: #e05a3a; }

.section-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.12em; color: #3a4038; margin: 1.5rem 0 0.75rem 0;
    border-bottom: 1px solid #1a1e1b; padding-bottom: 6px;
}

.com-name { font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; font-size: 13px; color: #e8e4dc; }
.com-ticker { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #3a4038; margin-top: 2px; }

.signal-bull { background: #0d2010; color: #7ed957; padding: 3px 10px; border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 500; }
.signal-bear { background: #2a0d0a; color: #e05a3a; padding: 3px 10px; border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 500; }
.signal-neu { background: #1a1e1b; color: #5a6358; padding: 3px 10px; border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 500; }

.pos { color: #7ed957; font-family: 'IBM Plex Mono', monospace; }
.neg { color: #e05a3a; font-family: 'IBM Plex Mono', monospace; }
.neu { color: #5a6358; font-family: 'IBM Plex Mono', monospace; }

.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    border: 1px solid #2a2e2b !important; background: transparent !important;
    color: #5a6358 !important; border-radius: 4px !important; padding: 4px 14px !important;
}
.stButton > button:hover { border-color: #c8f5a0 !important; color: #c8f5a0 !important; background: #0d150a !important; }

.stSelectbox > div > div {
    background: #131714 !important; border: 1px solid #1f2420 !important;
    color: #e8e4dc !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important; border-radius: 6px !important;
}
.stRadio > div { gap: 8px; }
.stRadio label { font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; color: #5a6358 !important; }

div[data-testid="stHorizontalBlock"] { gap: 0px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ── KOMODITY ze Supplemental reportu ────────────────────────────────────────
SUPPLEMENTAL_COMMODITIES = {
    "WHEAT-SRW":        {"name": "Pšenice SRW",    "search": "WHEAT-SRW"},
    "WHEAT-HRW":        {"name": "Pšenice HRW",    "search": "WHEAT-HRW"},
    "CORN":             {"name": "Kukuřice",        "search": "CORN"},
    "SOYBEANS":         {"name": "Sója",            "search": "SOYBEANS"},
    "SOYBEAN OIL":      {"name": "Sójový olej",     "search": "SOYBEAN OIL"},
    "SOYBEAN MEAL":     {"name": "Sójový šrot",     "search": "SOYBEAN MEAL"},
    "LIVE CATTLE":      {"name": "Živý skot",       "search": "LIVE CATTLE"},
    "LEAN HOGS":        {"name": "Vepřové",         "search": "LEAN HOGS"},
    "COFFEE":           {"name": "Káva",            "search": "COFFEE"},
    "COCOA":            {"name": "Kakao",           "search": "COCOA"},
    "SUGAR NO. 11":     {"name": "Cukr č.11",       "search": "SUGAR NO. 11"},
    "COTTON NO. 2":     {"name": "Bavlna č.2",      "search": "COTTON NO. 2"},
}

# ── STAŽENÍ DAT Z CFTC ───────────────────────────────────────────────────────
@st.cache_data(ttl=3600 * 6, show_spinner=False)
def fetch_cot_supplemental():
    """Stáhne historická Supplemental COT data z CFTC (combined ZIP)."""
    url = "https://www.cftc.gov/files/dea/history/com_disagg_xls_2006_2016.zip"
    urls = [
        "https://www.cftc.gov/files/dea/history/com_disagg_txt_2006_2016.zip",
        "https://www.cftc.gov/files/dea/history/com_disagg_txt_2017_2024.zip",
        "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2025.zip",
    ]
    # Supplemental report URL
    supp_urls = [
        "https://www.cftc.gov/files/dea/history/com_sup_txt_2006_2016.zip",
        "https://www.cftc.gov/files/dea/history/com_sup_txt_2017_2024.zip",
        "https://www.cftc.gov/files/dea/history/fut_sup_txt_2025.zip",
    ]

    dfs = []
    for url in supp_urls:
        try:
            r = requests.get(url, timeout=30)
            if r.status_code != 200:
                continue
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for fname in z.namelist():
                    if fname.endswith(".txt") or fname.endswith(".csv"):
                        with z.open(fname) as f:
                            df = pd.read_csv(f, low_memory=False)
                            dfs.append(df)
        except Exception:
            continue

    if not dfs:
        return None

    combined = pd.concat(dfs, ignore_index=True)
    combined.columns = [c.strip() for c in combined.columns]

    # Standardizace názvů sloupců
    col_map = {}
    for c in combined.columns:
        cl = c.lower()
        if "market" in cl and "name" in cl:
            col_map[c] = "market_name"
        elif "report" in cl and "date" in cl:
            col_map[c] = "report_date"
        elif "noncomm" in cl and "long" in cl and "all" in cl:
            col_map[c] = "nc_long"
        elif "noncomm" in cl and "short" in cl and "all" in cl:
            col_map[c] = "nc_short"
        elif "noncomm" in cl and "spread" in cl:
            col_map[c] = "nc_spread"
        elif "open interest" in cl or "open_interest" in cl:
            col_map[c] = "open_interest"

    combined = combined.rename(columns=col_map)

    needed = ["market_name", "report_date", "nc_long", "nc_short"]
    for n in needed:
        if n not in combined.columns:
            return None

    combined["report_date"] = pd.to_datetime(combined["report_date"], errors="coerce")
    combined = combined.dropna(subset=["report_date", "nc_long", "nc_short"])
    combined["nc_long"]  = pd.to_numeric(combined["nc_long"],  errors="coerce")
    combined["nc_short"] = pd.to_numeric(combined["nc_short"], errors="coerce")
    combined["net"]      = combined["nc_long"] - combined["nc_short"]
    combined["market_name_upper"] = combined["market_name"].str.upper().str.strip()

    return combined.sort_values("report_date")


def get_commodity_data(df, search_key):
    """Filtruje data pro konkrétní komoditu."""
    mask = df["market_name_upper"].str.contains(search_key.upper(), na=False)
    sub = df[mask].copy()
    sub = sub.drop_duplicates(subset=["report_date"]).sort_values("report_date")
    return sub


def cot_index(series, lookback_weeks):
    """Vypočítá COT Index (0–100) pro každý bod v sérii."""
    result = pd.Series(index=series.index, dtype=float)
    for i in range(len(series)):
        start = max(0, i - lookback_weeks + 1)
        window = series.iloc[start:i+1]
        mn, mx = window.min(), window.max()
        if mx == mn:
            result.iloc[i] = 50.0
        else:
            result.iloc[i] = (series.iloc[i] - mn) / (mx - mn) * 100
    return result


def signal_html(idx_val):
    if idx_val >= 80:
        return '<span class="signal-bear">▼ BEARISH</span>'
    elif idx_val <= 20:
        return '<span class="signal-bull">▲ BULLISH</span>'
    else:
        return '<span class="signal-neu">◆ NEUTRÁL</span>'


def fmt_net(v):
    if abs(v) >= 1000:
        return f"{v/1000:+.1f}k"
    return f"{v:+.0f}"


# ── HEADER ───────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
st.markdown(f"""
<div class="dash-header">
  <div class="dash-title">📊 COT Supplemental · Non-Commercial</div>
  <div class="dash-sub">CFTC · Supplemental Report · {now_str}</div>
</div>
""", unsafe_allow_html=True)

# ── NAČTENÍ DAT ──────────────────────────────────────────────────────────────
with st.spinner("Načítám Supplemental COT data z CFTC…"):
    df_all = fetch_cot_supplemental()

if df_all is None:
    st.error("Nepodařilo se načíst data z CFTC. Zkontroluj připojení k internetu.")
    st.stop()

last_date = df_all["report_date"].max()
st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:11px;color:#3a4038;margin-bottom:1.5rem'>Poslední report: {last_date.strftime('%d.%m.%Y')} · {len(df_all):,} záznamů načteno</div>", unsafe_allow_html=True)

# ── LOOKBACK VOLBA ───────────────────────────────────────────────────────────
col_lb1, col_lb2, col_lb3, col_lb4 = st.columns([1,1,1,6])
with col_lb1:
    lb1 = st.button("1 rok")
with col_lb2:
    lb2 = st.button("3 roky")
with col_lb3:
    lb3 = st.button("5 let")

if lb1:
    st.session_state["lookback"] = 52
elif lb2:
    st.session_state["lookback"] = 156
elif lb3:
    st.session_state["lookback"] = 260

lookback = st.session_state.get("lookback", 156)
lb_label = {52: "1 rok", 156: "3 roky", 260: "5 let"}.get(lookback, "3 roky")

st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;margin-bottom:1rem'>COT Index lookback: <span style='color:#c8f5a0'>{lb_label} ({lookback} týdnů)</span></div>", unsafe_allow_html=True)

# ── VÝPOČET PRO VŠECHNY KOMODITY ─────────────────────────────────────────────
summary = []
for key, meta in SUPPLEMENTAL_COMMODITIES.items():
    sub = get_commodity_data(df_all, meta["search"])
    if sub.empty or len(sub) < 10:
        continue
    idx_series = cot_index(sub["net"], lookback)
    latest_idx   = idx_series.iloc[-1]
    latest_net   = sub["net"].iloc[-1]
    prev_net     = sub["net"].iloc[-2] if len(sub) > 1 else latest_net
    weekly_delta = latest_net - prev_net
    latest_long  = sub["nc_long"].iloc[-1]
    latest_short = sub["nc_short"].iloc[-1]
    summary.append({
        "key": key,
        "name": meta["name"],
        "net": latest_net,
        "delta": weekly_delta,
        "long": latest_long,
        "short": latest_short,
        "cot_index": latest_idx,
        "data": sub,
        "idx_series": idx_series,
    })

if not summary:
    st.error("Nenalezena žádná data pro Supplemental komodity. CFTC mohl změnit formát souboru.")
    st.stop()

# ── SUMMARY CARDS ─────────────────────────────────────────────────────────────
bulls = sum(1 for r in summary if r["cot_index"] <= 20)
bears = sum(1 for r in summary if r["cot_index"] >= 80)
neuts = sum(1 for r in summary if 20 < r["cot_index"] < 80)
top_bull = min(summary, key=lambda x: x["cot_index"])
top_bear = max(summary, key=lambda x: x["cot_index"])

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Komodit celkem</div>
    <div class="metric-value">{len(summary)}</div>
    <div class="metric-sub">Supplemental agri</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Signály</div>
    <div class="metric-value"><span class="metric-pos">{bulls}▲</span> <span style="color:#3a4038;font-size:16px">{neuts}◆</span> <span class="metric-neg">{bears}▼</span></div>
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

# ── PŘEHLEDOVÁ TABULKA ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Přehled · Non-Commercial pozice</div>', unsafe_allow_html=True)

sorted_summary = sorted(summary, key=lambda x: x["cot_index"])

for r in sorted_summary:
    delta_cls = "pos" if r["delta"] >= 0 else "neg"
    delta_arrow = "▲" if r["delta"] >= 0 else "▼"
    net_cls = "pos" if r["net"] >= 0 else "neg"
    idx_color = "#7ed957" if r["cot_index"] <= 20 else ("#e05a3a" if r["cot_index"] >= 80 else "#c8c4bc")

    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.2, 1.4, 1.4, 1.3, 1.3, 1.2, 0.9])

    with c1:
        st.markdown(f"""
        <div style="padding:9px 0">
          <div class="com-name">{r['name']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px;color:#5a6358'>Long: <span style='color:#e8e4dc'>{r['long']/1000:.1f}k</span></div>", unsafe_allow_html=True)

    with c3:
        st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px;color:#5a6358'>Short: <span style='color:#e8e4dc'>{r['short']/1000:.1f}k</span></div>", unsafe_allow_html=True)

    with c4:
        st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:13px' class='{net_cls}'>Net: {fmt_net(r['net'])}</div>", unsafe_allow_html=True)

    with c5:
        st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:12px' class='{delta_cls}'>{delta_arrow} {fmt_net(r['delta'])}/t</div>", unsafe_allow_html=True)

    with c6:
        st.markdown(f"<div style='padding:9px 0;font-family:IBM Plex Mono,monospace;font-size:14px;font-weight:500;color:{idx_color}'>IDX {r['cot_index']:.0f}</div>", unsafe_allow_html=True)

    with c7:
        if st.button("Graf", key=f"det_{r['key']}"):
            st.session_state["cot_detail"] = r["key"]

    st.markdown("<div style='border-bottom:1px solid #131714'></div>", unsafe_allow_html=True)

# ── LEGENDA ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:1rem;font-family:IBM Plex Mono,monospace;font-size:10px;color:#3a4038;display:flex;gap:20px'>
  <span><span style='color:#7ed957'>▲ IDX 0–20</span> Bullish (přeprodaná spec. pozice)</span>
  <span><span style='color:#e05a3a'>▼ IDX 80–100</span> Bearish (překoupená spec. pozice)</span>
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

        dcol1, dcol2 = st.columns([8, 1])
        with dcol2:
            if st.button("✕ Zavřít", key="close_detail"):
                del st.session_state["cot_detail"]
                st.rerun()

        sub = det["data"].copy()
        idx_s = det["idx_series"].copy()

        # Omezení na lookback období pro graf
        cutoff = sub["report_date"].max() - timedelta(weeks=lookback)
        sub_plot = sub[sub["report_date"] >= cutoff]
        idx_plot = idx_s[sub["report_date"] >= cutoff]

        dates = sub_plot["report_date"].dt.strftime("%d.%m.%y").tolist()
        net_vals = sub_plot["net"].tolist()
        long_vals = sub_plot["nc_long"].tolist()
        short_vals = sub_plot["nc_short"].tolist()
        idx_vals = idx_plot.tolist()

        # Barvy pro net (pos/neg)
        bar_colors = ["#7ed957" if v >= 0 else "#e05a3a" for v in net_vals]

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.55, 0.45],
            vertical_spacing=0.06,
            subplot_titles=["Net pozice Non-Commercial (Long − Short)", f"COT Index · lookback {lb_label}"]
        )

        # Graf 1: Net pozice jako bary + long/short jako linky
        fig.add_trace(go.Bar(
            x=dates, y=net_vals,
            marker_color=bar_colors,
            name="Net pozice",
            hovertemplate="%{x}<br>Net: %{y:,.0f}<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=long_vals,
            mode="lines", name="Long",
            line=dict(color="#7ed957", width=1, dash="dot"),
            hovertemplate="%{x}<br>Long: %{y:,.0f}<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=[-v for v in short_vals],
            mode="lines", name="Short (neg)",
            line=dict(color="#e05a3a", width=1, dash="dot"),
            hovertemplate="%{x}<br>Short: %{y:,.0f}<extra></extra>",
        ), row=1, col=1)

        # Graf 2: COT Index
        idx_colors_line = ["#7ed957" if v <= 20 else ("#e05a3a" if v >= 80 else "#c8c4bc") for v in idx_vals]

        fig.add_hrect(y0=80, y1=100, fillcolor="rgba(224,90,58,0.08)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=0, y1=20, fillcolor="rgba(126,217,87,0.08)", line_width=0, row=2, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="#e05a3a", line_width=0.8, row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#7ed957", line_width=0.8, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#2a2e2b", line_width=0.6, row=2, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=idx_vals,
            mode="lines",
            line=dict(color="#c8f5a0", width=2),
            fill="tozeroy",
            fillcolor="rgba(200,245,160,0.06)",
            name="COT Index",
            hovertemplate="%{x}<br>Index: %{y:.1f}<extra></extra>",
        ), row=2, col=1)

        # Aktuální hodnota jako bod
        fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[idx_vals[-1]],
            mode="markers",
            marker=dict(
                color="#7ed957" if idx_vals[-1] <= 20 else ("#e05a3a" if idx_vals[-1] >= 80 else "#c8f5a0"),
                size=8, line=dict(color="#0d0f0e", width=2)
            ),
            name=f"Aktuální: {idx_vals[-1]:.0f}",
            hovertemplate=f"Aktuální COT Index: {idx_vals[-1]:.1f}<extra></extra>",
        ), row=2, col=1)

        axis_style = dict(
            showgrid=True, gridcolor="#131714",
            color="#3a4038",
            tickfont=dict(family="IBM Plex Mono", size=10, color="#3a4038"),
            zeroline=True, zerolinecolor="#1f2420", zerolinewidth=1,
        )

        fig.update_layout(
            height=560,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0d0f0e",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(
                font=dict(family="IBM Plex Mono", size=10, color="#5a6358"),
                bgcolor="rgba(0,0,0,0)", borderwidth=0,
                orientation="h", y=1.02,
            ),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#131714", bordercolor="#2a2e2b",
                font=dict(family="IBM Plex Mono", size=11, color="#e8e4dc"),
            ),
        )
        fig.update_xaxes(**axis_style)
        fig.update_yaxes(**axis_style)
        fig.update_yaxes(range=[0, 100], row=2, col=1,
                         tickvals=[0, 20, 50, 80, 100],
                         ticktext=["0", "20 ▲bull", "50", "80 ▼bear", "100"])
        fig.update_annotations(font=dict(family="IBM Plex Mono", size=11, color="#5a6358"))

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Stats pod grafem
        s1, s2, s3, s4 = st.columns(4)
        idx_now = idx_vals[-1]
        idx_prev = idx_vals[-2] if len(idx_vals) > 1 else idx_now
        net_now = net_vals[-1]
        net_52w_min = min(net_vals[-52:]) if len(net_vals) >= 52 else min(net_vals)
        net_52w_max = max(net_vals[-52:]) if len(net_vals) >= 52 else max(net_vals)

        for col, label, val, sub_val in [
            (s1, "COT Index aktuálně", f"{idx_now:.1f}", f"předchozí: {idx_prev:.1f}"),
            (s2, "Net pozice",         f"{net_now/1000:+.1f}k", f"kontraktů"),
            (s3, "52w Net min/max",    f"{net_52w_min/1000:.0f}k / {net_52w_max/1000:.0f}k", "roční rozsah"),
            (s4, "Signál",             "BULLISH" if idx_now<=20 else ("BEARISH" if idx_now>=80 else "NEUTRÁL"),
                                       f"lookback {lb_label}"),
        ]:
            with col:
                val_color = "#7ed957" if (label=="Signál" and idx_now<=20) else ("#e05a3a" if (label=="Signál" and idx_now>=80) else "#e8e4dc")
                st.markdown(f"""
                <div class="metric-card" style='margin-top:8px'>
                  <div class="metric-label">{label}</div>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:15px;color:{val_color}'>{val}</div>
                  <div class="metric-sub">{sub_val}</div>
                </div>""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:2.5rem;padding-top:1rem;border-top:1px solid #1a1e1b;
  font-family:IBM Plex Mono,monospace;font-size:10px;color:#2a2e2b;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px'>
  <span>Zdroj: CFTC Supplemental COT Report · cftc.gov · každý pátek ~15:30 EST</span>
  <span>Non-Commercial = Large Speculators (managed money, hedge fondy, CTA)</span>
  <span>Cache: 6h · COT Index = (net − min) / (max − min) × 100</span>
</div>
""", unsafe_allow_html=True)

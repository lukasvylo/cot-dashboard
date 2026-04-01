"""
update_data.py — spusť lokálně každý pátek po 21:30 CET (15:30 EST)
Stáhne Supplemental CIT data z CFTC a uloží jako data/cot_supplemental.csv

Použití:
    pip install requests pandas
    python update_data.py
"""

import requests
import zipfile
import io
import pandas as pd
from datetime import datetime
from pathlib import Path

CURRENT_YEAR = datetime.now().year

CIT_URLS = [
    "https://www.cftc.gov/files/dea/history/dea_cit_txt_2006_2016.zip",
] + [
    f"https://www.cftc.gov/files/dea/history/dea_cit_txt_{y}.zip"
    for y in range(CURRENT_YEAR, 2016, -1)
]

def download_and_parse(url):
    print(f"  Stahuji: {url}")
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"  → HTTP {r.status_code}, přeskakuji")
            return None
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for fname in z.namelist():
                if fname.lower().endswith((".txt", ".csv")):
                    with z.open(fname) as f:
                        return pd.read_csv(f, low_memory=False)
    except Exception as e:
        print(f"  → Chyba: {e}")
    return None

def normalize(df):
    if df is None or df.empty:
        return None
    col_map = {}
    for c in df.columns:
        low = c.strip().lower()
        if "market" in low and "exchange" in low:
            col_map[c] = "Market_and_Exchange_Names"
        elif "report_date" in low and "yyyy" in low:
            col_map[c] = "Report_Date"
        elif "noncomm" in low and "long" in low and "all" in low:
            col_map[c] = "NonComm_Long"
        elif "noncomm" in low and "short" in low and "all" in low:
            col_map[c] = "NonComm_Short"
        elif "open_interest" in low and "all" in low:
            col_map[c] = "Open_Interest"
    df = df.rename(columns=col_map)
    required = ["Market_and_Exchange_Names", "Report_Date", "NonComm_Long", "NonComm_Short"]
    if not all(c in df.columns for c in required):
        print("  → Chybí sloupce, přeskakuji")
        return None
    df["Report_Date"] = pd.to_datetime(df["Report_Date"], errors="coerce")
    df["NonComm_Long"]  = pd.to_numeric(df["NonComm_Long"],  errors="coerce")
    df["NonComm_Short"] = pd.to_numeric(df["NonComm_Short"], errors="coerce")
    df["Net"] = df["NonComm_Long"] - df["NonComm_Short"]
    return df[required + ["Net", "Open_Interest"]].dropna(subset=["Report_Date", "NonComm_Long", "NonComm_Short"])

def main():
    print(f"\n=== COT Supplemental Update — {datetime.now().strftime('%d.%m.%Y %H:%M')} ===\n")
    dfs = []
    for url in CIT_URLS:
        raw = download_and_parse(url)
        norm = normalize(raw)
        if norm is not None and not norm.empty:
            dfs.append(norm)
            print(f"  → OK, {len(norm)} řádků")

    if not dfs:
        print("\n❌ Žádná data nestažena.")
        return

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Market_and_Exchange_Names", "Report_Date"])
    combined = combined.sort_values("Report_Date").reset_index(drop=True)

    # Uloží do složky data/
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "cot_supplemental.csv"
    combined.to_csv(out_path, index=False)

    print(f"\n✅ Uloženo: {out_path}")
    print(f"   Celkem záznamů: {len(combined):,}")
    print(f"   Rozsah dat: {combined['Report_Date'].min().date()} → {combined['Report_Date'].max().date()}")
    print(f"\n→ Nahraj data/cot_supplemental.csv na GitHub (git add data/cot_supplemental.csv && git commit -m 'update COT' && git push)")

if __name__ == "__main__":
    main()

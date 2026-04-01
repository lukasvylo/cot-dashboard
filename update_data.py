"""
update_data.py — stáhne Supplemental CIT data z CFTC a uloží jako data/cot_supplemental.csv
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
                        df = pd.read_csv(f, low_memory=False)
                        return df
    except Exception as e:
        print(f"  → Chyba: {e}")
    return None

def find_column(columns, *keywords):
    """Najde sloupec který obsahuje všechna klíčová slova (case-insensitive)."""
    for col in columns:
        col_low = col.strip().lower()
        if all(kw.lower() in col_low for kw in keywords):
            return col
    return None

def normalize(df):
    if df is None or df.empty:
        return None

    cols = df.columns.tolist()

    # Debug — vypíše všechny sloupce pro diagnostiku
    print(f"  → Sloupce v souboru: {cols[:10]}...")

    # Flexibilní hledání sloupců
    col_market = find_column(cols, "market")
    col_date   = find_column(cols, "date")
    col_long   = find_column(cols, "noncomm", "long", "all")
    col_short  = find_column(cols, "noncomm", "short", "all")

    # Fallback pro datum
    if not col_date:
        col_date = find_column(cols, "report", "date")
    if not col_date:
        col_date = find_column(cols, "yyyy")

    # Fallback pro long/short — zkus bez "all"
    if not col_long:
        col_long = find_column(cols, "noncomm", "long")
    if not col_short:
        col_short = find_column(cols, "noncomm", "short")

    print(f"  → Nalezené sloupce: market={col_market}, date={col_date}, long={col_long}, short={col_short}")

    if not all([col_market, col_date, col_long, col_short]):
        print(f"  → Chybí sloupce, přeskakuji")
        return None

    result = pd.DataFrame({
        "Market_and_Exchange_Names": df[col_market],
        "Report_Date":               df[col_date],
        "NonComm_Long":              pd.to_numeric(df[col_long],  errors="coerce"),
        "NonComm_Short":             pd.to_numeric(df[col_short], errors="coerce"),
    })

    # Open Interest — volitelný
    col_oi = find_column(cols, "open", "interest", "all")
    if not col_oi:
        col_oi = find_column(cols, "open_interest")
    if col_oi:
        result["Open_Interest"] = pd.to_numeric(df[col_oi], errors="coerce")
    else:
        result["Open_Interest"] = None

    result["Report_Date"] = pd.to_datetime(result["Report_Date"], errors="coerce")
    result["Net"] = result["NonComm_Long"] - result["NonComm_Short"]

    result = result.dropna(subset=["Report_Date", "NonComm_Long", "NonComm_Short"])
    return result

def main():
    print(f"\n=== COT Supplemental Update — {datetime.now().strftime('%d.%m.%Y %H:%M')} ===\n")
    dfs = []

    for url in CIT_URLS:
        raw = download_and_parse(url)
        norm = normalize(raw)
        if norm is not None and not norm.empty:
            dfs.append(norm)
            print(f"  → OK, {len(norm)} řádků\n")
        else:
            print()

    if not dfs:
        print("\n❌ Žádná data nestažena.")
        raise SystemExit(1)

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Market_and_Exchange_Names", "Report_Date"])
    combined = combined.sort_values("Report_Date").reset_index(drop=True)

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "cot_supplemental.csv"
    combined.to_csv(out_path, index=False)

    print(f"\n✅ Uloženo: {out_path}")
    print(f"   Celkem záznamů: {len(combined):,}")
    print(f"   Rozsah dat: {combined['Report_Date'].min().date()} → {combined['Report_Date'].max().date()}")

if __name__ == "__main__":
    main()

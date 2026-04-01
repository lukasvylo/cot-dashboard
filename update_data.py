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

# Přesné názvy sloupců z CFTC CIT Supplemental souboru
# (ověřeno z logu GitHub Actions)
# Datum: 'As_of_Date_In_Form_YYYY-MM-DD' nebo 'As of Date In Form YYYY-MM-DD'
# Long:  'NComm_Positions_Long_All_NoCIT' nebo 'NComm Positions Long All NoCIT'
# Short: 'NComm_Positions_Short_All_NoCIT' nebo 'NComm Positions Short All NoCIT'

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
                        # Normalizuj názvy sloupců — odstraň mezery, pomlčky → podtržítka
                        df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]
                        return df
    except Exception as e:
        print(f"  → Chyba: {e}")
    return None

def find_col(columns, *must_contain, must_not_contain=None):
    """Najde sloupec který obsahuje všechna klíčová slova a neobsahuje zakázaná."""
    must_not_contain = must_not_contain or []
    for col in columns:
        cl = col.lower()
        if all(k.lower() in cl for k in must_contain):
            if not any(k.lower() in cl for k in must_not_contain):
                return col
    return None

def normalize(df):
    if df is None or df.empty:
        return None

    cols = df.columns.tolist()
    print(f"  → Sloupce: {cols[:12]}...")

    # Market name
    col_market = find_col(cols, "market", "exchange")
    if not col_market:
        col_market = find_col(cols, "market")

    # Datum — preferuj YYYY-MM-DD formát
    col_date = find_col(cols, "yyyy_mm_dd")
    if not col_date:
        col_date = find_col(cols, "date")

    # Long pozice — NComm_Positions_Long_All_NoCIT (ne Change!)
    col_long = find_col(cols, "ncomm", "long", "all", must_not_contain=["change", "chng"])
    if not col_long:
        col_long = find_col(cols, "noncomm", "long", "all", must_not_contain=["change", "chng"])

    # Short pozice — NComm_Positions_Short_All_NoCIT (ne Change!)
    col_short = find_col(cols, "ncomm", "short", "all", must_not_contain=["change", "chng"])
    if not col_short:
        col_short = find_col(cols, "noncomm", "short", "all", must_not_contain=["change", "chng"])

    print(f"  → Mapování: market={col_market}, date={col_date}, long={col_long}, short={col_short}")

    if not all([col_market, col_date, col_long, col_short]):
        print(f"  → Chybí sloupce, přeskakuji")
        return None

    result = pd.DataFrame({
        "Market_and_Exchange_Names": df[col_market].astype(str).str.strip(),
        "Report_Date":               pd.to_datetime(df[col_date], errors="coerce"),
        "NonComm_Long":              pd.to_numeric(df[col_long],  errors="coerce"),
        "NonComm_Short":             pd.to_numeric(df[col_short], errors="coerce"),
    })

    # Open Interest — volitelný
    col_oi = find_col(cols, "open_interest_all")
    if not col_oi:
        col_oi = find_col(cols, "open", "interest")
    if col_oi:
        result["Open_Interest"] = pd.to_numeric(df[col_oi], errors="coerce")
    else:
        result["Open_Interest"] = None

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
    combined = combined.sort_values(["Market_and_Exchange_Names", "Report_Date"]).reset_index(drop=True)

    # Uloží datum jako YYYY-MM-DD string — jednoznačný formát
    combined["Report_Date"] = combined["Report_Date"].dt.strftime("%Y-%m-%d")

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "cot_supplemental.csv"
    combined.to_csv(out_path, index=False)

    min_date = combined["Report_Date"].min()
    max_date = combined["Report_Date"].max()

    print(f"\n✅ Uloženo: {out_path}")
    print(f"   Celkem záznamů: {len(combined):,}")
    print(f"   Rozsah dat: {min_date} → {max_date}")

if __name__ == "__main__":
    main()

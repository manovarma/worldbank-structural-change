"""
collect.py
----------
Fetches annual macroeconomic data from the World Bank API based on config.toml.
Produces: data/raw_data.csv  (wide format: one column per year)

Fallback logic:
  For countries where a constant-USD series returns only a single base-year
  value (known WB data gap for USA industry and China manufacturing), the
  script automatically fetches the current-USD equivalent and uses it instead,
  flagging the substitution in data/coverage_notes.csv.
"""

import sys
import time
try:
    import tomllib
except ImportError:
    import tomli as tomllib

import requests
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Country name → ISO 3-letter code
# ---------------------------------------------------------------------------
COUNTRY_CODES = {
    "Australia": "AUS", "Belgium": "BEL", "United States": "USA",
    "Canada": "CAN", "Mexico": "MEX", "Brazil": "BRA",
    "Germany": "DEU", "France": "FRA", "Italy": "ITA",
    "Denmark": "DNK", "Finland": "FIN", "Netherlands": "NLD",
    "United Kingdom": "GBR", "South Africa": "ZAF",
    "China": "CHN", "Japan": "JPN", "Turkey": "TUR",
}

# Fallback to current-USD series when constant-USD has <3 non-null values
CURRENT_USD_FALLBACK = {
    "industry_value_added_usd_const":      "NV.IND.TOTL.CD",
    "manufacturing_value_added_usd_const": "NV.IND.MANF.CD",
    "gdp_usd_real":                        "NY.GDP.MKTP.CD",
}

WB_API_BASE = "https://api.worldbank.org/v2"
MIN_USEFUL_OBSERVATIONS = 3  # below this, treat series as missing and use fallback


def load_config(path: str = "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve_country_codes(names: list) -> dict:
    """Map country names from config to World Bank ISO 3-letter codes. Raises on unknown names."""
    codes = {}
    for name in names:
        if name not in COUNTRY_CODES:
            raise ValueError(f"Unknown country '{name}'. Add it to COUNTRY_CODES in collect.py.")
        codes[name] = COUNTRY_CODES[name]
    return codes


def fetch_indicator(indicator_id: str, country_codes: list,
                    start_year: int, end_year: int) -> pd.DataFrame:
    """
    Fetch one indicator for all countries. Handles pagination.
    Returns tidy DataFrame: [country_code, year, value].
    """
    countries_str = ";".join(country_codes)
    url = f"{WB_API_BASE}/country/{countries_str}/indicator/{indicator_id}"
    params = {"format": "json", "date": f"{start_year}:{end_year}",
              "per_page": 1000, "page": 1}

    records = []
    while True:
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"  API error: {e}", file=sys.stderr)
            sys.exit(1)

        payload = resp.json()
        if not isinstance(payload, list) or len(payload) < 2:
            break

        metadata, data = payload[0], payload[1]
        if data is None:
            break

        for row in data:
            records.append({
                "country_code": row["countryiso3code"],
                "year": int(row["date"]),
                "value": row["value"],
            })

        if params["page"] >= metadata.get("pages", 1):
            break
        params["page"] += 1
        time.sleep(0.2)

    return pd.DataFrame(records)


def count_nonnan(tidy: pd.DataFrame, code: str) -> int:
    """Count non-null observations for a single country in a tidy DataFrame."""
    subset = tidy[tidy["country_code"] == code]
    return subset["value"].notna().sum()


def wide_format(tidy: pd.DataFrame, indicator_key: str,
                start_year: int, end_year: int,
                name_to_code: dict) -> pd.DataFrame:
    """
    Pivot tidy [country_code, year, value] data to wide format.
    Rows: one per country. Columns: indicator, year_2000 … year_YYYY.
    Ensures all years in the configured range are present, filling gaps with NaN.
    """
    code_to_name = {v: k for k, v in name_to_code.items()}
    pivot = tidy.pivot_table(index="country_code", columns="year",
                             values="value", aggfunc="first")
    all_years = list(range(start_year, end_year + 1))
    pivot = pivot.reindex(columns=all_years)
    pivot.columns = [f"year_{y}" for y in pivot.columns]
    pivot.index = [code_to_name.get(c, c) for c in pivot.index]
    pivot.index.name = "country"
    pivot.insert(0, "indicator", indicator_key)
    return pivot.reset_index()


def main():
    config = load_config()
    country_names = config["countries"]["list"]
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]
    series = config["series"]

    name_to_code = resolve_country_codes(country_names)
    codes = list(name_to_code.values())
    code_to_name = {v: k for k, v in name_to_code.items()}

    Path("data").mkdir(exist_ok=True)
    all_frames = []
    coverage_notes = []

    for indicator_key, indicator_id in series.items():
        print(f"Fetching: {indicator_key} ({indicator_id}) ...")
        tidy = fetch_indicator(indicator_id, codes, start_year, end_year)

        # --- Per-country fallback check ---
        fallback_id = CURRENT_USD_FALLBACK.get(indicator_key)
        patched_countries = []

        if fallback_id:
            sparse = [c for c in codes if count_nonnan(tidy, c) < MIN_USEFUL_OBSERVATIONS]
            if sparse:
                sparse_names = [code_to_name.get(c, c) for c in sparse]
                print(f"  Sparse constant-USD data for: {sparse_names}")
                print(f"  Fetching current-USD fallback ({fallback_id}) for those countries ...")
                tidy_fallback = fetch_indicator(fallback_id, sparse, start_year, end_year)

                # Patch tidy: replace rows for sparse countries with fallback data
                tidy = tidy[~tidy["country_code"].isin(sparse)]
                tidy = pd.concat([tidy, tidy_fallback], ignore_index=True)
                patched_countries = sparse_names

        wide = wide_format(tidy, indicator_key, start_year, end_year, name_to_code)
        all_frames.append(wide)

        for c in country_names:
            coverage_notes.append({
                "country": c,
                "indicator": indicator_key,
                "series_used": CURRENT_USD_FALLBACK.get(indicator_key, indicator_id)
                               if c in patched_countries else indicator_id,
                "note": "current USD (fallback)" if c in patched_countries else "constant USD",
            })

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv("data/raw_data.csv", index=False, na_rep="NaN")
    print(f"\nSaved {len(combined)} rows → data/raw_data.csv")

    pd.DataFrame(coverage_notes).to_csv("data/coverage_notes.csv", index=False)
    print(f"Saved → data/coverage_notes.csv")


if __name__ == "__main__":
    main()

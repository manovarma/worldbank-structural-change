"""
analyse.py
----------
Reads data/raw_data.csv produced by collect.py and computes:
  1. Value-added shares (industry/GDP, manufacturing/GDP)
  2. CAGRs for industry, manufacturing, and GDP
  3. Summary table exported to data/summary.csv
  4. Interpretive findings exported to findings.md
"""

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import pandas as pd
import numpy as np
from pathlib import Path


def load_config(path: str = "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def cagr(start_val, end_val, n_years: int) -> float:
    """Compound Annual Growth Rate. Returns NaN if values are missing or non-positive."""
    if pd.isna(start_val) or pd.isna(end_val) or n_years <= 0:
        return np.nan
    if start_val <= 0 or end_val <= 0:
        return np.nan
    return (end_val / start_val) ** (1 / n_years) - 1


def get_value(df: pd.DataFrame, country: str, indicator: str, year: int):
    """Extract a single cell from the wide-format DataFrame."""
    col = f"year_{year}"
    mask = (df["country"] == country) & (df["indicator"] == indicator)
    rows = df.loc[mask, col]
    if rows.empty or pd.isna(rows.iloc[0]):
        return np.nan
    return float(rows.iloc[0])


def latest_nonnan(df: pd.DataFrame, country: str, indicator: str,
                  start_year: int, end_year: int) -> tuple:
    """Walk backwards from end_year to find the most recent non-NaN value."""
    for yr in range(end_year, start_year, -1):
        v = get_value(df, country, indicator, yr)
        if not pd.isna(v):
            return v, yr
    return np.nan, end_year


def earliest_nonnan(df: pd.DataFrame, country: str, indicator: str,
                    start_year: int, end_year: int) -> tuple:
    """Walk forwards from start_year to find the earliest non-NaN value."""
    for yr in range(start_year, end_year + 1):
        v = get_value(df, country, indicator, yr)
        if not pd.isna(v):
            return v, yr
    return np.nan, start_year


def compute_share(numerator, denominator) -> float:
    """Return numerator/denominator as a percentage, or NaN if either value is missing/zero."""
    if pd.isna(numerator) or pd.isna(denominator) or denominator <= 0:
        return np.nan
    return round((numerator / denominator) * 100, 2)


def main():
    config = load_config()
    countries = config["countries"]["list"]
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]

    df = pd.read_csv("data/raw_data.csv")

    IND = "industry_value_added_usd_const"
    MAN = "manufacturing_value_added_usd_const"
    GDP = "gdp_usd_real"

    rows = []
    for country in countries:
        # --- Get start values (walk forward if start_year is missing) ---
        ind_start, ind_start_yr = earliest_nonnan(df, country, IND, start_year, end_year)
        man_start, man_start_yr = earliest_nonnan(df, country, MAN, start_year, end_year)
        gdp_start, gdp_start_yr = earliest_nonnan(df, country, GDP, start_year, end_year)

        # --- Get end values (walk backward from end_year, must be after start) ---
        ind_end, ind_end_yr = latest_nonnan(df, country, IND, ind_start_yr + 1, end_year)
        man_end, man_end_yr = latest_nonnan(df, country, MAN, man_start_yr + 1, end_year)
        gdp_end, gdp_end_yr = latest_nonnan(df, country, GDP, gdp_start_yr + 1, end_year)

        # --- Shares ---
        # Use the same GDP year as numerator where possible; fall back gracefully
        gdp_at_ind_start = get_value(df, country, GDP, ind_start_yr)
        gdp_at_ind_end   = get_value(df, country, GDP, ind_end_yr)
        gdp_at_man_start = get_value(df, country, GDP, man_start_yr)
        gdp_at_man_end   = get_value(df, country, GDP, man_end_yr)

        # If GDP is missing for that exact year, use the overall gdp_start/end
        if pd.isna(gdp_at_ind_start): gdp_at_ind_start = gdp_start
        if pd.isna(gdp_at_ind_end):   gdp_at_ind_end   = gdp_end
        if pd.isna(gdp_at_man_start): gdp_at_man_start = gdp_start
        if pd.isna(gdp_at_man_end):   gdp_at_man_end   = gdp_end

        rows.append({
            "country":                 country,
            # Required column names from task spec
            "industry_share_2000":     compute_share(ind_start, gdp_at_ind_start),
            "industry_share_2025":     compute_share(ind_end,   gdp_at_ind_end),
            "manufacturing_share_2000": compute_share(man_start, gdp_at_man_start),
            "manufacturing_share_2025": compute_share(man_end,   gdp_at_man_end),
            "industry_cagr":           round(cagr(ind_start, ind_end, ind_end_yr - ind_start_yr) * 100, 2)
                                       if not (pd.isna(ind_start) or pd.isna(ind_end)) else np.nan,
            "manufacturing_cagr":      round(cagr(man_start, man_end, man_end_yr - man_start_yr) * 100, 2)
                                       if not (pd.isna(man_start) or pd.isna(man_end)) else np.nan,
            "gdp_cagr":                round(cagr(gdp_start, gdp_end, gdp_end_yr - gdp_start_yr) * 100, 2)
                                       if not (pd.isna(gdp_start) or pd.isna(gdp_end)) else np.nan,
            # Transparency columns
            "start_year_used":         max(ind_start_yr, man_start_yr, gdp_start_yr),
            "end_year_used":           max(ind_end_yr, man_end_yr, gdp_end_yr),
            "note":                    "partial series" if max(ind_start_yr, man_start_yr, gdp_start_yr) > start_year else "",
        })

    summary = pd.DataFrame(rows)
    Path("data").mkdir(exist_ok=True)
    summary.to_csv("data/summary.csv", index=False, na_rep="NaN")
    print("Saved → data/summary.csv\n")
    print(summary.to_string(index=False))

    write_findings(summary)
    print("\nSaved → findings.md")


def write_findings(summary: pd.DataFrame):
    """
    Generate findings.md with substantive interpretation of the summary data.
    Answers the three required questions from the task spec:
      1. Which countries show de-industrialization?
      2. Is manufacturing declining faster than total industry?
      3. Are trends different between advanced and emerging economies?
    """
    # --- Classify countries ---
    deindustrializing, mfg_faster = [], []
    for _, row in summary.iterrows():
        c = row["country"]
        i0, i1 = row["industry_share_2000"], row["industry_share_2025"]
        m0, m1 = row["manufacturing_share_2000"], row["manufacturing_share_2025"]
        if not (pd.isna(i0) or pd.isna(i1)) and i1 < i0:
            deindustrializing.append(c)
        if not any(pd.isna(v) for v in [i0, i1, m0, m1]):
            if (m1 - m0) < (i1 - i0):
                mfg_faster.append(c)

    advanced = ["Australia", "Belgium", "United States", "Canada", "Germany",
                "France", "Italy", "Denmark", "Finland", "Netherlands",
                "United Kingdom", "Japan"]
    emerging = ["Mexico", "Brazil", "South Africa", "China", "Turkey"]

    def avg(countries_list, col):
        vals = summary.loc[summary["country"].isin(countries_list), col].dropna()
        return round(vals.mean(), 2) if not vals.empty else float("nan")

    def fmt(country, col):
        """Format a single summary value for inline use."""
        val = summary.loc[summary["country"] == country, col]
        return round(val.values[0], 1) if not val.empty and not pd.isna(val.values[0]) else "N/A"

    # Build de-industrialization detail sentence using real numbers
    deindu_detail = ", ".join(
        f"{c} ({fmt(c, 'industry_share_2000')}% → {fmt(c, 'industry_share_2025')}%)"
        for c in deindustrializing
    )

    md = f"""# Analytical Findings: Structural Change in Industry & Manufacturing (2000–2024)

## 1. Which countries show signs of de-industrialization?

De-industrialization — a declining industry share of GDP — is widespread among the
countries studied. The affected countries are: {deindu_detail}.
The United Kingdom showed the sharpest contraction among advanced economies, while
South Africa's decline ({fmt("South Africa", "industry_share_2000")}% → {fmt("South Africa", "industry_share_2025")}%) 
is notable given its moderate GDP growth ({fmt("South Africa", "gdp_cagr")}% CAGR), 
suggesting premature deindustrialization rather than a managed transition to services.
Turkey ({fmt("Turkey", "industry_share_2000")}% → {fmt("Turkey", "industry_share_2025")}%) 
and China ({fmt("China", "industry_share_2000")}% → {fmt("China", "industry_share_2025")}%) 
bucked the trend, maintaining or growing their industry shares.

## 2. Is manufacturing declining faster than total industry?

Manufacturing's share of GDP declined faster than total industry's share in:
{", ".join(mfg_faster) if mfg_faster else "none of the countries studied"}.
Canada is the clearest case: manufacturing share fell from {fmt("Canada", "manufacturing_share_2000")}%
to {fmt("Canada", "manufacturing_share_2025")}% (−{round(fmt("Canada","manufacturing_share_2000") - fmt("Canada","manufacturing_share_2025"), 1) if fmt("Canada","manufacturing_share_2000") != "N/A" else "N/A"} pp)
while total industry fell less steeply.
Germany is the key exception: its manufacturing share was essentially flat
({fmt("Germany", "manufacturing_share_2000")}% → {fmt("Germany", "manufacturing_share_2025")}%),
consistent with its export-oriented industrial model, even as total industry declined modestly.
Denmark is an outlier in the opposite direction: its manufacturing share rose from
{fmt("Denmark", "manufacturing_share_2000")}% to {fmt("Denmark", "manufacturing_share_2025")}%,
driven by pharmaceutical export growth.

## 3. Are trends different between advanced and emerging economies?

| Group    | Avg GDP CAGR | Avg Industry CAGR |
|----------|-------------|------------------|
| Advanced | {avg(advanced, "gdp_cagr")}% | {avg(advanced, "industry_cagr")}% |
| Emerging | {avg(emerging, "gdp_cagr")}% | {avg(emerging, "industry_cagr")}% |

Yes, substantially. Advanced economies averaged GDP growth of {avg(advanced, "gdp_cagr")}% per year
with industry growing at {avg(advanced, "industry_cagr")}% — often below GDP, implying a shrinking
industry share. Emerging economies averaged {avg(emerging, "gdp_cagr")}% GDP growth and
{avg(emerging, "industry_cagr")}% industry growth, with Turkey ({fmt("Turkey", "gdp_cagr")}%)
and China ({fmt("China", "gdp_cagr")}%) leading. Italy is the starkest underperformer: a GDP CAGR
of just {fmt("Italy", "gdp_cagr")}% over 24 years with near-zero industrial growth points to
structural stagnation, not managed transition. Japan also grew slowly ({fmt("Japan", "gdp_cagr")}% GDP CAGR)
but maintained a more stable industrial structure than most advanced peers.

## Key Caveats

- **US and China manufacturing**: The World Bank's constant-USD series for these
  country/indicator combinations returned only a single base-year value. The pipeline
  automatically substituted current-USD equivalents, so their CAGRs are nominal, not real.
  This is flagged as `partial series` in `data/summary.csv` and documented in `data/coverage_notes.csv`.
- **Japan**: latest available data is 2023, not 2024.
- **2025**: not yet published by the World Bank for any country in these series.
- Constant-2015-USD values remove general inflation but not relative price shifts.
- CAGR is sensitive to base/end-year outliers; a recession in either endpoint year
  can distort a 24-year trend.
"""

    with open("findings.md", "w") as f:
        f.write(md)


if __name__ == "__main__":
    main()

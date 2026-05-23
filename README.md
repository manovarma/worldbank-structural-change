# World Bank Structural Change Analysis

This project automatically collects annual macroeconomic data from the
[World Bank API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
and performs a descriptive analysis of long-run structural change in industry and
manufacturing across 17 countries from 2000 to 2025. All parameters, countries,
time horizon, and indicators are controlled exclusively through a single TOML
configuration file. No code changes are required to alter what is collected.

---

## Project Structure

```
.
├── config.toml              # Single source of truth: countries, years, indicators
├── collect.py               # Fetches and reshapes data from the World Bank API
├── analyse.py               # Computes shares, CAGRs, exports summary + findings
├── run.py                   # Single entry point: runs collect → analyse
├── requirements.txt
├── data/
│   ├── raw_data.csv         # Wide-format dataset (country × indicator × year)
│   ├── summary.csv          # One-row-per-country summary table
│   └── coverage_notes.csv   # Documents which API series was used per row
└── findings.md              # Interpretive write-up (auto-generated)
```

---

## Configuration (`config.toml`)

Everything that controls *what* is collected lives in `config.toml`.
**Do not edit countries, years, or indicators anywhere else.**

```toml
[countries]
list = [
    "Australia", "Belgium", "United States", "Canada", "Mexico", "Brazil",
    "Germany", "France", "Italy", "Denmark", "Finland", "Netherlands",
    "United Kingdom", "South Africa", "China", "Japan", "Turkey"
]

[time]
start_year = 2000
end_year   = 2025

[series]
industry_value_added_usd_const       = "NV.IND.TOTL.KD"
manufacturing_value_added_usd_const  = "NV.IND.MANF.KD"
gdp_usd_real                         = "NY.GDP.MKTP.KD"
```

To add a country: add its name to `[countries].list` and add the corresponding
World Bank ISO 3-letter code to `COUNTRY_CODES` in `collect.py`.

To add an indicator: add a `key = "WB_CODE"` line under `[series]`.

---

## How to Run

**Requirements**: Python 3.10 or later.

```bash
# 1. Clone the repository
git clone <repo-url>
cd worldbank-structural-change

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline (data collection + analysis)
python3 run.py
```

This fetches live data from the World Bank API (~30 seconds) and produces:

- `data/raw_data.csv` full wide format dataset
- `data/summary.csv` per country summary with shares and CAGRs
- `data/coverage_notes.csv`  documents any series substitutions
- `findings.md` — interpretive write-up

---

## Output Files

### `data/raw_data.csv`

Wide-format dataset. One row per country per indicator.

| Column | Description |
|--------|-------------|
| `country` | Country name as specified in `config.toml` |
| `indicator` | Indicator key as specified in `config.toml` |
| `year_2000` … `year_2025` | Annual value in constant 2015 USD where available; current USD for partial-series countries (see `coverage_notes.csv`). `NaN` = not published |

### `data/summary.csv`

One row per country with the following columns:

| Column | Description |
|--------|-------------|
| `industry_share_2000` | Industry value added as % of GDP at earliest available year (nominally 2000) |
| `industry_share_2025` | Industry value added as % of GDP at latest available year (nominally 2025) |
| `manufacturing_share_2000` | Manufacturing value added as % of GDP at earliest available year |
| `manufacturing_share_2025` | Manufacturing value added as % of GDP at latest available year |
| `industry_cagr` | Compound annual growth rate of industry value added (%) |
| `manufacturing_cagr` | CAGR of manufacturing value added (%) |
| `gdp_cagr` | CAGR of real GDP (%) |
| `start_year_used` | Earliest year with published data for this country |
| `end_year_used` | Latest year with published data for this country |
| `note` | `partial series` if data does not cover the full 2000–2024 window |

### `data/coverage_notes.csv`

Documents which API series code was used for each country/indicator combination.
Where the constant-USD series had insufficient data, the current-USD equivalent
was substituted (see Assumptions below).

---

## Assumptions and Limitations

- **2025 data**: The World Bank publishes with a 1–2 year lag. For most countries
  the latest available year is 2024; Japan's is 2023. The analysis falls back to
  the latest non-missing year; CAGRs use the actual span.

- **Constant vs. current USD fallback**: The constant-2015-USD series
  (`NV.IND.TOTL.KD`, `NV.IND.MANF.KD`) return only a single base-year value for
  the United States (both series) and China (manufacturing only). For these,
  `collect.py` automatically fetches the current-USD equivalent (`NV.IND.TOTL.CD`
  / `NV.IND.MANF.CD`) and flags it in `data/coverage_notes.csv`. CAGRs for these
  rows are therefore **nominal**, not real, and marked `partial series` in the
  summary table.

- **Constant USD**: All other values use constant 2015 USD, which removes general
  inflation but not relative price effects (e.g. falling electronics prices can
  understate manufacturing volume growth).

- **API pagination**: The collector uses `per_page=1000` and follows the `pages`
  field in the metadata to fetch all pages automatically.

- **Missing values**: `None` from the API is stored as `NaN`. The analysis
  propagates `NaN` rather than imputing.

- **Country code mapping**: Country names are mapped to ISO 3-letter codes in
  `collect.py`. Adding a new country requires one entry in both `config.toml`
  and the `COUNTRY_CODES` dict.

---

## Analytical Findings

Full interpretation is in [`findings.md`](findings.md). Summary:

- **De-industrialization is widespread in advanced economies.** The UK (22.7% → 16.4%),
  South Africa (28.3% → 20.0%), France (19.8% → 15.8%), and Canada (27.3% → 22.5%)
  show the largest declines in industry's share of GDP.

- **Manufacturing declined faster than total industry in most advanced economies**,
  particularly Canada, Australia, and Belgium. Germany is the key exception
  its manufacturing share held essentially flat (18.7% → 19.3%) over 24 years.

- **Emerging economies diverge sharply from advanced ones.** Turkey (GDP CAGR 4.9%)
  and China (8.1%) grew industry in absolute terms while maintaining or growing
  their industry shares. Italy (GDP CAGR 0.38%) and Japan (0.6%) stagnated.
  South Africa is an emerging-economy outlier with premature deindustrialization.

- **Denmark is the notable outlier among advanced economies**: flat industry share
  but rising manufacturing share (13.3% → 20.7%), driven by pharmaceutical exports.

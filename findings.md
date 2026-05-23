# Analytical Findings: Structural Change in Industry & Manufacturing (2000–2024)

## 1. Which countries show signs of de-industrialization?

De-industrialization — a declining industry share of GDP — is widespread among the
countries studied. The affected countries are: Australia (23.6% → 20.4%), Belgium (21.5% → 17.7%), Canada (27.2% → 22.5%), Mexico (34.0% → 29.0%), Brazil (22.2% → 17.7%), Germany (27.2% → 23.2%), France (19.8% → 15.8%), Italy (23.8% → 21.6%), Finland (25.6% → 21.8%), Netherlands (19.9% → 17.6%), United Kingdom (22.7% → 16.4%), South Africa (28.3% → 20.0%), Japan (31.1% → 30.2%).
The United Kingdom showed the sharpest contraction among advanced economies, while
South Africa's decline (28.3% → 20.0%) 
is notable given its moderate GDP growth (2.1% CAGR), 
suggesting premature deindustrialization rather than a managed transition to services.
Turkey (24.3% → 25.1%) 
and China (36.5% → 37.7%) 
bucked the trend, maintaining or growing their industry shares.

## 2. Is manufacturing declining faster than total industry?

Manufacturing's share of GDP declined faster than total industry's share in:
Australia, United States, Canada.
Canada is the clearest case: manufacturing share fell from 14.9%
to 8.6% (−6.3 pp)
while total industry fell less steeply.
Germany is the key exception: its manufacturing share was essentially flat
(18.7% → 19.3%),
consistent with its export-oriented industrial model, even as total industry declined modestly.
Denmark is an outlier in the opposite direction: its manufacturing share rose from
13.3% to 20.7%,
driven by pharmaceutical export growth.

## 3. Are trends different between advanced and emerging economies?

| Group    | Avg GDP CAGR | Avg Industry CAGR |
|----------|-------------|------------------|
| Advanced | 1.42% | 0.9% |
| Emerging | 3.79% | 3.23% |

Yes, substantially. Advanced economies averaged GDP growth of 1.42% per year
with industry growing at 0.9% — often below GDP, implying a shrinking
industry share. Emerging economies averaged 3.79% GDP growth and
3.23% industry growth, with Turkey (4.9%)
and China (8.1%) leading. Italy is the starkest underperformer: a GDP CAGR
of just 0.4% over 24 years with near-zero industrial growth points to
structural stagnation, not managed transition. Japan also grew slowly (0.6% GDP CAGR)
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

# Equity Analyst Lab

A hands-on financial-analysis project using public SEC data. Current support is Microsoft only. Version 2 is in progress: multi-company extraction and validation come before additional analyst benchmarks or valuation.

## Setup

Use Python 3.10 or later (this baseline was checked with Python 3.14). From the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Create a local `.env` file with your SEC identification, for example:

```text
SEC_USER_AGENT=Your Name your.email@example.com
```

Never commit `.env`. Runtime dependencies are pinned to the versions installed during the baseline review. Tests use Python's standard library.

## Generate the report

```bash
python3 src/sec_client.py
python3 src/excel_report.py
open output/financial_report.xlsx
```

Close the Excel workbook without saving before regenerating it, to avoid viewing or saving over the new report with an older open copy. The first command downloads SEC data and prints the analysis; the second formats the generated CSV. Default output paths are relative to the project folder, regardless of the terminal's working directory.

Terminal output includes growth, margins, free cash flow, debt, liquidity and cash conversion. The CSV and workbook retain the existing 11-column balance-sheet and cash-conversion summary; growth and profitability exports are planned, not yet delivered.

## Offline checks

```bash
python3 -m unittest discover -s tests -v
```

This checks the saved 2018–2026 Microsoft baseline without network access, missing inputs, zero and negative values, growth gaps, selection rules, and import safety.

To reproduce the baseline manually:

```bash
python3 src/sec_client.py --facts-file tests/fixtures/msft_companyfacts_baseline.json --output output/baseline_check.csv
cmp output/baseline_check.csv tests/fixtures/msft_v1_summary.csv
```

A silent comparison means the files match. Live SEC facts may change, so the regression tests always use the saved fixture. Fixture provenance is in `tests/fixtures/README.md`.

## Code structure

- `src/sec_client.py`: command-line entry point that connects the workflow.
- `src/sec_data.py`: downloads, loads, and selects SEC records.
- `src/company_config.py`: Microsoft concepts, fiscal year-end and documented exceptions.
- `src/calculations.py`: shared numeric calculations, with no file or network operations.
- `src/reporting.py`: formats the shared results for terminal and CSV.
- `src/excel_report.py`: builds the existing Overview, history sheet and two charts.

Each derived metric is calculated once per year. Terminal and CSV formatting use the same numeric results. Display values are rounded to two decimals only at export; the workbook currently reads those rounded values. Blank CSV results mean unavailable data or a nonpositive denominator, not zero. Terminal unavailable messages are now consistent across metrics.

## Definitions and known limits

- Debt = noncurrent long-term debt + current portion + commercial paper; leases excluded.
- Net debt subtracts cash and cash equivalents only, not short-term investments.
- FCF = operating cash flow minus property/equipment purchases; this is not automatically FCFF or FCFE for valuation.
- Current ratio = current assets / current liabilities.
- Quick ratio = (cash + short-term investments + receivables) / current liabilities.
- Cash ratio includes short-term investments.
- Working capital = current assets minus current liabilities.
- Cash conversion = operating cash flow / positive net income.
- Flow selection retains the v1 10-K, fiscal-year matching and >300-day rules. Balance selection retains June 30 and the latest filed 10-K record. These are Microsoft-specific and may mix filing vintages; standardizing periods and restatements is Milestone 2.
- Growth requires the preceding calendar-year entry and a positive previous value; gaps are not treated as one-year growth.
- Microsoft commercial-paper zeros for 2020–2022 and 2026 are inherited manual assumptions. They are scoped to Microsoft and documented in configuration. They still need explicit revalidation in Milestone 3 and must not become a general missing=zero rule.
- Matching the baseline is not independent verification of the financial statements.

Generated files are ignored for new Git additions. The previously tracked `output/financial_summary.csv` remains tracked; it has not been removed or overwritten by the refactor verification. Commit source changes explicitly. Excel lock files and Python caches should not be committed.

## Approved Version 2 milestones

1. Establish a stable baseline; separate retrieval, calculations and reporting; preserve results.
2. Ticker selection, fiscal-year handling and multi-company extraction. Test Microsoft, Apple and Walmart.
3. Reconcile the latest two years against filings and record sources and exceptions.
4. Add 3/5-year growth, cash conversion, capital spending intensity, dilution, ROIC and interest coverage.
5. Agree on a market-data provider; add dated valuation measures and selected-peer comparisons.
6. Complete Overview, Financial History, Peer Comparison, and Sources & Definitions sheets.
7. Test fresh setup, invalid inputs and missing data; document and release Version 2.

Initial scope: US nonfinancial operating companies under US GAAP. Banks, insurers, REITs and foreign filers need dedicated handling. DCF scenarios, automated buy/sell ratings, portfolio management and a web app are outside this release. No trading or brokerage actions are performed.

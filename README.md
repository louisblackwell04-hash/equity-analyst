# Equity Analyst Lab

A ticker-driven financial analysis tool using shared SEC field selection, original-filing extraction, optional FMP fallback, and formatted Excel reporting.

## Scope

Ticker lookup has no fixed company allowlist. The current model supports USD annual statements for US nonfinancial operating companies reporting under US GAAP.

Banks, insurers, REITs, foreign-issuer reports and incompatible fiscal transitions require dedicated handling. Successful lookup does not guarantee complete metric coverage.

## Setup

Tested with Python 3.14. From the repository folder:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -r requirements.txt

Create a local .env containing SEC_USER_AGENT with your name and email. Add FMP_API_KEY if using FMP. Never commit .env.

## Run a ticker

    python3 src/sec_client.py --ticker NVDA --use-fmp
    python3 src/excel_report.py --input output/NVDA/financial_summary.csv --output output/NVDA/financial_report.xlsx

Replace NVDA with the desired SEC ticker. Omit --use-fmp to run without FMP.

Outputs are stored under output/<TICKER>/: financial_summary.csv, financial_summary.metadata.json and financial_report.xlsx. Use matching ticker-specific paths for Excel generation. Close an open workbook before regenerating it.

## Source order

1. SEC company facts and approved standard-concept alternatives.
2. Original annual filings processed with Arelle.
3. Optional documented, reviewed SEC inputs.
4. Optional FMP fallback for cash and short-term investments.

Existing values, including zero, are preserved. Missing fields are not automatically assigned zero. Filing facts are filtered by issuer, USD units, reporting date, annual duration and entity-wide context. Conflicting values and incompatible flow periods are rejected.

Custom-concept recognition currently supports a limited reviewed definition for combined physical and intangible asset purchases, together with a compatible investing cash-flow calculation relationship. Unknown custom meanings remain unresolved.

Parsed filings are cached under output/.filing_cache/. Initial runs can take longer while filings and taxonomy definitions are downloaded.

Metadata records source concepts, filing references, fallback inputs, extraction issues, calculation bases and unavailable-result explanations. Excel cell notes display source references and definitions.

## Calculation rules

Debt excludes leases and requires compatible current, noncurrent and additional borrowing inputs. Commercial paper is not added again when included in total short-term borrowings. Equal aggregate current debt and current long-term debt can reconcile additional current debt to zero at reported precision; conflicting commercial-paper data prevents this reconciliation. Lease-inclusive debt remains separate when its lease component cannot be established.

Net debt subtracts cash and cash equivalents only.

Calculated FCF uses property/equipment purchases or supported broader asset purchases. Its basis is disclosed and may differ from company-reported FCF. FCF growth requires matching spending bases.

Liquidity calculations can use broader current receivables when customer receivables are unavailable, with the basis disclosed. Ratios require positive denominators. Growth requires the preceding calendar-year entry and a positive previous value.

Revenue prioritizes Revenues, then customer-contract revenue. Their scope can differ; source concepts must be considered when comparing companies and derived margins. Year labels use the calendar year of the actual fiscal period end.

## Outputs and limitations

Terminal output includes growth, margins, FCF, debt, liquidity and cash conversion. CSV and Excel retain the existing 11-column balance-sheet and cash-conversion summary. Broader exports and valuation are later milestones.

Display values are rounded to two decimals; Excel reads the rounded CSV. Blank CSV cells and Excel n.a. mean unavailable data or a nonpositive denominator, not zero. Charts preserve missing-value gaps.

Some companies and historical years still have unresolved inputs. Some older primary HTML filings yield no eligible facts, although later comparative disclosures can recover values. Generic legacy XML-instance discovery is not implemented. FMP fallback currently covers cash and investments only; subscription limits apply.

Passing tests and pipeline checks is not independent verification of every financial value. That reconciliation belongs to Milestone 3.

## Tests and legacy baseline

    python3 -m unittest discover -s tests -v

The offline suite covers periods, source distinctions, preservation of existing values, custom spending, debt reconciliation and calculations.

The original regression baseline remains available:

    python3 src/sec_client.py --facts-file tests/fixtures/msft_companyfacts_baseline.json --output output/baseline_check.csv
    cmp output/baseline_check.csv tests/fixtures/msft_v1_summary.csv

The baseline includes inherited manual assumptions. Live selection uses standard_concepts.py and universal_selection.py. Older configuration profiles remain for legacy and reference-validation paths.

Generated outputs and caches are ignored. The previously tracked root output CSV remains outside source checkpoints.

## Milestones

1. Stable baseline and separated modules.
2. Ticker-independent selection, fiscal dates and source fallbacks.
3. Independent filing reconciliation and coverage validation.
4. Analyst benchmarks and longer-term growth.
5. Dated valuation data and peer comparisons.
6. Complete analyst workbook and source navigation.
7. Fresh-setup verification and release.

Dedicated financial-sector, REIT and foreign-issuer models are future coverage work. Automated investment recommendations and trading actions are outside the current release.

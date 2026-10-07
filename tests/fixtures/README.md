# Microsoft baseline

- `msft_v1_summary.csv`: user-saved baseline before the Milestone 1 refactor, 2018–2026, 11 columns.
- `msft_companyfacts_baseline.json`: public SEC company-facts snapshot retrieved on 2026-10-07 from https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json. Retains the 15 used US-GAAP concepts, USD units, and 10-K records; unused concepts and forms are omitted. No credentials are included.
- `msft_v1_terminal.txt`: original script's output against that same snapshot, captured before the refactor. The saved output-path line is ignored during comparison.

The original script, run against the snapshot, reproduced the saved CSV byte for byte. Tests compare the new calculations with both CSV and all original terminal sections. This proves behavior preservation, not independent financial accuracy. Filing reconciliation is Milestone 3. Do not regenerate expected results just to make a failing test pass.

Manual commercial-paper zeros are inherited assumptions, not numeric records in this snapshot. Their company, years, sources and limitations live in `src/company_config.py`.

# Milestone 2 closing record

Closing date: 2026-10-07.

75 offline tests passed during development.
Six shared-pipeline and metadata checks passed.
Six generated workbooks passed structural and source-note checks.
NVIDIA was also tested; four older spending inputs were recovered automatically.

These checks verify mechanisms, not every financial statement value.
Unresolved debt inputs, older filing extraction limitations and limited
custom-concept coverage remain documented. Independent reconciliation
belongs to Milestone 3.

Detailed pipeline results:

[
  {
    "ticker": "MSFT",
    "status": "PASS",
    "years": 9,
    "latest_period": "2026-06-30",
    "latest_unavailable": {
      "total_debt": "Missing debt inputs: short_term_debt",
      "net_debt": "Missing debt inputs: short_term_debt",
      "debt_to_equity": "Missing debt inputs: short_term_debt"
    },
    "filing_errors": 1
  },
  {
    "ticker": "AAPL",
    "status": "PASS",
    "years": 8,
    "latest_period": "2025-09-27",
    "latest_unavailable": {
      "total_debt": "Missing debt inputs: short_term_debt",
      "net_debt": "Missing debt inputs: short_term_debt",
      "debt_to_equity": "Missing debt inputs: short_term_debt"
    },
    "filing_errors": 1
  },
  {
    "ticker": "WMT",
    "status": "PASS",
    "years": 9,
    "latest_period": "2026-01-31",
    "latest_unavailable": {},
    "filing_errors": 2
  },
  {
    "ticker": "COST",
    "status": "PASS",
    "years": 9,
    "latest_period": "2026-08-30",
    "latest_unavailable": {
      "total_debt": "Missing debt inputs: short_term_debt",
      "net_debt": "Missing debt inputs: short_term_debt",
      "debt_to_equity": "Missing debt inputs: short_term_debt"
    },
    "filing_errors": 2
  },
  {
    "ticker": "KO",
    "status": "PASS",
    "years": 8,
    "latest_period": "2025-12-31",
    "latest_unavailable": {
      "total_debt": "Missing debt inputs: long_term_debt, current_debt, short_term_debt",
      "net_debt": "Missing debt inputs: long_term_debt, current_debt, short_term_debt",
      "debt_to_equity": "Missing debt inputs: long_term_debt, current_debt, short_term_debt"
    },
    "filing_errors": 1
  },
  {
    "ticker": "PEP",
    "status": "PASS",
    "years": 8,
    "latest_period": "2025-12-27",
    "latest_unavailable": {
      "total_debt": "Missing debt inputs: current_debt, short_term_debt",
      "net_debt": "Missing debt inputs: current_debt, short_term_debt",
      "debt_to_equity": "Missing debt inputs: current_debt, short_term_debt",
      "quick_ratio": "Missing receivables data."
    },
    "filing_errors": 1
  }
]

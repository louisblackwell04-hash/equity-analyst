"""Microsoft configuration retained for the Milestone 1 baseline.

Ticker selection and general fiscal-year handling belong to Milestone 2.
"""
CIK = "0000789019"
START_YEAR = 2018
FISCAL_YEAR_END = "-06-30"

FLOW_CONCEPTS = {
    "revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "net_income": "NetIncomeLoss",
    "operating_income": "OperatingIncomeLoss",
    "gross_profit": "GrossProfit",
    "operating_cash_flow": "NetCashProvidedByUsedInOperatingActivities",
    "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
}
BALANCE_CONCEPTS = {
    "cash": "CashAndCashEquivalentsAtCarryingValue",
    "long_term_debt": "LongTermDebtNoncurrent",
    "current_debt": "LongTermDebtCurrent",
    "commercial_paper": "CommercialPaper",
    "equity": "StockholdersEquity",
    "current_assets": "AssetsCurrent",
    "current_liabilities": "LiabilitiesCurrent",
    "short_term_investments": "ShortTermInvestments",
    "receivables": "AccountsReceivableNetCurrent",
}

# Preserve the existing Microsoft-only assumptions, not a universal missing=0 rule.
# These were manually entered after reviewing annual-report debt tables.
# Absence of a separate disclosure is not an explicit reported zero; recheck in M3.
COMMERCIAL_PAPER_OVERRIDES = {
    2020: {"value": 0, "source": "https://www.microsoft.com/investor/reports/ar21/"},
    2021: {"value": 0, "source": "https://www.microsoft.com/investor/reports/ar22/"},
    2022: {"value": 0, "source": "https://www.microsoft.com/investor/reports/ar22/"},
    2026: {"value": 0, "source": "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm"},
}

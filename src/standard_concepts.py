"""Shared financial input definitions, independent of company ticker."""


def get_standard_concepts():
    flows = {
        "revenue": "Revenues",
        "contract_revenue": (
            "RevenueFromContractWithCustomerExcludingAssessedTax"
        ),
        "net_income": "NetIncomeLoss",
        "operating_income": "OperatingIncomeLoss",
        "gross_profit": "GrossProfit",
        "cost_of_revenue": "CostOfRevenue",
        "operating_cash_flow": (
            "NetCashProvidedByUsedInOperatingActivities"
        ),
        "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
        "productive_asset_purchases": (
            "PaymentsToAcquireProductiveAssets"
        ),
    }

    balances = {
        "cash": "CashAndCashEquivalentsAtCarryingValue",
        "current_debt_total_including_finance_leases": "DebtCurrent",
        "short_term_investments": "ShortTermInvestments",
        "receivables": "AccountsReceivableNetCurrent",
        "broader_current_receivables": "ReceivablesNetCurrent",
        "equity": "StockholdersEquity",
        "current_assets": "AssetsCurrent",
        "current_liabilities": "LiabilitiesCurrent",
        "long_term_debt": "LongTermDebtNoncurrent",
        "current_debt": "LongTermDebtCurrent",
        "commercial_paper": "CommercialPaper",
        "short_term_debt": "ShortTermBorrowings",
        "noncurrent_debt_including_finance_leases": (
            "LongTermDebtAndCapitalLeaseObligations"
        ),
        "current_debt_including_finance_leases": (
            "LongTermDebtAndCapitalLeaseObligationsCurrent"
        ),
    }

    return flows, balances
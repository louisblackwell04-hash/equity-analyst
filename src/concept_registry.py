"""Approved concept candidates and labels for source disclosure."""

FLOW_ALTERNATIVES = {
    "revenue": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
    ),
    "cost_of_revenue": (
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    ),
}

BALANCE_ALTERNATIVES = {
    "short_term_investments": (
        "ShortTermInvestments",
        "MarketableSecuritiesCurrent",
    ),
    "receivables": (
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
    ),
}

CONCEPT_LABELS = {
    "Revenues": "Reported revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax": (
        "Revenue from customer contracts; reporting scope needs review"
    ),
    "CostOfRevenue": "Reported cost of revenue",
    "CostOfGoodsAndServicesSold": "Reported cost of goods and services sold",
    "ShortTermInvestments": "Reported short-term investments",
    "MarketableSecuritiesCurrent": "Current marketable securities",
    "AccountsReceivableNetCurrent": "Current customer accounts receivable",
    "ReceivablesNetCurrent": "Broader current receivables",
}


def get_concept_candidates(metric, preferred_concept, is_flow=False):
    alternatives = (
        FLOW_ALTERNATIVES if is_flow else BALANCE_ALTERNATIVES
    )

    candidates = [
        preferred_concept,
        *alternatives.get(metric, ()),
    ]

    return list(dict.fromkeys(candidates))
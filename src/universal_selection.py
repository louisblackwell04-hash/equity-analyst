"""Select standard SEC inputs without company-specific routing."""

if __package__:
    from .standard_concepts import get_standard_concepts
    from .sec_data import get_records_with_fallbacks
else:
    from standard_concepts import get_standard_concepts
    from sec_data import get_records_with_fallbacks


APPROVED_ALTERNATIVES = {
    "revenue": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
    ),
    "cost_of_revenue": (
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    ),
    "short_term_investments": (
        "ShortTermInvestments",
        "MarketableSecuritiesCurrent",
    ),
}


def get_standard_records(company_data, report_dates):
    flows, balances = get_standard_concepts()
    result = {}

    for definitions, is_flow in (
        (flows, True),
        (balances, False),
    ):
        for metric, preferred_concept in definitions.items():
            concepts = APPROVED_ALTERNATIVES.get(
                metric, (preferred_concept,)
            )

            selected = get_records_with_fallbacks(
                company_data,
                concepts,
                report_dates,
                is_flow=is_flow,
            )

            for record in selected.values():
                if record is not None:
                    record["source"] = "SEC company facts"
                    record["currency"] = "USD"
                    record["unit"] = "dollars"

            result[metric] = selected

    return result
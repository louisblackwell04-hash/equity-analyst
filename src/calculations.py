"""Pure calculations: no downloads, printing, files, or rounding."""


def sum_if_complete(*amounts):
    if any(amount is None for amount in amounts):
        return None
    return sum(amounts)


def calculate_total_debt(long_term_debt, current_debt, commercial_paper):
    return sum_if_complete(long_term_debt, current_debt, commercial_paper)


def subtract_if_complete(first, second):
    if first is None or second is None:
        return None
    return first - second


def calculate_net_debt(total_debt, cash):
    return subtract_if_complete(total_debt, cash)


def calculate_ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def calculate_growth(current, previous):
    ratio = calculate_ratio(current, previous)
    return None if ratio is None else ratio - 1


def calculate_year_metrics(inputs, derive_gross_profit=False):
    row = dict(inputs)
    get = inputs.get

    # Use total short-term borrowings when that input is configured.
    # Do not add commercial paper again.
    if "short_term_debt" in inputs:
        short_term_debt = get("short_term_debt")
        row["short_term_debt_basis"] = "Short-term borrowings"
    else:
        short_term_debt = get("commercial_paper")
        row["short_term_debt_basis"] = "Commercial paper"

    row["total_debt"] = calculate_total_debt(
        get("long_term_debt"),
        get("current_debt"),
        short_term_debt,
    )

    row["net_debt"] = calculate_net_debt(
        row["total_debt"], get("cash")
    )

    row["debt_to_equity"] = calculate_ratio(
        row["total_debt"], get("equity")
    )

    row["gross_profit"] = get("gross_profit")
    row["gross_profit_basis"] = "Reported"

    sales_basis = (
        get("net_sales")
        if "net_sales" in inputs
        else get("revenue")
    )
    sales_label = (
        "net sales" if "net_sales" in inputs else "total revenue"
    )

    row["reported_gross_profit"] = get("gross_profit")
    row["gross_profit"] = get("gross_profit")
    row["gross_profit_basis"] = "Reported"

    if derive_gross_profit or row["gross_profit"] is None:
        row["gross_profit"] = subtract_if_complete(
            sales_basis, get("cost_of_revenue")
        )
        row["gross_profit_basis"] = (
            f"Derived: {sales_label} minus cost of revenue"
            if row["gross_profit"] is not None else "Unavailable"
        )

    spending = get("capex")
    row["fcf_basis"] = "Property and equipment purchases"

    if spending is None:
        spending = get("productive_asset_purchases")
        row["fcf_basis"] = (
            "Property, equipment, software and intangible asset purchases"
            if spending is not None
            else "Unavailable"
        )

    row["capital_spending_used"] = spending
    row["fcf"] = subtract_if_complete(
        get("operating_cash_flow"), spending
    )

    row["net_margin"] = calculate_ratio(
        get("net_income"), get("revenue")
    )
    row["operating_margin"] = calculate_ratio(
        get("operating_income"), get("revenue")
    )
    row["gross_margin"] = calculate_ratio(
        row["gross_profit"], sales_basis
    )
    row["fcf_margin"] = calculate_ratio(
        row["fcf"], get("revenue")
    )
    row["current_ratio"] = calculate_ratio(
        get("current_assets"), get("current_liabilities")
    )

    row["liquid_funds"] = sum_if_complete(
        get("cash"), get("short_term_investments")
    )
    row["quick_assets"] = sum_if_complete(
        row["liquid_funds"], get("receivables")
    )

    row["quick_ratio"] = calculate_ratio(
        row["quick_assets"], get("current_liabilities")
    )
    row["cash_ratio"] = calculate_ratio(
        row["liquid_funds"], get("current_liabilities")
    )
    row["working_capital"] = subtract_if_complete(
        get("current_assets"), get("current_liabilities")
    )
    row["cash_conversion"] = calculate_ratio(
        get("operating_cash_flow"), get("net_income")
    )

    return row


def build_analysis(series, start_year=2018):
    years = sorted({
        year for values in series.values() for year in values
    })
    displayed_years = [
        year for year in years if year >= start_year
    ]

    sales_key = "net_sales" if "net_sales" in series else "revenue"

    missing_reported_gross = any(
        series.get("gross_profit", {}).get(year) is None
        for year in displayed_years
    )

    complete_derivation_inputs = (
        bool(displayed_years)
        and all(
            series.get(sales_key, {}).get(year) is not None
            and series.get("cost_of_revenue", {}).get(year) is not None
            for year in displayed_years
        )
    )

    derive_consistently = (
        missing_reported_gross and complete_derivation_inputs
    )

    all_rows = {}

    for year in years:
        inputs = {
            key: values.get(year)
            for key, values in series.items()
        }

        row = calculate_year_metrics(
            inputs,
            derive_gross_profit=(
                derive_consistently and year >= start_year
            ),
        )
        row["year"] = year
        all_rows[year] = row

    for year, row in all_rows.items():
        previous = all_rows.get(year - 1, {})
        row["revenue_growth"] = calculate_growth(
            row.get("revenue"), previous.get("revenue")
        )
        row["fcf_growth"] = calculate_growth(
            row["fcf"], previous.get("fcf")
        )
        if (
            row["fcf"] is not None
            and previous.get("fcf") is not None
            and row["fcf_basis"] != previous.get("fcf_basis")
        ):
            row["fcf_growth"] = None
    return [
        row for year, row in all_rows.items()
        if year >= start_year
    ]
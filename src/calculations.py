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


def calculate_year_metrics(inputs):
    """Calculate each result once; None means an input/valid denominator is absent."""
    row = dict(inputs)
    get = inputs.get
    row["total_debt"] = calculate_total_debt(get("long_term_debt"), get("current_debt"), get("commercial_paper"))
    row["net_debt"] = calculate_net_debt(row["total_debt"], get("cash"))
    row["debt_to_equity"] = calculate_ratio(row["total_debt"], get("equity"))
    row["fcf"] = subtract_if_complete(get("operating_cash_flow"), get("capex"))
    row["net_margin"] = calculate_ratio(get("net_income"), get("revenue"))
    row["operating_margin"] = calculate_ratio(get("operating_income"), get("revenue"))
    row["gross_margin"] = calculate_ratio(get("gross_profit"), get("revenue"))
    row["fcf_margin"] = calculate_ratio(row["fcf"], get("revenue"))
    row["current_ratio"] = calculate_ratio(get("current_assets"), get("current_liabilities"))
    row["liquid_funds"] = sum_if_complete(get("cash"), get("short_term_investments"))
    row["quick_assets"] = sum_if_complete(row["liquid_funds"], get("receivables"))
    row["quick_ratio"] = calculate_ratio(row["quick_assets"], get("current_liabilities"))
    row["cash_ratio"] = calculate_ratio(row["liquid_funds"], get("current_liabilities"))
    row["working_capital"] = subtract_if_complete(get("current_assets"), get("current_liabilities"))
    row["cash_conversion"] = calculate_ratio(get("operating_cash_flow"), get("net_income"))
    return row


def build_analysis(series, start_year=2018):
    years = sorted({year for values in series.values() for year in values})
    all_rows = {}
    for year in years:
        row = calculate_year_metrics({key: values.get(year) for key, values in series.items()})
        row["year"] = year
        all_rows[year] = row
    for year, row in all_rows.items():
        previous = all_rows.get(year - 1, {})
        row["revenue_growth"] = calculate_growth(row.get("revenue"), previous.get("revenue"))
        row["fcf_growth"] = calculate_growth(row["fcf"], previous.get("fcf"))
    return [row for year, row in all_rows.items() if year >= start_year]

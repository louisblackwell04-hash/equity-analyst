"""Retrieve FMP balance sheets without changing analysis inputs."""

import requests


def get_annual_balance_sheets(ticker, api_key, limit=5):
    ticker = str(ticker).strip().upper()
    api_key = str(api_key or "").strip()

    if not ticker:
        raise ValueError("Provide a company ticker.")

    if not api_key:
        raise ValueError("Set FMP_API_KEY in the project's .env file.")

    if not isinstance(limit, int) or not 1 <= limit <= 5:
        raise ValueError("Request between 1 and 5 annual records.")

    try:
        response = requests.get(
            "https://financialmodelingprep.com/stable/balance-sheet-statement",
            params={
                "symbol": ticker,
                "period": "annual",
                "limit": limit,
                "apikey": api_key,
            },
            timeout=30,
        )
    except requests.RequestException:
        raise ValueError("Could not connect to FMP.") from None

    if response.status_code != 200:
        raise ValueError(
            f"FMP rejected the request: HTTP {response.status_code}."
        )

    try:
        records = response.json()
    except ValueError:
        raise ValueError("FMP returned an invalid response.") from None

    if not isinstance(records, list) or not records:
        raise ValueError(f"FMP returned no balance sheets for {ticker}.")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("FMP returned an invalid balance-sheet record.")

        if record.get("symbol") != ticker or record.get("period") != "FY":
            raise ValueError("FMP returned an unexpected company or period.")

    return records
def get_balance_candidates(records, period_end):
    """Prepare dated fallback values; do not apply them to SEC inputs."""
    from decimal import Decimal, InvalidOperation

    matches = [
        record for record in records
        if record.get("date") == period_end
    ]

    if not matches:
        return {}

    if len(matches) != 1:
        raise ValueError(f"Multiple FMP records found for {period_end}.")

    record = matches[0]

    if record.get("reportedCurrency") != "USD":
        raise ValueError("This release supports USD statements only.")

    fields = {
        "cash": "cashAndCashEquivalents",
        "short_term_investments": "shortTermInvestments",
    }

    candidates = {}

    for metric, field in fields.items():
        raw_value = record.get(field)

        if raw_value is None:
            continue

        try:
            value = Decimal(str(raw_value))
        except InvalidOperation:
            raise ValueError(f"Invalid FMP value for {field}.") from None

        if not value.is_finite() or value < 0:
            raise ValueError(f"Invalid FMP value for {field}.")

        candidates[metric] = {
            "value": value,
            "source": "FMP",
            "field": field,
            "ticker": record["symbol"],
            "period_end": period_end,
            "currency": "USD",
            "unit": "dollars",
        }

    return candidates
def fill_missing_balance_inputs(series, records, report_dates):
    """Fill missing cash/investments and record each fallback's source."""
    updated = {
        metric: dict(values)
        for metric, values in series.items()
    }
    sources = {}

    years = [int(date[:4]) for date in report_dates]

    if len(years) != len(set(years)):
        raise ValueError("Multiple reporting dates share the same year.")

    for period_end in report_dates:
        year = int(period_end[:4])
        candidates = get_balance_candidates(records, period_end)

        for metric, candidate in candidates.items():
            annual_values = updated.setdefault(metric, {})

            # A reported zero is an existing value.
            if annual_values.get(year) is not None:
                continue

            value = candidate["value"]

            if value != value.to_integral_value():
                raise ValueError(
                    f"FMP returned fractional dollars for {metric}."
                )

            annual_values[year] = int(value)

            details = dict(candidate)
            details["value"] = str(value)
            sources.setdefault(str(year), {})[metric] = details

    return updated, sources
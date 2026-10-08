"""Check whether standard inputs support a useful annual analysis."""


def check_data_compatibility(series, report_dates):
    if not report_dates:
        raise ValueError("No supported annual reporting periods were found.")

    years = [int(date[:4]) for date in report_dates]

    if len(years) != len(set(years)):
        raise ValueError(
            "Multiple annual periods end in the same calendar year. "
            "Fiscal-year labeling needs review."
        )

    latest_date = max(report_dates)
    latest_year = int(latest_date[:4])

    required = ("revenue", "net_income", "operating_cash_flow")

    missing = [
        metric
        for metric in required
        if series.get(metric, {}).get(latest_year) is None
    ]

    if missing:
        raise ValueError(
            f"Standard inputs are missing for {latest_date}: "
            + ", ".join(missing)
            + ". This company needs additional tag handling."
        )

    return {
        "status": "Core annual inputs available",
        "latest_period_end": latest_date,
    }
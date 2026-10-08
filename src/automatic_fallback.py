"""Automatic, cached SEC filing fallback for shared inputs."""

import json
from importlib.metadata import version
from pathlib import Path

if __package__:
    from .arelle_filing import read_processed_filing
    from .filing_fallback import get_annual_filing_documents
    from .filing_inputs import fill_from_filing
    from .sec_data import check_period_consistency
else:
    from arelle_filing import read_processed_filing
    from filing_fallback import get_annual_filing_documents
    from filing_inputs import fill_from_filing
    from sec_data import check_period_consistency


def fill_from_annual_filings(series, facts, dates, user_agent, cache_folder):
    if len({date[:4] for date in dates}) != len(dates):
        raise ValueError("Multiple annual reporting dates share one year.")

    cik = str(int(facts["cik"])).zfill(10)
    updated = {key: dict(values) for key, values in series.items()}
    sources = {}
    status = {"attempted": 0, "cached": 0, "errors": [], "rejected_inputs": {}}
    starts = {}

    checks = check_period_consistency(facts, dates)

    for period_end, check in checks.items():
        reported_starts = list(check["flow_start_dates"])
        if len(reported_starts) > 1:
            raise ValueError(f"Conflicting annual flow periods: {period_end}.")
        if reported_starts:
            starts[period_end] = reported_starts[0]

    def needs_filing(period_end):
        year = int(period_end[:4])

        def missing(metric):
            return updated.get(metric, {}).get(year) is None

        singles = (
            "revenue", "net_income", "operating_income",
            "operating_cash_flow", "cash", "equity",
            "current_assets", "current_liabilities",
            "short_term_investments",
            "long_term_debt", "current_debt", "short_term_debt",
        )
        alternatives = (
            ("gross_profit", "cost_of_revenue"),
            ("capex", "productive_asset_purchases"),
            ("receivables", "broader_current_receivables"),
        )

        return (
            any(missing(metric) for metric in singles)
            or any(all(missing(metric) for metric in group)
                   for group in alternatives)
        )

    if not any(needs_filing(date) for date in dates):
        return updated, sources, status

    documents = get_annual_filing_documents(
        cik, user_agent, min(int(date[:4]) for date in dates)
    )

    folder = Path(cache_folder) / cik
    folder.mkdir(parents=True, exist_ok=True)
    processor_version = version("arelle-release")

    for filing in documents:
        period_end = filing["period_end"]

        if period_end not in dates or not needs_filing(period_end):
            continue

        status["attempted"] += 1
        print(f"Checking original filing: {period_end}")

        path = folder / f'{filing["accession"]}.json'
        fingerprint = {
            "reader_version": 2,
            "processor_version": processor_version,
            "cik": cik,
            "url": filing["url"],
            "dates": sorted(dates),
        }
        records = None

        if path.exists():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
                if (
                    isinstance(cached, dict)
                    and cached.get("fingerprint") == fingerprint
                    and isinstance(cached.get("records"), list)
                    and all(
                        isinstance(record, dict)
                        and record.get("source_url") == filing["url"]
                        and record.get("accn") == filing["accession"]
                        for record in cached["records"]
                    )
                ):
                    records = cached["records"]
                    status["cached"] += 1
            except (ValueError, OSError):
                pass

        if records is None:
            try:
                records = read_processed_filing(
                    filing, cik, user_agent, dates
                )
            except ValueError as error:
                status["errors"].append({
                    "accession": filing["accession"],
                    "period_end": period_end,
                    "reason": str(error),
                })
                print(f"Filing extraction unavailable: {period_end}")
                continue

            path.write_text(json.dumps({
                "fingerprint": fingerprint,
                "records": records,
            }, indent=2) + "\n", encoding="utf-8")

        updated, additions, issues = fill_from_filing(
            updated, records, dates, expected_starts=starts
        )

        for year, entries in additions.items():
            sources.setdefault(year, {}).update(entries)
            for record in entries.values():
                if record.get("start") is not None:
                    starts[record["end"]] = record["start"]

        for year, entries in issues.items():
            status["rejected_inputs"].setdefault(year, {}).update(entries)

    return updated, sources, status
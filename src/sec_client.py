"""Run the financial analysis from saved facts or SEC downloads."""
import json
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from calculations import build_analysis
from company_config import (
    CIK,
    START_YEAR,
    COMMERCIAL_PAPER_OVERRIDES,
)
from company_lookup import find_company
from reporting import print_report, write_summary_csv
from sec_data import (
    extract_inputs,
    extract_inputs_for_dates,
    get_annual_report_dates,
    get_company_facts,
    load_company_facts,
)

PROJECT_FOLDER = Path(__file__).resolve().parents[1]
TEST_COMPANIES = {"MSFT", "AAPL", "WMT"}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a company financial summary."
    )
    parser.add_argument("--facts-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ticker", default="MSFT")
    args = parser.parse_args(argv)

    ticker = args.ticker.strip().upper()

    if args.facts_file:
        # Preserve the existing offline Microsoft baseline.
        facts = load_company_facts(args.facts_file)

        if ticker != "MSFT":
            raise ValueError(
                "Saved-file analysis currently supports the MSFT baseline only."
            )

        series = extract_inputs(facts)
        output = args.output or (
            PROJECT_FOLDER / "output" / "financial_summary.csv"
        )
    else:
        if ticker not in TEST_COMPANIES:
            raise ValueError(
                "This stage supports MSFT, AAPL and WMT. "
                "Broader ticker coverage is still being developed."
            )

        load_dotenv(PROJECT_FOLDER / ".env")
        user_agent = os.getenv("SEC_USER_AGENT")
        company = find_company(ticker, user_agent)

        print(f'Company: {company["name"]} ({ticker})')

        facts = get_company_facts(company["cik"], user_agent)
        dates = get_annual_report_dates(
            company["cik"], user_agent, START_YEAR
        )

        if not dates:
            raise ValueError("No annual report dates were found.")

        series = extract_inputs_for_dates(facts, dates, ticker)

        if ticker == "MSFT":
            if company["cik"] != CIK:
                raise ValueError("Microsoft company ID does not match.")

            for year, override in COMMERCIAL_PAPER_OVERRIDES.items():
                if year in series["commercial_paper"]:
                    if series["commercial_paper"][year] is None:
                        series["commercial_paper"][year] = override["value"]

            print(
                "Note: Microsoft retains documented manual "
                "commercial-paper assumptions pending filing validation."
            )

        if ticker == "WMT":
            print(
                "Note: gross profit is derived from total revenue minus "
                "cost of revenue. Receivables include broader current "
                "receivables. Missing investments remain unavailable."
            )

        output = args.output or (
            PROJECT_FOLDER / "output" / ticker / "financial_summary.csv"
        )

    rows = build_analysis(series, START_YEAR)
    print_report(rows, ticker=ticker)
    path = write_summary_csv(rows, output)

    if args.facts_file:
        report_dates = [
            f'{row["year"]}-06-30' for row in rows
        ]
    else:
        report_dates = dates

    notes = []

    if ticker == "MSFT":
        notes.append(
            "Commercial-paper zeros for 2020–2022 and 2026 "
            "include inherited manual assumptions pending validation."
        )

    if ticker == "WMT":
        notes.append(
            "Gross profit is derived from total revenue minus "
            "cost of revenue. Current receivables include broader "
            "receivables. Missing investments remain unavailable."
        )
    missing_inputs = {}

    for row in rows:
        year = row["year"]

        missing = [
            metric
            for metric, annual_values in series.items()
            if annual_values.get(year) is None
        ]

        if missing:
            missing_inputs[str(year)] = missing
        unavailable_results = {}

    for row in rows:
        reasons = {}

        if row.get("short_term_investments") is None:
            reasons["quick_ratio"] = "Missing short-term investment data."
            reasons["cash_ratio"] = "Missing short-term investment data."

        if row.get("receivables") is None:
            reasons["quick_ratio"] = "Missing receivables data."

        liabilities = row.get("current_liabilities")

        if liabilities is None or liabilities <= 0:
            reason = (
                "Missing current liabilities."
                if liabilities is None
                else "Current liabilities are zero or negative."
            )
            reasons["current_ratio"] = reason
            reasons["quick_ratio"] = reason
            reasons["cash_ratio"] = reason

        if row.get("cash") is None:
            reasons["quick_ratio"] = "Missing cash data."
            reasons["cash_ratio"] = "Missing cash data."

        if row.get("current_assets") is None:
            reasons["current_ratio"] = "Missing current assets."

        if reasons:
            unavailable_results[str(row["year"])] = reasons
    metadata = {
        "ticker": ticker,
        "company_name": facts["entityName"],
        "cik": str(facts["cik"]).zfill(10),
        "period_ends": {
            date[:4]: date for date in report_dates
        },
        "notes": notes,
        "missing_inputs": missing_inputs,
        "unavailable_results": unavailable_results,
    }

    metadata_path = path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nSaved: {path}")
    return rows


if __name__ == "__main__":
    main()
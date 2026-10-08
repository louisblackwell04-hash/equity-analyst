"""Run the financial analysis from saved facts or SEC downloads."""
from company_eligibility import check_company_eligibility
from data_compatibility import check_data_compatibility
import sys
import json
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv, dotenv_values
from fmp_data import (
    get_annual_balance_sheets,
    fill_missing_balance_inputs,
)
from calculations import build_analysis
from company_config import (
    CIK,
    START_YEAR,
    COMMERCIAL_PAPER_OVERRIDES,
)
from company_lookup import find_company
from reviewed_inputs import fill_reviewed_inputs
from reporting import print_report, write_summary_csv
from sec_data import (
    get_company_submissions,
    check_period_consistency,
    extract_inputs,
    extract_inputs_for_dates,
    get_annual_report_dates,
    get_company_facts,
    load_company_facts,
)

PROJECT_FOLDER = Path(__file__).resolve().parents[1]

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a company financial summary."
    )
    parser.add_argument("--facts-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ticker", default="MSFT")
    parser.add_argument(
        "--use-fmp",
        action="store_true",
        help="Use FMP to fill missing cash and short-term investments.",
    )
    args = parser.parse_args(argv)

    ticker = args.ticker.strip().upper()
    period_checks = {}
    compatibility = {"status": "Legacy offline baseline"}
    fmp_sources = {}
    reviewed_sources = {}

    if args.facts_file and args.use_fmp:
        raise ValueError(
            "FMP fallback is unavailable for the legacy offline baseline."
        )
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


        load_dotenv(PROJECT_FOLDER / ".env")
        user_agent = os.getenv("SEC_USER_AGENT")
        company = find_company(ticker, user_agent)

        print(f'Company: {company["name"]} ({ticker})')

        facts = get_company_facts(company["cik"], user_agent)
        submissions = get_company_submissions(
            company["cik"], user_agent
        )
        eligibility = check_company_eligibility(
            submissions, facts
        )

        print(f'Industry: {eligibility["industry"]}')
        dates = get_annual_report_dates(
            company["cik"], user_agent, START_YEAR
        )

        if not dates:
            raise ValueError("No annual report dates were found.")

        series = extract_inputs_for_dates(facts, dates, ticker)
        reviewed_path = (
            PROJECT_FOLDER / "data" / "reviewed_inputs.json"
        )

        if reviewed_path.exists():
            series, reviewed_sources = fill_reviewed_inputs(
                series,
                reviewed_path,
                ticker,
                company["cik"],
                dates,
            )

            reviewed_count = sum(
                len(values) for values in reviewed_sources.values()
            )
            print(
                f"Reviewed SEC fallback: "
                f"{reviewed_count} missing inputs filled."
            )

        if args.use_fmp:
            api_key = dotenv_values(
                PROJECT_FOLDER / ".env"
            ).get("FMP_API_KEY")

            fmp_records = get_annual_balance_sheets(
                ticker, api_key, limit=5
            )

            series, fmp_sources = fill_missing_balance_inputs(
                series, fmp_records, dates
            )

            fallback_count = sum(
                len(values) for values in fmp_sources.values()
            )
            print(f"FMP fallback: {fallback_count} missing inputs filled.")

        compatibility = check_data_compatibility(series, dates)
        period_checks = check_period_consistency(
            facts, dates, ticker
        )

        conflicting_dates = [
            date
            for date, check in period_checks.items()
            if check["different_flow_periods"]
        ]

        if conflicting_dates:
            raise ValueError(
                "Annual inputs cover different flow periods: "
                + ", ".join(conflicting_dates)
            )

        if ticker == "MSFT":
            if company["cik"] != CIK:
                raise ValueError("Microsoft company ID does not match.")

            print(
                "Note: missing commercial-paper balances are not "
                "assumed to be zero. Dependent debt results remain "
                "unavailable."
            )

        if ticker == "WMT":
            print(
                "Note: gross profit is derived from net sales minus "
                "cost of revenue. Receivables include broader current "
                "receivables. Unresolved investment balances remain unavailable."
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
    if reviewed_sources:
        notes.append(
            "Some missing inputs were supplied from reviewed SEC "
            "disclosures. Company identity, reporting date, filing "
            "reference and supporting evidence are recorded "
            "in reviewed_sources."
        )
    if any(
        row.get("fcf") is not None
        and row.get("fcf_basis") == (
            "Property, equipment, software and intangible asset purchases"
        )
        for row in rows
    ):
        notes.append(
            "Calculated free cash flow uses operating cash flow minus "
            "asset purchases. Some periods include software and intangible "
            "assets. Separate financing principal payments are not deducted; "
            "this may differ from company-reported free cash flow."
        )
    if fmp_sources:
        notes.append(
            "Some missing cash or short-term investment inputs "
            "were supplied by FMP using matching reporting dates "
            "and USD currency. Details are recorded in fmp_sources."
        )

    if ticker == "MSFT":
        if args.facts_file:
            notes.append(
                "The legacy offline baseline includes manual "
                "commercial-paper assumptions."
            )
        else:
            notes.append(
                "Missing commercial-paper balances are not assumed "
                "to be zero. Dependent debt results are unavailable."
            )

    if ticker == "WMT":
        notes.append(
            "Gross profit is derived from net sales minus "
            "cost of revenue. Current receivables include broader "
            "receivables. Unresolved investment balances remain unavailable."
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
        debt_input = (
            "short_term_debt"
            if "short_term_debt" in row
            else "commercial_paper"
        )

        missing_debt = [
            metric
            for metric in ("long_term_debt", "current_debt", debt_input)
            if row.get(metric) is None
        ]

        if missing_debt:
            reason = "Missing debt inputs: " + ", ".join(missing_debt)

            for metric in ("total_debt", "net_debt", "debt_to_equity"):
                reasons[metric] = reason

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
         "gross_profit_basis": {
            str(row["year"]): row.get("gross_profit_basis", "Unavailable")
            for row in rows
        },
        "ticker": ticker,
        "company_name": facts["entityName"],
        "cik": str(facts["cik"]).zfill(10),
        "period_ends": {
            date[:4]: date for date in report_dates
        },
        "notes": notes,
        "fcf_basis": {
            str(row["year"]): row["fcf_basis"]
            for row in rows
        },
        "fmp_sources": fmp_sources,
        "reviewed_sources": reviewed_sources,
        "missing_inputs": missing_inputs,
        "unavailable_results": unavailable_results,
        "period_checks": period_checks,
        "data_compatibility": compatibility,
    }

    metadata_path = path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nSaved: {path}")
    return rows


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)

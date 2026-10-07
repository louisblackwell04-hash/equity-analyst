"""Compare extracted inputs with independently reviewed annual filings."""
import argparse
import csv
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from company_config import get_company_concepts
from sec_data import get_company_facts, get_financial_records

PROJECT_FOLDER = Path(__file__).resolve().parents[1]

# Half of the filings' displayed USD-million precision.
TOLERANCE = Decimal("0.5")

REFERENCES = {
    "AAPL": {
        "cik": "0000320193",
        "file": "aapl_2025_10k_reference.csv",
        "source": (
            "https://www.sec.gov/Archives/edgar/data/320193/"
            "000032019325000079/aapl-20250927.htm"
        ),
        "income_page": 29,
        "balance_page": 31,
        "cash_flow_page": 33,
    },
    "MSFT": {
        "cik": "0000789019",
        "file": "msft_2026_10k_reference.csv",
        "source": (
            "https://www.sec.gov/Archives/edgar/data/789019/"
            "000119312526323660/msft-20260630.htm"
        ),
        "income_page": 50,
        "balance_page": 52,
        "cash_flow_page": 53,
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate inputs against reviewed annual filings."
    )
    parser.add_argument(
        "--ticker",
        type=str.upper,
        choices=REFERENCES,
        default="AAPL",
    )
    args = parser.parse_args()
    ticker = args.ticker
    reference_info = REFERENCES[ticker]

    load_dotenv(PROJECT_FOLDER / ".env")

    reference_path = (
        PROJECT_FOLDER / "tests" / "fixtures" / reference_info["file"]
    )

    with reference_path.open(newline="") as file:
        references = list(csv.DictReader(file))

    dates = [row["period_end"] for row in references]
    facts = get_company_facts(
        reference_info["cik"], os.getenv("SEC_USER_AGENT")
    )
    flows, balances = get_company_concepts(ticker)
    records = get_financial_records(
        facts, dates, flows, balances
    )

    income_metrics = {
        "revenue", "net_income", "operating_income", "gross_profit"
    }
    cash_flow_metrics = {"operating_cash_flow", "capex"}
    checks = []

    for reference in references:
        date = reference["period_end"]

        for metric, expected_text in reference.items():
            if metric == "period_end":
                continue

            expected = Decimal(expected_text)
            record = records[metric][date]

            if record is None:
                actual = ""
                difference = ""
                status = "MISSING"
                accession = ""
            else:
                actual = Decimal(str(record["val"])) / Decimal("1000000")
                difference = actual - expected
                status = (
                    "PASS"
                    if abs(difference) <= TOLERANCE
                    else "MISMATCH"
                )
                accession = record["accn"]

            if metric in income_metrics:
                page = reference_info["income_page"]
            elif metric in cash_flow_metrics:
                page = reference_info["cash_flow_page"]
            else:
                page = reference_info["balance_page"]

            checks.append({
                "period_end": date,
                "metric": metric,
                "expected_usd_millions": expected,
                "actual_usd_millions": actual,
                "difference_usd_millions": difference,
                "status": status,
                "extracted_filing": accession,
                "reference_page": page,
                "reference_source": reference_info["source"],
            })

    output = PROJECT_FOLDER / "output" / ticker / "validation.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(checks[0]))
        writer.writeheader()
        writer.writerows(checks)

    failures = [check for check in checks if check["status"] != "PASS"]

    print(
        f"{ticker} filing checks: "
        f"{len(checks) - len(failures)}/{len(checks)} passed"
    )

    for check in failures:
        print(
            check["period_end"],
            check["metric"],
            check["status"],
            check["difference_usd_millions"],
        )

    print(f"Saved: {output}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
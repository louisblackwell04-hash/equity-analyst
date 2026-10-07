"""Compare Apple's extracted inputs with its 2025 annual filing."""
import csv
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from company_config import get_company_concepts
from sec_data import get_company_facts, get_financial_records

PROJECT_FOLDER = Path(__file__).resolve().parents[1]

REFERENCE_SOURCE = (
    "https://www.sec.gov/Archives/edgar/data/320193/"
    "000032019325000079/aapl-20250927.htm"
)

# Half of the filing's displayed USD-million precision.
TOLERANCE = Decimal("0.5")

SOURCE_PAGES = {
    "revenue": 29,
    "net_income": 29,
    "operating_income": 29,
    "gross_profit": 29,
    "operating_cash_flow": 33,
    "capex": 33,
}


def main():
    load_dotenv(PROJECT_FOLDER / ".env")

    reference_path = (
        PROJECT_FOLDER
        / "tests"
        / "fixtures"
        / "aapl_2025_10k_reference.csv"
    )

    with reference_path.open(newline="") as file:
        references = list(csv.DictReader(file))

    dates = [row["period_end"] for row in references]
    facts = get_company_facts(
        "0000320193", os.getenv("SEC_USER_AGENT")
    )
    flows, balances = get_company_concepts("AAPL")
    records = get_financial_records(
        facts, dates, flows, balances
    )

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

            checks.append({
                "period_end": date,
                "metric": metric,
                "expected_usd_millions": expected,
                "actual_usd_millions": actual,
                "difference_usd_millions": difference,
                "status": status,
                "extracted_filing": accession,
                "reference_page": SOURCE_PAGES.get(metric, 31),
                "reference_source": REFERENCE_SOURCE,
            })

    output = PROJECT_FOLDER / "output" / "AAPL" / "validation.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(checks[0]))
        writer.writeheader()
        writer.writerows(checks)

    failures = [check for check in checks if check["status"] != "PASS"]

    print(f"Apple filing checks: {len(checks) - len(failures)}/{len(checks)} passed")

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
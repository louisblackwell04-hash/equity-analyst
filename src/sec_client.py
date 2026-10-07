"""Run the Microsoft analysis; reusable functions live in the supporting modules."""
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from calculations import build_analysis
from company_config import CIK, START_YEAR
from reporting import print_report, write_summary_csv
from sec_data import extract_inputs, get_company_facts, load_company_facts

PROJECT_FOLDER = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the Microsoft financial summary.")
    parser.add_argument("--facts-file", type=Path, help="Use saved public company facts instead of downloading.")
    parser.add_argument("--output", type=Path, default=PROJECT_FOLDER / "output" / "financial_summary.csv")
    args = parser.parse_args(argv)
    if args.facts_file:
        facts = load_company_facts(args.facts_file)
    else:
        load_dotenv(PROJECT_FOLDER / ".env")
        facts = get_company_facts(CIK, os.getenv("SEC_USER_AGENT"))
    rows = build_analysis(extract_inputs(facts), START_YEAR)
    print_report(rows)
    path = write_summary_csv(rows, args.output)
    print(f"\nSaved: {path}")
    return rows


if __name__ == "__main__":
    main()

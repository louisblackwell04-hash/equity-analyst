"""Offline regression and edge-case checks; no SEC credentials required."""
import contextlib
import importlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from calculations import (build_analysis, calculate_net_debt, calculate_ratio,
                          calculate_total_debt, calculate_year_metrics)
from reporting import print_report, write_summary_csv
from sec_data import extract_inputs, get_annual_facts, get_year_end_balances, load_company_facts

FIXTURES = ROOT / "tests" / "fixtures"


def sections(text):
    """Compare headings and numeric results, not spacing or the output filename."""
    result = {}
    heading = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("Saved:"):
            continue
        if line[:4].isdigit():
            result[heading].append(line)
        else:
            heading = line
            result[heading] = []
    return result


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = load_company_facts(FIXTURES / "msft_companyfacts_baseline.json")
        cls.rows = build_analysis(extract_inputs(cls.facts))

    def test_csv_matches_original_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_summary_csv(self.rows, Path(directory) / "report.csv")
            self.assertEqual(path.read_bytes(), (FIXTURES / "msft_v1_summary.csv").read_bytes())

    def test_every_terminal_section_matches_original(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_report(self.rows)
        self.assertEqual(sections(output.getvalue()), sections((FIXTURES / "msft_v1_terminal.txt").read_text()))

    def test_zero_is_not_missing(self):
        self.assertEqual(calculate_total_debt(100, 20, 0), 120)
        self.assertIsNone(calculate_total_debt(100, 20, None))
        self.assertEqual(calculate_ratio(0, 100), 0)
        self.assertEqual(calculate_net_debt(0, 50), -50)

    def test_invalid_denominators(self):
        for denominator in (None, 0, -1):
            self.assertIsNone(calculate_ratio(100, denominator))
        self.assertIsNone(calculate_ratio(None, 100))
        self.assertEqual(calculate_ratio(-50, 100), -0.5)

    def test_missing_input_only_affects_dependent_metrics(self):
        row = calculate_year_metrics({"cash": 20, "short_term_investments": 30,
            "current_assets": 100, "current_liabilities": 50, "equity": 200,
            "long_term_debt": 80, "current_debt": 10, "commercial_paper": 0})
        self.assertEqual(row["total_debt"], 90)
        self.assertEqual(row["net_debt"], 70)
        self.assertEqual(row["current_ratio"], 2)
        self.assertEqual(row["cash_ratio"], 1)
        self.assertIsNone(row["quick_ratio"])  # Receivables absent, not zero.
        self.assertIsNone(row["cash_conversion"])

    def test_growth_does_not_bridge_missing_year(self):
        rows = build_analysis({"revenue": {2020: 100, 2022: 150, 2023: 180}})
        self.assertIsNone(rows[1]["revenue_growth"])
        self.assertAlmostEqual(rows[2]["revenue_growth"], 0.2)

    def test_negative_fcf_is_preserved(self):
        row = calculate_year_metrics({"operating_cash_flow": 10, "capex": 20, "revenue": 100})
        self.assertEqual(row["fcf"], -10)
        self.assertEqual(row["fcf_margin"], -0.1)

    def test_exports_retain_years_with_missing_cash(self):
        rows = build_analysis({"equity": {2024: 200}, "cash": {}})
        self.assertEqual(rows[0]["year"], 2024)
        with tempfile.TemporaryDirectory() as directory:
            path = write_summary_csv(rows, Path(directory) / "report.csv")
            self.assertIn("2024,,", path.read_text())

    def test_balance_date_and_latest_filing(self):
        items = [
            {"end": "2023-06-30", "fy": 2024, "form": "10-K", "filed": "2024-07-30", "val": 5},
            {"end": "2023-06-30", "fy": 2023, "form": "10-K", "filed": "2023-07-30", "val": 4},
            {"end": "2023-09-30", "fy": 2024, "form": "10-Q", "filed": "2024-01-01", "val": 8},
        ]
        facts = {"facts": {"us-gaap": {"Cash": {"units": {"USD": items}}}}}
        self.assertEqual(get_year_end_balances(facts, "Cash")[2023]["val"], 5)
        self.assertEqual(len(get_year_end_balances(facts, "Cash")), 1)

    def test_flow_duration_filter_is_preserved(self):
        items = [
            {"start": "2023-07-01", "end": "2024-06-30", "fy": 2024, "form": "10-K", "val": 100},
            {"start": "2024-04-01", "end": "2024-06-30", "fy": 2024, "form": "10-K", "val": 20},
        ]
        facts = {"facts": {"us-gaap": {"Revenue": {"units": {"USD": items}}}}}
        self.assertEqual(get_annual_facts(facts, "Revenue"), [items[0]])

    def test_wrong_company_cannot_receive_msft_overrides(self):
        with self.assertRaisesRegex(ValueError, "Microsoft only"):
            extract_inputs({"cik": 320193})

    def test_imports_have_no_network_or_output_side_effects(self):
        with patch("requests.get", side_effect=AssertionError("Unexpected network request")), \
             patch("xlsxwriter.Workbook", side_effect=AssertionError("Unexpected report write")):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                importlib.import_module("sec_client")
                importlib.import_module("excel_report")
            self.assertEqual(output.getvalue(), "")

    def test_cli_works_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary.csv"
            result = subprocess.run([sys.executable, str(ROOT / "src/sec_client.py"),
                "--facts-file", str(FIXTURES / "msft_companyfacts_baseline.json"),
                "--output", str(output)], cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), (FIXTURES / "msft_v1_summary.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()

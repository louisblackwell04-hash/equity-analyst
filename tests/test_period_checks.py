import unittest
from unittest.mock import patch

from src.sec_data import check_period_consistency


def make_record(start, accession):
    return {
        "start": start,
        "end": "2025-09-27",
        "form": "10-K",
        "filed": "2025-10-30",
        "accn": accession,
        "val": 100,
    }


class PeriodCheckTests(unittest.TestCase):
    def run_check(self, revenue, cash_flow):
        facts = {
            "facts": {
                "us-gaap": {
                    "Revenue": {"units": {"USD": [revenue]}},
                    "CashFlow": {"units": {"USD": [cash_flow]}},
                }
            }
        }

        concepts = (
            {
                "revenue": "Revenue",
                "operating_cash_flow": "CashFlow",
            },
            {},
        )

        with patch(
            "src.company_config.get_company_concepts",
            return_value=concepts,
        ):
            checks = check_period_consistency(
                facts, ["2025-09-27"], "AAPL"
            )

        return checks["2025-09-27"]

    def test_different_flow_periods_are_flagged(self):
        check = self.run_check(
            make_record("2024-09-29", "filing-one"),
            make_record("2024-10-01", "filing-one"),
        )

        self.assertTrue(check["different_flow_periods"])
        self.assertFalse(check["multiple_filings"])

    def test_multiple_filings_are_distinct_from_period_conflicts(self):
        check = self.run_check(
            make_record("2024-09-29", "filing-one"),
            make_record("2024-09-29", "filing-two"),
        )

        self.assertFalse(check["different_flow_periods"])
        self.assertTrue(check["multiple_filings"])


if __name__ == "__main__":
    unittest.main()
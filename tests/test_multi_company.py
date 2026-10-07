import unittest

from src.calculations import calculate_year_metrics
from src.company_config import get_company_concepts
from src.sec_data import (
    get_balances_for_dates,
    get_flows_for_dates,
)


def make_facts(concept, records):
    return {
        "facts": {
            "us-gaap": {
                concept: {"units": {"USD": records}}
            }
        }
    }


class MultiCompanyTests(unittest.TestCase):
    def test_exact_date_and_latest_amendment(self):
        records = [
            {
                "end": "2025-09-27",
                "form": "10-K",
                "filed": "2025-10-30",
                "accn": "original",
                "val": 100,
            },
            {
                "end": "2025-09-27",
                "form": "10-K/A",
                "filed": "2025-11-30",
                "accn": "amended",
                "val": 110,
            },
            {
                "end": "2025-06-30",
                "form": "10-K",
                "filed": "2025-12-01",
                "accn": "different-period",
                "val": 999,
            },
        ]

        selected = get_balances_for_dates(
            make_facts("Cash", records),
            "Cash",
            ["2025-09-27"],
        )

        self.assertEqual(selected["2025-09-27"]["val"], 110)

    def test_annual_flow_excludes_quarter(self):
        annual = {
            "start": "2022-09-25",
            "end": "2023-09-30",
            "form": "10-K",
            "filed": "2023-11-01",
            "accn": "annual",
            "val": 100,
        }
        quarter = {
            "start": "2023-07-02",
            "end": "2023-09-30",
            "form": "10-K",
            "filed": "2023-12-01",
            "accn": "quarter",
            "val": 25,
        }

        selected = get_flows_for_dates(
            make_facts("Revenue", [annual, quarter]),
            "Revenue",
            ["2023-09-30"],
        )

        self.assertEqual(selected["2023-09-30"]["val"], 100)

    def test_missing_balance_is_not_zero(self):
        selected = get_balances_for_dates(
            make_facts("Cash", []),
            "Cash",
            ["2025-01-31"],
        )

        self.assertIsNone(selected["2025-01-31"])

    def test_short_term_borrowings_are_not_double_counted(self):
        row = calculate_year_metrics({
            "long_term_debt": 100,
            "current_debt": 20,
            "short_term_debt": 30,
            "commercial_paper": 10,
        })

        self.assertEqual(row["total_debt"], 150)

    def test_missing_borrowings_do_not_fall_back_to_commercial_paper(self):
        row = calculate_year_metrics({
            "long_term_debt": 100,
            "current_debt": 20,
            "short_term_debt": None,
            "commercial_paper": 10,
        })

        self.assertIsNone(row["total_debt"])

    def test_company_mappings_do_not_modify_each_other(self):
        _, apple = get_company_concepts("AAPL")
        _, microsoft = get_company_concepts("MSFT")

        self.assertEqual(
            apple["short_term_investments"],
            "MarketableSecuritiesCurrent",
        )
        self.assertEqual(
            microsoft["short_term_investments"],
            "ShortTermInvestments",
        )

    def test_derived_gross_profit_is_identified(self):
        row = calculate_year_metrics({
            "revenue": 100,
            "cost_of_revenue": 75,
        })

        self.assertEqual(row["gross_profit"], 25)
        self.assertEqual(row["gross_margin"], 0.25)
        self.assertEqual(
            row["gross_profit_basis"],
            "Derived: total revenue minus cost of revenue",
        )


if __name__ == "__main__":
    unittest.main()
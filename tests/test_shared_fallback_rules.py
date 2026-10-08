import copy
import json
import unittest
from pathlib import Path

from src.calculations import calculate_year_metrics
from src.custom_concepts import classify_custom_fact
from src.filing_inputs import fill_from_filing


class SharedFallbackTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / "fixtures" / "custom_asset_purchase.json"
        self.record = json.loads(path.read_text())
        self.end = self.record["end"]
        self.year = int(self.end[:4])

    def merge(self, records, existing=None, starts=None):
        series = {
            "productive_asset_purchases": {self.year: existing}
        }
        return fill_from_filing(
            series, records, [self.end], expected_starts=starts
        )

    def test_reviewed_custom_meaning_is_recognized(self):
        self.assertEqual(
            classify_custom_fact(self.record),
            "productive_asset_purchases",
        )

    def test_changed_meaning_is_not_recognized(self):
        self.record["definition"] = (
            "Does not represent " + self.record["definition"]
        )
        self.assertIsNone(classify_custom_fact(self.record))

    def test_wrong_calculation_parent_is_rejected(self):
        for parent in self.record["calculation_parents"]:
            parent["concept"] = "NetCashProvidedByUsedInOperatingActivities"
        self.assertIsNone(classify_custom_fact(self.record))

    def test_wrong_type_or_balance_is_rejected(self):
        for field, value in (
            ("is_monetary", False),
            ("period_type", "instant"),
            ("balance", "debit"),
        ):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                record[field] = value
                self.assertIsNone(classify_custom_fact(record))

    def test_custom_input_retains_filing_source(self):
        updated, sources, issues = self.merge([self.record])
        self.assertEqual(
            updated["productive_asset_purchases"][self.year],
            self.record["val"],
        )
        self.assertEqual(
            sources[str(self.year)]["productive_asset_purchases"]["accn"],
            self.record["accn"],
        )
        self.assertEqual(issues, {})

    def test_existing_zero_is_preserved(self):
        updated, sources, issues = self.merge([self.record], existing=0)
        self.assertEqual(
            updated["productive_asset_purchases"][self.year], 0
        )
        self.assertEqual(sources, {})

    def test_conflicting_custom_values_are_rejected(self):
        other = {**self.record, "val": self.record["val"] + 1}
        updated, sources, issues = self.merge([self.record, other])
        self.assertIsNone(
            updated["productive_asset_purchases"][self.year]
        )
        self.assertIn(
            "productive_asset_purchases", issues[str(self.year)]
        )

    def test_quarterly_and_mismatched_flows_are_rejected(self):
        quarter = {**self.record, "start": self.end[:4] + "-01-01"}
        updated, sources, issues = self.merge([quarter])
        self.assertIsNone(
            updated["productive_asset_purchases"][self.year]
        )

        updated, sources, issues = self.merge(
            [self.record],
            starts={self.end: "2020-01-28"},
        )
        self.assertIsNone(
            updated["productive_asset_purchases"][self.year]
        )
        self.assertIn(
            "productive_asset_purchases", issues[str(self.year)]
        )

    def test_equal_current_debt_reconciles_additional_debt(self):
        row = calculate_year_metrics({
            "long_term_debt": 100,
            "current_debt": 20,
            "short_term_debt": None,
            "current_debt_total_including_finance_leases": 20,
        })
        self.assertEqual(row["total_debt"], 120)

    def test_uncertain_current_debt_is_not_assumed_zero(self):
        for aggregate in (None, 25):
            with self.subTest(aggregate=aggregate):
                row = calculate_year_metrics({
                    "long_term_debt": 100,
                    "current_debt": 20,
                    "short_term_debt": None,
                    "current_debt_total_including_finance_leases": aggregate,
                })
                self.assertIsNone(row["total_debt"])

    def test_customer_receivables_take_priority_over_broader_balances(self):
        row = calculate_year_metrics({
            "cash": 10,
            "short_term_investments": 20,
            "current_liabilities": 100,
            "receivables": 0,
            "broader_current_receivables": 30,
        })
        self.assertEqual(row["quick_ratio"], 0.3)
        self.assertEqual(
            row["receivables_basis"], "Customer accounts receivable"
        )


if __name__ == "__main__":
    unittest.main()

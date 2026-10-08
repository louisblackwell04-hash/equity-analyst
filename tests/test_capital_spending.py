import unittest

from src.calculations import build_analysis, calculate_year_metrics


class CapitalSpendingTests(unittest.TestCase):
    def test_existing_capex_takes_priority(self):
        row = calculate_year_metrics({
            "operating_cash_flow": 100,
            "capex": 20,
            "productive_asset_purchases": 30,
        })
        self.assertEqual(row["fcf"], 80)
        self.assertEqual(row["capital_spending_used"], 20)

    def test_zero_capex_is_preserved(self):
        row = calculate_year_metrics({
            "operating_cash_flow": 100,
            "capex": 0,
            "productive_asset_purchases": 30,
        })
        self.assertEqual(row["fcf"], 100)
        self.assertEqual(row["capital_spending_used"], 0)

    def test_broader_spending_fills_missing_capex(self):
        row = calculate_year_metrics({
            "operating_cash_flow": 100,
            "capex": None,
            "productive_asset_purchases": 30,
        })
        self.assertEqual(row["fcf"], 70)
        self.assertIn("intangible", row["fcf_basis"])

    def test_missing_spending_remains_unavailable(self):
        row = calculate_year_metrics({
            "operating_cash_flow": 100,
        })
        self.assertIsNone(row["fcf"])

    def test_negative_free_cash_flow_is_preserved(self):
        row = calculate_year_metrics({
            "operating_cash_flow": 20,
            "productive_asset_purchases": 30,
        })
        self.assertEqual(row["fcf"], -10)

    def test_growth_requires_matching_spending_basis(self):
        rows = build_analysis({
            "operating_cash_flow": {2024: 100, 2025: 120},
            "capex": {2024: 20, 2025: None},
            "productive_asset_purchases": {2024: 30, 2025: 30},
        }, start_year=2024)

        self.assertEqual(rows[0]["fcf"], 80)
        self.assertEqual(rows[1]["fcf"], 90)
        self.assertIsNone(rows[1]["fcf_growth"])

    def test_growth_calculates_when_basis_matches(self):
        rows = build_analysis({
            "operating_cash_flow": {2024: 100, 2025: 120},
            "productive_asset_purchases": {2024: 20, 2025: 20},
        }, start_year=2024)

        self.assertAlmostEqual(rows[1]["fcf_growth"], 0.25)


if __name__ == "__main__":
    unittest.main()
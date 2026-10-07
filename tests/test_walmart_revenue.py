import unittest

from src.calculations import calculate_year_metrics


class WalmartRevenueTests(unittest.TestCase):
    def test_gross_margin_uses_net_sales(self):
        row = calculate_year_metrics({
            "revenue": 100,
            "net_sales": 80,
            "cost_of_revenue": 60,
            "net_income": 10,
        })

        self.assertEqual(row["gross_profit"], 20)
        self.assertEqual(row["gross_margin"], 0.25)
        self.assertEqual(row["net_margin"], 0.10)
        self.assertEqual(
            row["gross_profit_basis"],
            "Derived: net sales minus cost of revenue",
        )

    def test_missing_net_sales_does_not_use_total_revenue(self):
        row = calculate_year_metrics({
            "revenue": 100,
            "net_sales": None,
            "cost_of_revenue": 60,
        })

        self.assertIsNone(row["gross_profit"])
        self.assertIsNone(row["gross_margin"])


if __name__ == "__main__":
    unittest.main()
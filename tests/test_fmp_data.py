import unittest

from src.fmp_data import fill_missing_balance_inputs


class FMPFallbackTests(unittest.TestCase):
    def setUp(self):
        self.records = [{
            "symbol": "TEST",
            "date": "2025-12-31",
            "reportedCurrency": "USD",
            "period": "FY",
            "cashAndCashEquivalents": 100,
            "shortTermInvestments": 200,
        }]
        self.dates = ["2025-12-31"]

    def test_missing_values_are_filled_with_sources(self):
        updated, sources = fill_missing_balance_inputs(
            {"cash": {2025: None}},
            self.records,
            self.dates,
        )
        self.assertEqual(updated["cash"][2025], 100)
        self.assertEqual(
            sources["2025"]["cash"]["source"], "FMP"
        )
        self.assertEqual(
            sources["2025"]["cash"]["period_end"], self.dates[0]
        )

    def test_existing_values_and_zero_are_preserved(self):
        original = {
            "cash": {2025: 50},
            "short_term_investments": {2025: 0},
        }
        updated, sources = fill_missing_balance_inputs(
            original, self.records, self.dates
        )
        self.assertEqual(updated, original)
        self.assertEqual(sources, {})

    def test_original_inputs_are_unchanged(self):
        original = {"cash": {2025: None}}
        fill_missing_balance_inputs(
            original, self.records, self.dates
        )
        self.assertEqual(original, {"cash": {2025: None}})

    def test_different_date_is_not_used(self):
        updated, sources = fill_missing_balance_inputs(
            {}, self.records, ["2024-12-31"]
        )
        self.assertEqual(updated, {})
        self.assertEqual(sources, {})

    def test_non_usd_record_is_rejected(self):
        self.records[0]["reportedCurrency"] = "EUR"
        with self.assertRaises(ValueError):
            fill_missing_balance_inputs(
                {}, self.records, self.dates
            )

    def test_duplicate_period_is_rejected(self):
        self.records.append(dict(self.records[0]))
        with self.assertRaises(ValueError):
            fill_missing_balance_inputs(
                {}, self.records, self.dates
            )

    def test_invalid_amounts_are_rejected(self):
        for value in [-1, "NaN", "Infinity", "invalid", "100.5"]:
            with self.subTest(value=value):
                self.records[0]["cashAndCashEquivalents"] = value
                with self.assertRaises(ValueError):
                    fill_missing_balance_inputs(
                        {}, self.records, self.dates
                    )


if __name__ == "__main__":
    unittest.main()
import unittest

from src.concept_registry import get_concept_candidates
from src.sec_data import get_records_with_fallbacks


def record(date, value):
    return {
        "end": date,
        "val": value,
        "form": "10-K",
        "filed": "2026-02-20",
        "accn": "example-filing",
    }


def facts(primary, alternative):
    return {
        "facts": {
            "us-gaap": {
                "Primary": {"units": {"USD": primary}},
                "Alternative": {"units": {"USD": alternative}},
            }
        }
    }


class ConceptFallbackTests(unittest.TestCase):
    def test_reported_zero_is_not_replaced(self):
        selected = get_records_with_fallbacks(
            facts(
                [record("2025-01-31", 0)],
                [record("2025-01-31", 50)],
            ),
            ["Primary", "Alternative"],
            ["2025-01-31"],
        )

        self.assertEqual(selected["2025-01-31"]["val"], 0)
        self.assertEqual(
            selected["2025-01-31"]["selected_concept"], "Primary"
        )

    def test_fallback_fills_only_missing_periods(self):
        selected = get_records_with_fallbacks(
            facts(
                [record("2025-01-31", 100)],
                [
                    record("2025-01-31", 999),
                    record("2026-01-31", 120),
                ],
            ),
            ["Primary", "Alternative"],
            ["2025-01-31", "2026-01-31"],
        )

        self.assertEqual(selected["2025-01-31"]["val"], 100)
        self.assertEqual(selected["2026-01-31"]["val"], 120)
        self.assertEqual(
            selected["2026-01-31"]["selected_concept"], "Alternative"
        )

    def test_missing_candidates_remain_missing(self):
        selected = get_records_with_fallbacks(
            facts([], []),
            ["Primary", "Alternative"],
            ["2025-01-31"],
        )

        self.assertIsNone(selected["2025-01-31"])

    def test_broader_asset_spending_is_not_a_capex_alias(self):
        candidates = get_concept_candidates(
            "capex",
            "PaymentsToAcquirePropertyPlantAndEquipment",
            is_flow=True,
        )

        self.assertNotIn("PaymentsToAcquireProductiveAssets", candidates)

    def test_original_records_are_not_modified(self):
        original = record("2025-01-31", 100)

        get_records_with_fallbacks(
            facts([original], []),
            ["Primary", "Alternative"],
            ["2025-01-31"],
        )

        self.assertNotIn("selected_concept", original)


if __name__ == "__main__":
    unittest.main()
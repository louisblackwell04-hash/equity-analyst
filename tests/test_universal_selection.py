import unittest

from src.universal_selection import get_standard_records


class UniversalSelectionTests(unittest.TestCase):
    def setUp(self):
        self.date = "2025-12-31"
        self.facts = {
            "cik": 123,
            "facts": {"us-gaap": {}},
        }

    def add_fact(self, concept, value, flow=False):
        record = {
            "end": self.date,
            "val": value,
            "form": "10-K",
            "filed": "2026-03-01",
            "accn": "synthetic-filing",
        }
        if flow:
            record["start"] = "2025-01-01"

        self.facts["facts"]["us-gaap"][concept] = {
            "units": {"USD": [record]},
        }

    def select(self):
        return get_standard_records(self.facts, [self.date])

    def test_reported_revenue_has_priority_over_contract_revenue(self):
        self.add_fact("Revenues", 100, flow=True)
        self.add_fact(
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            90, flow=True,
        )
        selected = self.select()
        self.assertEqual(selected["revenue"][self.date]["val"], 100)
        self.assertEqual(
            selected["contract_revenue"][self.date]["val"], 90
        )

    def test_reported_zero_is_not_replaced_by_alternative(self):
        self.add_fact("Revenues", 0, flow=True)
        self.add_fact(
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            90, flow=True,
        )
        self.assertEqual(
            self.select()["revenue"][self.date]["val"], 0
        )

    def test_fallback_retains_actual_source_concept(self):
        concept = "RevenueFromContractWithCustomerExcludingAssessedTax"
        self.add_fact(concept, 90, flow=True)
        record = self.select()["revenue"][self.date]
        self.assertEqual(record["selected_concept"], concept)
        self.assertEqual(record["source"], "SEC company facts")

    def test_broader_receivables_are_not_customer_receivables(self):
        self.add_fact("ReceivablesNetCurrent", 30)
        selected = self.select()
        self.assertIsNone(selected["receivables"][self.date])
        self.assertEqual(
            selected["broader_current_receivables"][self.date]["val"],
            30,
        )

    def test_lease_inclusive_debt_is_not_lease_exclusive_debt(self):
        self.add_fact("LongTermDebtAndCapitalLeaseObligations", 100)
        selected = self.select()
        self.assertIsNone(selected["long_term_debt"][self.date])
        self.assertEqual(
            selected["noncurrent_debt_including_finance_leases"]
            [self.date]["val"],
            100,
        )

    def test_commercial_paper_and_borrowings_remain_separate(self):
        self.add_fact("ShortTermBorrowings", 30)
        self.add_fact("CommercialPaper", 10)
        selected = self.select()
        self.assertEqual(
            selected["short_term_debt"][self.date]["val"], 30
        )
        self.assertEqual(
            selected["commercial_paper"][self.date]["val"], 10
        )


if __name__ == "__main__":
    unittest.main()
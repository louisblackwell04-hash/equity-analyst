import json
import tempfile
import unittest
from pathlib import Path

from src.reviewed_inputs import fill_reviewed_inputs


class ReviewedInputTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "reviewed_inputs.json"

        # Synthetic fixture: not an actual financial disclosure.
        self.record = {
            "ticker": "TEST",
            "cik": "0000000123",
            "period_end": "2026-12-31",
            "metric": "commercial_paper",
            "value": 0,
            "currency": "USD",
            "unit": "dollars",
            "source": "Reviewed SEC filing",
            "accession": "0000000123-26-000001",
            "source_url": (
                "https://www.sec.gov/Archives/edgar/data/"
                "123/000000012326000001/test.htm"
            ),
            "location": "Synthetic debt note",
            "evidence": "Synthetic zero-balance test fixture.",
        }

    def apply(self, series, records=None, ticker="TEST",
              cik="0000000123", dates=None):
        self.path.write_text(json.dumps(
            [self.record] if records is None else records
        ))
        return fill_reviewed_inputs(
            series,
            self.path,
            ticker,
            cik,
            ["2026-12-31"] if dates is None else dates,
        )

    def test_missing_value_receives_documented_zero(self):
        original = {"commercial_paper": {2026: None}}
        updated, sources = self.apply(original)

        self.assertEqual(updated["commercial_paper"][2026], 0)
        self.assertEqual(original["commercial_paper"][2026], None)
        self.assertEqual(
            sources["2026"]["commercial_paper"]["accession"],
            self.record["accession"],
        )

    def test_existing_values_including_zero_are_preserved(self):
        for value in (0, 123):
            with self.subTest(value=value):
                original = {"commercial_paper": {2026: value}}
                updated, sources = self.apply(original)
                self.assertEqual(updated, original)
                self.assertEqual(sources, {})

    def test_other_company_does_not_receive_entry(self):
        updated, sources = self.apply(
            {}, ticker="OTHER", cik="0000000456"
        )
        self.assertEqual(updated, {})
        self.assertEqual(sources, {})

    def test_wrong_company_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.apply({}, cik="0000000456")

    def test_other_period_does_not_receive_entry(self):
        updated, sources = self.apply(
            {}, dates=["2025-12-31"]
        )
        self.assertEqual(updated, {})
        self.assertEqual(sources, {})

    def test_duplicate_entries_are_rejected(self):
        with self.assertRaises(ValueError):
            self.apply({}, records=[self.record, dict(self.record)])

    def test_missing_evidence_is_rejected(self):
        self.record["evidence"] = ""
        with self.assertRaises(ValueError):
            self.apply({})


if __name__ == "__main__":
    unittest.main()